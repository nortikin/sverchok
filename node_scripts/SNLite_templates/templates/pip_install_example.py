"""
in package s
"""

#
#
# this example should not be run as a script inside script node, it exists only to give users
# quick access to a scripted version of pip-install :
#
# you can pass it a package name, or a list of package names
# you can pass it a local whl location
#
# below are examples of lines that you can execute using these two functions, they will call subprocess
# and install the packages into the current bpython executable's site-packages directory.

from sverchok.utils.pip_utils import install_package, install_whl
    
#if __name__ == '__main__':
# install_package(['--upgrade', 'pip']) # <-- may not be needed
# install_package('pandas')
# install_package('gdal') # <-- may fail
# install_package('fiona') # <-- may fail.
# install_whl(r"C:\Users\zeffi\Downloads\GDAL-3.4.2-cp310-cp310-win_amd64.whl")
# install_whl(r"C:\Users\zeffi\Downloads\Fiona-1.8.21-cp310-cp310-win_amd64.whl")
# install_package('geopandas')
# install_package('pygeos')
# install_package('shapely')

