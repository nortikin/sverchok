<p align="center">
<a href="http://nikitron.cc.ua/sverchok_en.html">
<img src="ui/logo/png/sverchock_icon_t.png" width="150" title="hover text">
</a>
</p>
<h1 align="center">Sverchok</h1>

[![Build Status](https://travis-ci.org/nortikin/sverchok.svg?branch=master)](https://travis-ci.org/nortikin/sverchok)

## English

[RU](https://github.com/nortikin/sverchok/blob/master/README_RU.md)  
**addon for**: [Blender](http://blender.org) version *2.80* and above. For *2.79* see [special installation instruction](https://github.com/nortikin/sverchok/wiki/Sverchok-for-Blender-2.79-installation).  
**current sverchok version**: Find version in addon settings or in the node Sverchok panel   
**License**: [GPL3](http://www.gnu.org/licenses/quick-guide-gplv3.html)   
**prerequisites**: Python 3.6, and `numpy`, both included in recent versions of Blender (precompiled binaries are convenient for this). Sverchok can also optionally use several additional libraries; if you have them, a number of additional nodes will be available. Please refer to [wiki page](https://github.com/nortikin/sverchok/wiki/Dependencies) for list of such dependencies and instructions for their installation.

**manual**: [In English](http://nikitron.cc.ua/sverch/html/main.html) - This is an introduction to Sverchok and contains 3 lessons, and documentation on almost all nodes. If anything isn't clear (or missing) in this document please ask about it on the [Issue Tracker](https://github.com/nortikin/sverchok/issues), we want to get these lessons right and you can help us! 

  
### Description
Sverchok is a powerful parametric tool for architects, allowing geometry to be programmed visually with nodes. 
Mesh and geometry programming consists of combining basic elements such as:  

  - lists of indexed Vectors representing coordinates (Sverchok vectors are zero based)
  - lists of grouped indices to represent edges and polygons.
  - matrices (user-friendly rotation-scale-location transformations)  
  - curves  
  - surfaces  
  - scalar and vector fields  
  - solids  

### Possibilities
Comes with more than 500 nodes to help create and manipulate geometry. Combining these nodes will allow you to:

  - do parametric constructions  
  - easily change parameters with sliders and formulas    
  - power nodes such as: Profile parametric, UVconnect, Generative art, Mesh expression, Proportion edit, Wafel, Adaptive Poligons (tissue vectorized), Adaptive edges, ExecNodeMod, Vector Interpolation series of nodes, List manipulators, CSG Boolean, Bmesh ops, Bmesh props, etc.  
  - do cross sections, extrusions, other modifications with hight level flexible parametrised and vectorised node tools  
  - calculate areas, volume, and perform other geometric analysis  
  - make or import CSV tables or custom formats  
  - use Vector fields, create them, visualize data  
  - even code your own custom nodes in python with Scripted node  
  - make your own 'addons' on node layouts and utilise them with Sverchok 3dview panel in your everyday pipeline  
  - access to Blender Python API (bpy) with special _Set_ and _Get_ nodes  
  - upgrade Sverchok with pressing one button  
  - using genetic algorythm in your workflow  
  - and much, much more!  

### Installation
Install Sverchok as you would any blender addon.  
  
-  _Installation from Preferences_  
   Download Sverchok [archive (zip) from github](https://github.com/nortikin/sverchok/archive/master.zip)   
   User Preferences > Addons > install from file >  choose zip-archive > activate flag beside Sverchok  
   Enable permanently in the startup.blend using `Ctrl + U` and `Save User Settings` from the Addons menu.  

-  _Upgrade Sverchok on fly_   
   Use button `Check for new version` in sverchok panel in node editor (press `N` for panel).    
   Press `Update Sverchok` button.   
   At the end press F8 to reload add-ons. In NodeView the new version number will appear in the N-panel.   

-  _Additionally_  
   It is recommended to have such python libreries as scipy, marching cubes, shapely. They are used in some scripted nodes.  

### Troubleshooting Installation Errors

If you are installing from a release zip, please be aware that if it contains a folder named `sverchok-master.x.y.z`, you will need to rename that folder to `sverchok-master` because folder names with dots are not valid python package names. But it's best to just name it `sverchok`.  

If you are installing from a release found [here](https://github.com/nortikin/sverchok/releases), these files contain folders that have the dots mentioned in the previous point. These versioned release zips are not meant for installing from, but rather can be used to try older versions of Sverchok when you are using older .blend files and older Blender versions. Don't use these release zips if you are installing sverchok for the first time.

##### Errors during "install" or "enable" in preferences

if an error is raised like:

> `NameError: name 'nodes' is not defined`

then exit Blender and restart Blender. This time also activate Sverchok by checking the tickbox, but give it as long as it needs to initialize the add-on. It's a complicated Add-on and might take up to 10 seconds to enable (depends on how fast your machine is and how much ram you have).

##### Other reasons for failing:

In case Sverchok still fails to install, we've compiled a list of reasons and known resolutions [here](http://nikitron.cc.ua/sverch/html/installation.html). Please let us know if you encounter other installation issues.   

If you update with update button in sverchok panel it can raise an error if you renamed a folder, so follow [this](https://github.com/nortikin/sverchok/issues/669) (a bootstrap script you can run from TextEditor)  

### Contact and Credit
Homepage: [Home](http://nikitron.cc.ua/sverchok_en.html)  
Authors: 
-  Alexander Nedovizin,  
-  Nikita Gorodetskiy,  
-  Linus Yng,  
-  Agustin Gimenez, 
-  Dealga McArdle,  
-  Konstantin Vorobiew, 
-  Ilya Protnov,  
-  Eleanor Howick,    
-  Walter Perdan,    
-  Marius Giurgi,      
-  Durman,     
-  Ivan Prytov,
-  Victor Doval

Email: sverchok-b3d@yandex.ru  

[![Please donate](https://www.paypalobjects.com/en_US/GB/i/btn/btn_donateCC_LG.gif)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=JZESR6GN9AKNS)
