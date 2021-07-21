***********************
Installing dependencies
***********************

Sverchok can use several external libraries, that provide some mathematical or other functions. 
We call such libraries "Dependencies". When these libraries are available, you will be able to 
use much more nodes in Sverchok. If you do not need all these features, you can skip installation 
of dependencies, or install only some of them.

Some of dependencies can be installed easily, by just running `pip`. For such
dependencies, Sverchok supports easy-to-use installation user interface.
To use it, navigate to ``Edit => Preferences``, then locate Sverchok
preferences under Addons section; then navigate to the "Extra Nodes" tab:

.. image:: https://user-images.githubusercontent.com/284644/92996779-93c65600-f527-11ea-8b88-1ea3b2bc4559.png

The dialog shows current status of all dependencies. For dependencies that can
be installed by `pip`, but are not yet installed, this dialog will show an
"Install" button. You'll have just to press the button and wait for when
Blender will say that the library is installed. If there will be any errors
during installation, Blender will report it and print details into console
output.

For dependencies that can not be installed that easily, the dialog contains a
button which opens the browser on an official web site of corresponding
library, so you can find installation instructions.


Install pip
===========

In some cases, it may appear that Blender's python already knows about your
system's installation of python (python is usually installed by default on most
Linux distros). In such cases, you may use just `pip install something` to
install libraries.

There are two known ways to install `pip` into Blender.

* Option 1

This I tested on latest Blender 2.81 builds. The similar instructions should
work for other Blender 2.8x versions::

    $ /path/to/blender/2.xx/python/bin/python3 -m ensurepip
    $ /path/to/blender/2.xx/python/bin/python3 -m pip install --upgrade pip setuptools wheel

(exact name of `python` executable depends on specific blender build).

* Option 2

If, for some reason, Option 1 does not work for you (on some system Python says
`no module named ensurepip`), then you have to do the following:

1. Download `get-pip.py <https://bootstrap.pypa.io/get-pip.py>`_ script
2. Run it with Blender's python::

    $ /path/to/blender/2.xx/python/bin/python3.7m /path/to/get-pip.py

Please refer to `official pip site <https://pip.pypa.io/en/stable/installing/>`_ for official installation instructions.


Troubleshooting
===============

I can't install dependencies on Windows
---------------------------------------

It can appear that the problem is in filesystem permissions. Try running Blender from an administrator
account and install dependencies in this mode.

Another possibility is to use a prepared archive with Python libraries, for Blender 2.91 
https://disk.yandex.ru/d/ZX4_jPGMRUvP7Q or for Blender 2.92 https://disk.yandex.ru/d/CRUxCC4RshA3qg.
just unzip the archive in C:\Program Files\Blender Foundation\Blender 2.91\2.91 (or *\2.92) These 
archives also include libraries for Sverchok-extra and Sverchok-open3d in addition to Pygalmesh, you 
also need to install Visual C++ 14.0 To connect the FreeCAD libraries, specify 
\Blender 2.*\2.*\python\lib\site-packages\conda-0.18.3\bin in the Sverchok settings.

This archive was tested to be working with Blender versions since 2.90 to 2.93. For 2.90, 
use the 2.91 archive, and for 2.93, use the 2.92 archive.

If you experience some problems with use of this Zip archive, please report them in a github issue.


I can't install dependencies on Linux, while using Blender installed from Snap
------------------------------------------------------------------------------

Snap creates readonly file system, so you can't put dependencies into it. The only way known to work 
reliably is to not use Blender from Snap for Sverchok, if you want to use dependencies. 
The recommended way is to just download Blender's `tar.xz` from blender.org and unpack it.


Pip install says that the package is already installed, but Sverchok can't see it
---------------------------------------------------------------------------------

It can appear that you have the package installed into your system-wide or user-wide 
Python installation, for example into ``~/.local/lib/python/...``. In this case Pip will 
see that the package is installed, but Sverchok will not be able to access it. Try to run::

    $ python3.7 -m pip uninstall $PACKAGENAME

(using your system's python, not blender's one), and then install the package again with Blender's python::

    $ /path/to/blender/2.xx/python/bin/python3 -m pip install $PACKAGENAME

This time you should see that pip is actually installing package.


Other troubles with pip
-----------------------

If you admit some kind of errors with pip, you can try:      
Wipe all versions of pip from `2.90\python\lib\site-packages` and then
run `2.90\python\bin> ./python.exe -m ensurepip -U`    
