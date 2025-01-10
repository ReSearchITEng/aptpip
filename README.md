# aptpip
When possible, apt install python3-package , and pip3 install only when not possible.   
It tries its best to find recursively what can be apt installed before doing any pip install.

# how to run
```python3 aptpip.py <desired_python_module> [--debug]```

./aptpip.py -h
usage: aptpip.py [-h] [-r REQUIREMENTS_FILE] [--debug] [--dev] [package_name]

Installs dependencies for a package or from a requirements file.

positional arguments:
  package_name          The package to install dependencies for.

options:
  -h, --help            show this help message and exit
  -r REQUIREMENTS_FILE, --requirements REQUIREMENTS_FILE
                        Path to a requirements.txt file.
  --debug               Enable debug logging.
  --dev                 Include development dependencies.

E.g.
```
./aptpip.py gphotos-sync --debug
Starting installation process for gphotos-sync
Checking gphotos-sync (gphotos-sync)
Checking if apt package python3-gphotos-sync exists...
Executing: apt-cache show python3-gphotos-sync
Fetching data from PyPI: https://pypi.python.org/pypi/gphotos-sync/json
Checking attrs (gphotos-sync -> attrs)
Checking if apt package python3-attrs exists...
Executing: apt-cache show python3-attrs
Fetching data from PyPI: https://pypi.python.org/pypi/attrs/json
Checking cloudpickle (gphotos-sync -> attrs -> cloudpickle)
Checking if apt package python3-cloudpickle exists...
Executing: apt-cache show python3-cloudpickle
Checking hypothesis (gphotos-sync -> attrs -> hypothesis)
Checking if apt package python3-hypothesis exists...
Executing: apt-cache show python3-hypothesis
Checking mypy (gphotos-sync -> attrs -> mypy)
Checking if apt package python3-mypy exists...
Executing: apt-cache show python3-mypy
Checking pympler (gphotos-sync -> attrs -> pympler)
Checking if apt package python3-pympler exists...
Executing: apt-cache show python3-pympler
Checking coverage[toml] (gphotos-sync -> attrs -> coverage[toml])
Checking if apt package python3-coverage[toml] exists...
Executing: apt-cache show python3-coverage[toml]
Fetching data from PyPI: https://pypi.python.org/pypi/coverage[toml]/json
Checking exif (gphotos-sync -> exif)
Checking if apt package python3-exif exists...
Executing: apt-cache show python3-exif
Checking appdirs (gphotos-sync -> appdirs)
Checking if apt package python3-appdirs exists...
Executing: apt-cache show python3-appdirs
Checking pyyaml (gphotos-sync -> pyyaml)
Checking if apt package python3-pyyaml exists...
Executing: apt-cache show python3-pyyaml
Fetching data from PyPI: https://pypi.python.org/pypi/pyyaml/json
Checking psutil (gphotos-sync -> psutil)
Checking if apt package python3-psutil exists...
Executing: apt-cache show python3-psutil
Checking google-auth-oauthlib (gphotos-sync -> google-auth-oauthlib)
Checking if apt package python3-google-auth-oauthlib exists...
Executing: apt-cache show python3-google-auth-oauthlib

Running apt command: sudo apt install -y python3-cloudpickle python3-exif python3-hypothesis python3-mypy python3-appdirs python3-pympler python3-google-auth-oauthlib python3-psutil
Executing: sudo apt install -y python3-cloudpickle python3-exif python3-hypothesis python3-mypy python3-appdirs python3-pympler python3-google-auth-oauthlib python3-psutil
Checking if apt package python3-gphotos-sync exists...
Executing: apt-cache show python3-gphotos-sync
Running pip command: sudo pip3 install --break-system-packages gphotos-sync coverage[toml] pyyaml attrs gphotos-sync
Executing: sudo pip3 install --break-system-packages gphotos-sync coverage[toml] pyyaml attrs gphotos-sync
Installation process completed in 13.37 seconds.

```

