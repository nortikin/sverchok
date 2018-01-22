echo off

:: blender executable path
set arg1=%1 

shift
%arg1% -b --addons sverchok --python utils/testing.py --python-exit-code 1 