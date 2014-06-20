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

In case Sverchok fails to install, we've compiled a list of reasons and known resolutions [here](/docs/Installation_troubleshooting.md). Please let us know if you encounter other installation issues.

###Contact and Credit
Homepage: http://nikitron.cc.ua/sverchok.html  
Authors: 
-  Alexander Nedovizin,  
-  Nikita Gorodetskiy,  
-  Linus Yng,  
-  Agustin Gimenez, 
-  Dealga McArdle  

Email: sverchok-b3d@yandex.ru  
