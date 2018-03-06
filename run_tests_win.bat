:: usage
:: PS C:\Users\you\Desktop\GITHUB\sverchok> .\run_tests_win.bat C:\fullpathto\b279\blender.exe

echo off

:: blender executable path
set arg1=%1 

shift
%arg1% -b --addons sverchok --python utils/testing.py --python-exit-code 1
