"""
in package t
"""

import sys
import os
import subprocess

def install_package(package):
    if not isinstance(package, list):
        package = [package]
    subprocess.call([os.path.join(sys.prefix, 'bin', 'python.exe'), "-m", "pip", "install", *package])

def install_whl(package_path):
    subprocess.call([os.path.join(sys.prefix, 'bin', 'python.exe'), "-m", "pip", "install", f"{package_path}"])
    

if __name__ == '__main__':
    ## install_package(['--upgrade', 'pip'])  <-- may not be needed
    # install_package('pandas')
    ## install_package('gdal')  <-- may fail
    ## install_package('fiona')  <-- may fail.
    # install_whl(r"C:\Users\zeffi\Downloads\GDAL-3.4.2-cp310-cp310-win_amd64.whl")
    # install_whl(r"C:\Users\zeffi\Downloads\Fiona-1.8.21-cp310-cp310-win_amd64.whl")
    # install_package('geopandas')
    # install_package('pygeos')   <-- optional
    # install_package('shapely')  <-- optional