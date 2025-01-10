#!/usr/bin/env python3
import argparse
import logging
import os
import re
import requests
import subprocess
import sys
import time
import json

def setup_logging(debug_mode):
    """Sets up logging based on debug mode."""
    log_level = logging.DEBUG if debug_mode else logging.INFO
    if os.path.exists('dependency_check.log'):
        os.remove('dependency_check.log')
    logging.basicConfig(filename='dependency_check.log', level=log_level,
                        format='%(asctime)s - %(levelname)s - %(message)s')
    return log_level

def run_command(command, log_message, check_error=True, expected_return_code=0):
    """Runs a command and logs the output, optionally checking for errors."""
    logging.debug(log_message)
    if args.debug:
        print(log_message)
        print(f"Executing: {' '.join(command)}")
    try:
        result = subprocess.run(command, check=False, capture_output=True, text=True)
        logging.debug(f"Command output:\n{result.stdout}\n{result.stderr}")
        if check_error and result.returncode != expected_return_code:
            logging.error(f"Command failed: {' '.join(command)}\nReturn Code: {result.returncode}\n{result.stderr}")
            print(f"Error: {' '.join(command)} failed.\nReturn Code: {result.returncode}\n{result.stderr}", file=sys.stderr)
            return None
        return result
    except FileNotFoundError:
        logging.error(f"Command not found: {' '.join(command)}")
        print(f"Error: Command not found: {' '.join(command)}", file=sys.stderr)
        return None

def get_dependencies(package_name):
    """Retrieves dependencies for a given package from PyPI and handles extras."""
    try:
        pypi_url = f'https://pypi.python.org/pypi/{package_name}/json'
        log_message = f"Fetching data from PyPI: {pypi_url}"
        logging.debug(log_message)
        if args.debug:
            print(log_message)
        try:
            data = requests.get(pypi_url).json()
        except json.JSONDecodeError:
            logging.error(f"Error decoding JSON for {package_name}. Invalid JSON returned from PyPI.")
            return None
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching data from PyPI for {package_name}: {e}")
            return None

        if not data:
            logging.warning(f"No data received from PyPI for {package_name}. Assuming no dependencies or invalid package.")
            return None

        deps = data.get('info', {}).get('requires_dist')  # Get requires_dist

        if deps is None:  # Check if requires_dist is None
            logging.debug(f"No dependencies found for {package_name} in PyPI data.")
            return []  # Return an empty list if no dependencies

        cleaned_deps = []
        for dep in deps:
            match = re.match(r"([a-zA-Z0-9-_]+)(?:\[(.*?)\])?(?:;.*)?", dep)
            if match:
                package = match.group(1)
                extras = match.group(2)
                cleaned_deps.append((package, extras))
        logging.debug(f"Dependencies from PyPI for {package_name}: {cleaned_deps}")
        return cleaned_deps

    except Exception as e:
        logging.exception(f"An unexpected error occurred: {e}")
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

def apt_package_exists(package_name_with_extras):
    """Checks if an apt package exists using apt-cache show and extracts the real package name."""

    # Convert package name to lowercase
    package_name_lower = package_name_with_extras.lower()

    log_message = f"Checking if apt package python3-{package_name_lower} exists..."
    command = ["apt-cache", "show", f"python3-{package_name_lower}"]  # Use lowercase name
    result = run_command(command, log_message, check_error=False)
    if result and result.returncode == 0:
        output = result.stdout
        match = re.search(r"^Package: (\S+)$", output, re.MULTILINE)
        if match:
            real_package_name = match.group(1)
            logging.debug(f"Found apt package: {real_package_name}")
            return real_package_name
    return None

def install_dependencies_recursive(package_name, processed=None, apt_packages=None, pip_packages=None, path=None, include_dev=False):
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
        pip_packages.add((package_name, None))  # Add as tuple (package, None)
        return

    for dependency, extras in dependencies:
        if include_dev or not is_dev_dependency(dependency):
            install_dependencies_recursive(dependency, processed, apt_packages, pip_packages, path + [dependency], include_dev)

    if package_name not in apt_packages:
        pip_packages.add((package_name, None)) # Add as tuple (package, None)

def install_from_requirements(requirements_file, apt_packages, pip_packages, include_dev):
    """Installs dependencies from a requirements.txt file."""
    try:
        with open(requirements_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):  # Skip empty lines and comments
                    # Handle version specifiers (e.g., package==1.2.3, package>=1.0)
                    match = re.match(r"([a-zA-Z0-9-_]+)([=><]=)?(.*)", line)
                    if match:
                        package_name = match.group(1)
                        install_dependencies_recursive(package_name, processed_packages, apt_packages, pip_packages, include_dev=include_dev)
                    else:
                        logging.warning(f"Invalid line in requirements.txt: {line}")
    except FileNotFoundError:
        logging.error(f"Requirements file not found: {requirements_file}")
        print(f"Error: Requirements file not found: {requirements_file}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        logging.exception(f"An unexpected error occurred while processing requirements file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Installs dependencies for a package or from a requirements file.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("package_name", nargs="?", help="The package to install dependencies for.")
    group.add_argument("-r", "--requirements", dest="requirements_file", help="Path to a requirements.txt file.")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging.")
    parser.add_argument("--dev", action="store_true", help="Include development dependencies.")

    args = parser.parse_args()

    log_level = setup_logging(args.debug)

    package_name = args.package_name
    include_dev = args.dev

    logging.info(f"Starting installation process for {package_name}")
    print(f"Starting installation process for {package_name}")

    start_time = time.time()

    apt_packages_to_install = set()
    pip_packages_to_install = set()
    processed_packages = set()

    if args.requirements_file:
        install_from_requirements(args.requirements_file, apt_packages_to_install, pip_packages_to_install, include_dev)
    else:
        install_dependencies_recursive(package_name, processed=processed_packages, apt_packages=apt_packages_to_install, pip_packages=pip_packages_to_install, include_dev=include_dev)

    print("")

    if apt_packages_to_install:
        apt_install_packages = []
        for apt_package_with_extras in apt_packages_to_install:
            real_apt_package = apt_package_exists(apt_package_with_extras.replace("python3-",""))
            if real_apt_package:
                apt_install_packages.append(real_apt_package)
        if apt_install_packages:
            apt_install_command = ["sudo", "apt", "install", "-y"] + list(apt_install_packages)
            if not run_command(apt_install_command, f"Running apt command: {' '.join(apt_install_command)}"):
                print("Apt packages installation failed.", file=sys.stderr)
                sys.exit(1)

    if pip_packages_to_install:
        pip_install_packages = []
        for package, extras in pip_packages_to_install:
            install_string = package
            if extras:
                install_string += f"[{extras}]"
            pip_install_packages.append(install_string)
        pip_install_command = ["sudo", "pip3", "install", "--break-system-packages"] + pip_install_packages
        if not run_command(pip_install_command, f"Running pip command: {' '.join(pip_install_command)}"):
            print("Pip packages installation failed.", file=sys.stderr)
            sys.exit(1)

    end_time = time.time()
    elapsed_time = end_time - start_time

    logging.info(f"Installation process completed in {elapsed_time:.2f} seconds.")
    print(f"Installation process completed in {elapsed_time:.2f} seconds.")
