##Sverchok parametric tools
version - look version file here   
addon for: http://blender.org   
License: GPL3   
  
###Description
Sverchok is a powerful parametric tool for architects, allowing geometry to be programmed visually with nodes. 
Mesh and geometry programming consists of combining basic elements such as:  

  - lists of indexed Vectors representing coordinates (Sverchok vectors are zero based)
  - lists of grouped indices to represent edges and polygons.
  - rotation angles 
  - matrices (user-friendly rotation-scale-location transformations)

Comes with more than 100 nodes to help create and manipulate geometry. Combining these nodes will allow you to:

  - do parametric constructions
  - easily change parameters with sliders and formulas
  - do cross sections
  - calculate areas
  - design material
  - use Vector fields
  - even code your own custom nodes
  - and more!

###Installation
Install Sverchok as you would any blender addon.  
  
-  _Installation from Preferences_  
   Download Sverchok from github  
   User Preferences > Addons > install from file >   
   choose zip-archive > activate flag beside Sverchok  
   If appears error - close and run blender again and activate again.  
   Enable permanently in the startup.blend using `Ctrl + U` and `Save User Settings` from the Addons menu.  
  
-  _Manual installation_  
   Download Sverchok from github  
   Drop the `sverchok-master` folder into `/scripts/addons`.  
   User Preferences > Addons > Community > (search Sverchok) > activate flag beside Sverchok  
   Enable permanently in the startup.blend using `Ctrl + U` and `Save User Settings` from the Addons menu.   

-  _Upgrade Sverchok on fly_   
   Use button 'Upgrade Sverchok addon' in sverchok panel in node editor (press `N` for panel)  
   And at the end press `F8` button to reload addons. In next blender run in panel will appear new version number  

###Troubleshooting Installation Errors
We now include NumPy code in Sverchok nodes, this means that you should have an up-to-date version of NumPy on your machine. Normally if you get your Blender precompiled NumPy will be included with Python, however this isn't always the case. If you get an error when enabling Sverchok the last lines of the error are important: 

If it mentions   

-  ImportError: No module named 'numpy'
-  multiarray
-  DLL failure
-  Module use of python33.dll conflicts with this version of Python

then here are steps to fix that.  

- download and install Python 3.4.(1) for your os
- download and install numpy 1.8 (for python 3.4) for your os.
- in the Blender directory rename the `python` folder to `_python` so Blender uses your local Python 3.4 install.
  
  
binaries  
python: https://www.python.org/downloads/release/python-341/  
numpy: http://sourceforge.net/projects/numpy/files/NumPy/  

  
An alternative is to send a polite email to whoever builds the binary of Blender which you currently use, and inform them that their NumPy inclusion should be double-checked.


###Contact and Credit
Homepage: http://nikitron.cc.ua/sverchok.html  
Authors: 
-  Alexander Nedovizin,  
-  Nikita Gorodetskiy,  
-  Linus Yng,  
-  Agustin Gimenez, 
-  Dealga McArdle  

Email: sverchok-b3d@yandex.ru  
