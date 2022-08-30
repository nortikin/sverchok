#pip_utils.py

# you can pass it a package name, or a list of package commands
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

usage = r"""\

from sverchok.utils.pip_utils import install_package, install_whl

install_package(['--upgrade', 'pip']) # <-- may not be needed
install_package('pandas')
install_package('gdal') # <-- may fail
install_package('fiona') # <-- may fail.
install_whl(r"your_path\GDAL-3.4.2-cp310-cp310-win_amd64.whl")
install_whl(r"your_path\Fiona-1.8.21-cp310-cp310-win_amd64.whl")
install_package('geopandas')
install_package('pygeos')
install_package('shapely')

"""
