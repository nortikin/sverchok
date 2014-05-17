##Sverchok parametric tools
version 0.2.8  
addon for: blender.org  
License: GPL3  
  
###Description
Sverchok is a powerful parametric tool for architects, allowing geometry to be programmed visually with nodes. 
Mesh and geometry programming consists of combining basic elements such as:  

  - lists of indexed Vectors representing coordinates (Sverchok vectors are zero based)
  - lists of grouped indices to represent edges and polygons.
  - rotation angles 
  - matrices (user-friendly rotation-scale-location transformations)

Version 0.2.8 comes with more than 50 nodes to help create and manipulate geometry. Combining these nodes will allow you to:

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
   User Preferences > Addons > install from file > 
   choose zip-archive > activate flag beside Sverchok
   If appears error - close and run blender again.
  
-  _Manual installation_  
   Drop the `sverchok-master` folder into `/scripts/addons`.  
   User Preferences > Addons > Community > (search Sverchok) > activate flag beside Sverchok  

-  _Linux manual installation_ 
   For current blender version 2.7.0.

   Open terminal and run there one line:

     `cd ~/.config/blender/2.70/scripts/addons/ && wget https://github.com/nortikin/sverchok/archive/master.zip && unzip master.zip`
   
   Done!

Enable permanently in the startup.blend using `Ctrl + U` and `Save User Settings` from the Addons menu.
  
###Contact and Credit
Homepage http://nikitron.cc.ua/sverchok.html  
Authors: Alexander Nedovizin, Nikita Gorodetskiy, Linus Yng, Agustin Gimenez, Dealga McArdle
