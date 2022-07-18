#pip_utils.py

# you can pass it a package name, or a list of package names
# you can pass it a local whl location
#
# below are examples of lines that you can execute using these two functions, they will call subprocess
# and install the packages into the current bpython executable's site-packages directory.

import sys
import os
import subprocess

def install_package(package):
    if not isinstance(package, list):
        package = [package]
    subprocess.call([os.path.join(sys.prefix, 'bin', 'python.exe'), "-m", "pip", "install", *package])

def install_whl(package_path):
    subprocess.call([os.path.join(sys.prefix, 'bin', 'python.exe'), "-m", "pip", "install", f"{package_path}"])
