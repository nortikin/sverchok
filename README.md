<p align="center">
<a href="http://nortikin.github.io/sverchok/">
<img src="ui/logo/png/sverchock_icon_t.png" width="150" title="hover text">
</a>
</p>
<h1 align="center">Sverchok</h1>

[![Sverchok CI](https://github.com/nortikin/sverchok/actions/workflows/test-sverchok.yml/badge.svg?event=push)](https://github.com/nortikin/sverchok/actions/workflows/test-sverchok.yml)
<a href="https://discord.gg/pjHHhjJz8Z"><img alt="Discord" src="https://img.shields.io/discord/745273148018262158"></a>
[![Stack Exchange questions](https://img.shields.io/stackexchange/blender/t/sverchok?label=StackExchange)](https://blender.stackexchange.com/questions/tagged/sverchok)
![GitHub issues by-label](https://img.shields.io/github/issues/nortikin/sverchok/Proposal%20:bulb:?color=%237de57b&label=Proposal)
![GitHub issues by-label](https://img.shields.io/github/issues/nortikin/sverchok/bug%20:bug:?color=%23f4f277&label=Bug)

[comment]: <> (To get more labels or edit current go to https://shields.io/, type Github in project URL field and you will get available labels which can be customized)

## English

[RU](https://github.com/nortikin/sverchok/blob/master/README_RU.md)  
**Addon for**: [Blender](http://blender.org) version *2.93* and above. For *2.79* see [special installation instruction](https://github.com/nortikin/sverchok/wiki/Sverchok-for-Blender-2.79-installation).   
**License**: [GPL3](http://www.gnu.org/licenses/quick-guide-gplv3.html)   
**Prerequisites**: We added optional nodes that depend on additional libraries. This [wiki page](https://github.com/nortikin/sverchok/wiki/Dependencies) lists these dependencies and includes installation instructions.  
[**Documentation**:](http://nortikin.github.io/sverchok/docs/main.html) If anything isn't clear (or missing) in this document please
ask about it on the [Issue Tracker](https://github.com/nortikin/sverchok/issues), we want to get these lessons right
and you can help us!  
**Community**:  [Discord](https://discord.gg/pjHHhjJz8Z)
  
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
  - insolation/sun heating calculations   

### Possibilities
Comes with more than 600 nodes to help create and manipulate geometry. Combining these nodes will allow you to:

  - do parametric constructions  
  - easily change parameters with sliders and formulas    
  - power nodes such as: Profile parametric, UVconnect, Generative art, Mesh expression, Proportion edit, Wafel, Adaptive Polygons (tissue vectorized), Adaptive edges, ExecNodeMod, Vector Interpolation series of nodes, List manipulators, CSG Boolean, Bmesh ops, Bmesh props, etc.  
  - do cross sections, extrusions, other modifications with height level flexible parametrised and vectorised node tools  
  - calculate areas, volume, and perform other geometric analysis  
  - make or import CSV tables or custom formats  
  - use Vector/Scalar fields, create them, visualize data  
  - Solid modelling  
  - even code your own custom nodes in python with Scripted node  
  - make your own 'addons' on node layouts and utilise them with Sverchok 3dview panel in your everyday pipeline  
  - access to Blender Python API (bpy) with special _Set_ and _Get_ nodes  
  - upgrade Sverchok with pressing one button  
  - using genetic algorithm in your workflow  
  - insolation/radiation calculations  
  - SVG/DXF drawing export from node tree  
  - brep/NURBS/IFC exchange  
  - and much, much more!  

### Installation
Install Sverchok as you would any blender addon.  
  
-  _Installation from Preferences_  
   Download Sverchok [archive (zip) from github](https://github.com/nortikin/sverchok/archive/refs/heads/master.zip)
   -  Do not unpack it after downloading, Blender will take care of that later.
       - Mac OS users can [recompress the folder](https://support.apple.com/guide/mac-help/zip-and-unzip-files-and-folders-on-mac-mchlp2528/mac) if Safari has automatically extracted it and deleted the `.zip`  
   -  Edit > Preferences > Add-ons > 
   -  Press the `Install..` button 
   -  Browse to the location of the zip and select it, then press "Install Add-on"
   -  Blender unpacks the add-on, and when completed it will present the option to enable it.
   -  Enable it by clicking in the box beside `Node: Sverchok`:
   -  Let Blender complete the installation, most likely this will take a few seconds, be patient.
   -  When complete Blender will display:
       -  [x] Node: Sverchok
   
   
   By default Blender ( above 2.80) will store the fact that you enabled an add-on and it will be available next time you start Blender.
   

-  _Upgrade Sverchok on fly_   
   Use button `Check for new version` in sverchok panel in node editor (press `N` for panel).    
   Press `Update Sverchok` button.   
   At the end press F8 to reload add-ons. In NodeView the new version number will appear in the N-panel.   

-  _Additionally_  
   Sverchok provides a lot of useful features out-of-the-box that don't require you to install anything extra, but we
   do provide additional nodes and scripts that make use of so called "3rd party" libraries like: 
   - scipy
   - marching cubes 
   - geomdl   
   - SciKit-image   
   - shapely  
   - circlify  
   - freecadpython3lib   
   
   Instructions regarding their installation is found at this [wiki page](https://github.com/nortikin/sverchok/wiki/Dependencies)

### Troubleshooting Installation Errors

If you are installing from a release zip, please be aware that if it contains a folder named `sverchok-master.x.y.z`, you will need to rename that folder to `sverchok-master` because folder names with dots are not valid python package names.

If you are installing from a release found [here](https://github.com/nortikin/sverchok/releases), these files contain folders that have the dots mentioned in the previous point. These versioned release zips are not meant for installing from, but rather can be used to try older versions of Sverchok when you are using older .blend files and older Blender versions. Don't use these release zips if you are installing sverchok for the first time.

##### Errors during "install" or "enable" in preferences

if an error is raised like:

> `NameError: name 'nodes' is not defined`

then exit Blender and restart Blender. This time also activate Sverchok by checking the tickbox, but give it as long as it needs to initialize the add-on. It's a complicated Add-on and might take up to 10 seconds to enable (depends on how fast your machine is and how much ram you have).

##### Other reasons for failing:

In case Sverchok still fails to install, we've compiled a list of reasons and known resolutions [here](http://nortikin.github.io/sverchok/docs/installation.html). Please let us know if you encounter other installation issues.   

If you update with update button in sverchok panel it can raise an error if you renamed a folder, so follow [this](https://github.com/nortikin/sverchok/issues/669) (a bootstrap script you can run from TextEditor)  

### Contact and Credit
Homepage: [Home](http://nortikin.github.io/sverchok/)  
Authors: 
-  Alexander Nedovizin,  
-  Nikita Gorodetskiy,  
-  Linus Yng,  
-  Agustin Gimenez, 
-  Dealga McArdle,  
-  Konstantin Vorobiew, 
-  Ilya Portnov,  
-  Eleanor Howick,    
-  Walter Perdan,    
-  Marius Giurgi,      
-  Sergey Soluyanov,     
-  Ivan Prytov,   
-  Victor Doval,  
-  Dion Moult,  
-  Alessandro Zomparelli
-  Alex (aka Satabol)   

Email: sverchok-b3d@yandex.ru  

[![Please donate](https://www.paypalobjects.com/en_US/GB/i/btn/btn_donateCC_LG.gif)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=JZESR6GN9AKNS)
