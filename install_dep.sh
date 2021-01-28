# blender configs
_blender_path=blender-2.93.0-ded9484925ed-linux64
_blender_version=2.93
# paths
_blender_python=./$_blender_path/$_blender_version/python/bin/python3.7m
_blender_python_libs=$_blender_path/$_blender_version/python/include/python3.7m
# download and install pip
wget -4 --unlink https://bootstrap.pypa.io/get-pip.py
$_blender_python ./get-pip.py
# use China Tsinghua mirror
# note that this mirror may not be available for other countries
$_blender_python -m pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
# install packages
$_blender_python -m pip install -U circlify
$_blender_python -m pip install Cython
rm $_blender_python_libs/../python3.7m_backup
mv $_blender_python_libs/ $_blender_python_libs/../python3.7m_backup
mkdir $_blender_python_libs
ln -s /usr/include/python3.7m/* $(pwd)/$_blender_python_libs/
$_blender_python -m pip install -U PyMCubes
# $_blender_python -m pip install -U geomdl
$_blender_python -m pip install geomdl --install-option="--use-cython"
echo "complete."
