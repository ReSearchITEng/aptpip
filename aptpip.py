import argparse
import csv
import json
import requests
import sys
import logging
import subprocess
import time
import os

def setup_logging(debug_mode):
    """Sets up logging based on debug mode."""
    log_level = logging.DEBUG if debug_mode else logging.INFO
    if os.path.exists('dependency_check.log'):
        os.remove('dependency_check.log')
    logging.basicConfig(filename='dependency_check.log', level=log_level,
                        format='%(asctime)s - %(levelname)s - %(message)s')
    return log_level

def run_command(command, log_message, check_error=True):
    """Runs a command and logs the output, optionally checking for errors."""
    logging.debug(log_message)
    if args.debug:
        print(log_message)
        print(f"Executing: {' '.join(command)}")
    try:
        result = subprocess.run(command, check=check_error, capture_output=True, text=True)
        logging.debug(f"Command output:\n{result.stdout}\n{result.stderr}")
        return result
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed: {' '.join(command)}\n{e.stderr}")
        print(f"Error: {' '.join(command)} failed.\n{e.stderr}", file=sys.stderr)
        return None
    except FileNotFoundError:
        logging.error(f"Command not found: {' '.join(command)}")
        print(f"Error: Command not found: {' '.join(command)}", file=sys.stderr)
        return None

def get_dependencies(package_name):
    """Retrieves dependencies for a given package from PyPI."""
    try:
        pypi_url = f'https://pypi.python.org/pypi/{package_name}/json'
        log_message = f"Fetching data from PyPI: {pypi_url}"
        logging.debug(log_message)
        if args.debug:
            print(log_message)
        data = requests.get(pypi_url).json()
        if not data:
            logging.warning(f"No data received from PyPI for {package_name}. Assuming no dependencies or invalid package.")
            return None
        deps = data.get('info', {}).get('requires_dist', [])
        logging.debug(f"Dependencies from PyPI for {package_name}: {deps}")
        return deps
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching data from PyPI for {package_name}: {e}")
        return None
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON for {package_name}: {e}")
        return None

def is_dev_dependency(dependency_string):
    """Checks if a dependency string suggests it's a dev dependency."""
    dev_terms = ["test", "dev", "devel", "docs"]
    is_dev = any(term in dependency_string.lower() for term in dev_terms)
    logging.debug(f"Is '{dependency_string}' a dev dependency? {is_dev}")
    return is_dev

def apt_package_exists(package_name):
    """Checks if an apt package exists using apt-cache show."""
    log_message = f"Checking if apt package python3-{package_name} exists..."
    command = ["apt-cache", "show", f"python3-{package_name}"]
    result = run_command(command, log_message, check_error=False)
    exists = result is not None and result.stdout.strip() != "" # Check if stdout is not empty
    logging.debug(f"apt_package_exists({package_name}) returned: {exists}")
    return exists

def install_dependencies_recursive(package_name, processed=None, apt_packages=None, pip_packages=None, path=None):
    """Recursively installs dependencies, prioritizing apt."""
    if processed is None:
        processed = set()
    if apt_packages is None:
        apt_packages = set()
    if pip_packages is None:
        pip_packages = set()
    if path is None:
        path = [package_name]

    if package_name in processed:
        return

    processed.add(package_name)

    path_str = " -> ".join(path)
    print(f"Checking {package_name} ({path_str})")
    logging.info(f"Checking {package_name} ({path_str})")

    if apt_package_exists(package_name):
        apt_packages.add(f"python3-{package_name}")
        return

    dependencies = get_dependencies(package_name)

    if dependencies is None:
        pip_packages.add(package_name)
        return

    non_dev_dependencies = [dep for dep in dependencies if not is_dev_dependency(dep)]

    for dependency in non_dev_dependencies:
        dep_name = dependency.split(';')[0].split('<')[0].split('>')[0].split('=')[0].strip()
        install_dependencies_recursive(dep_name, processed, apt_packages, pip_packages, path + [dep_name])

    if package_name not in apt_packages:
        pip_packages.add(package_name)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Installs dependencies for a package.")
    parser.add_argument("package_name", help="The package to install dependencies for.")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging.")

    args = parser.parse_args()

    log_level = setup_logging(args.debug)

    package_name = args.package_name

    logging.info(f"Starting installation process for {package_name}")
    print(f"Starting installation process for {package_name}")

    start_time = time.time()

    apt_packages_to_install = set()
    pip_packages_to_install = set()
    processed_packages = set()

    install_dependencies_recursive(package_name, processed=processed_packages, apt_packages=apt_packages_to_install, pip_packages=pip_packages_to_install)

    print("")

    if apt_packages_to_install:
        apt_install_command = ["sudo", "apt", "install", "-y"] + list(apt_packages_to_install)
        if not run_command(apt_install_command, f"Running apt command: {' '.join(apt_install_command)}"):
            print("Apt packages installation failed.", file=sys.stderr)
            sys.exit(1)

    # ***The final crucial fix: Install the main package with pip if it's not in apt***
    if not apt_package_exists(package_name): #check if the main package was installed using apt
        pip_install_command = ["sudo", "pip3", "install", "--break-system-packages", package_name] + list(pip_packages_to_install) #install the main package first
        if not run_command(pip_install_command, f"Running pip command: {' '.join(pip_install_command)}"):
            print("Pip packages installation failed.", file=sys.stderr)
            sys.exit(1)
    elif pip_packages_to_install: #if it was installed with apt
        pip_install_command = ["sudo", "pip3", "install", "--break-system-packages"] + list(pip_packages_to_install)
        if not run_command(pip_install_command, f"Running pip command: {' '.join(pip_install_command)}"):
            print("Pip packages installation failed.", file=sys.stderr)
            sys.exit(1)

    end_time = time.time()
    elapsed_time = end_time - start_time

    logging.info(f"Installation process completed in {elapsed_time:.2f} seconds.")
    print(f"Installation process completed in {elapsed_time:.2f} seconds.")
