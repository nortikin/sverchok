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
[![Telegram chat](https://img.shields.io/badge/Telegram-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)](https://t.me/sverchok_3d)
[![VK](https://img.shields.io/badge/вконтакте-%232E87FB.svg?&style=for-the-badge&logo=vk&logoColor=white)](https://vk.com/sverchok_b3d)

[comment]: <> (To get more labels or edit current go to https://shields.io/, type Github in project URL field and you will get available labels which can be customized)

## English

[RU](https://github.com/nortikin/sverchok/blob/master/README_RU.md)  
**Addon for**: [Blender](http://blender.org) version *2.93* and above (currently tested with 5.1). For *2.79*, see [special installation instructions](https://github.com/nortikin/sverchok/wiki/Sverchok-for-Blender-2.79-installation).  
**License**: [GPL3](http://www.gnu.org/licenses/quick-guide-gplv3.html)  
**Prerequisites**: Some optional nodes require additional libraries. See this [wiki page](https://github.com/nortikin/sverchok/wiki/Dependencies) for a list of dependencies and installation instructions.  
[**Documentation**](http://nortikin.github.io/sverchok/docs/main.html): If anything is unclear or missing in this document, please ask on the [Issue Tracker](https://github.com/nortikin/sverchok/issues). We want to improve these resources and your feedback helps!  
**Community**: [Discord](https://discord.gg/pjHHhjJz8Z)

### Description
Sverchok is a powerful parametric tool for architects and designers, enabling visual programming of geometry through nodes. Mesh and geometry programming involves combining basic elements such as:

- Lists of indexed vectors representing coordinates (Sverchok uses zero-based indexing)
- Lists of grouped indices representing edges and polygons
- Matrices (user-friendly rotation-scale-location transformations)
- Curves
- Surfaces
- Scalar and vector fields
- Solids
- Insolation and solar heating calculations

### Features
With over 600 nodes for creating and manipulating geometry, combining these nodes enables you to:

- Create parametric constructions
- Easily adjust parameters using sliders and formulas
- Utilize powerful nodes including: Profile parametric, UVconnect, Generative art, Mesh expression, Proportion edit, Wafel, Adaptive Polygons (tissue vectorized), Adaptive edges, ExecNodeMod, Vector Interpolation series, List manipulators, CSG Boolean, Bmesh operations, Bmesh properties, and more
- Perform cross-sections, extrusions, and other modifications with flexible, parameterized, and vectorized node tools
- Calculate areas, volumes, and perform other geometric analysis
- Create or import CSV tables and custom formats
- Work with vector/scalar fields—create them and visualize data
- Perform solid modeling
- Code custom nodes in Python using the Scripted node
- Create custom 'addons' based on node layouts and integrate them into your workflow via Sverchok's 3D View panel
- Access Blender's Python API (bpy) with specialized *Set* and *Get* nodes
- Update Sverchok with a single click
- Incorporate genetic algorithms into your workflow
- Perform insolation/radiation calculations
- Export SVG/DXF drawings directly from node trees
- Exchange BREP/NURBS/IFC data
- And much more!

### Installation
Install Sverchok like any other Blender addon.

- **Installation from Preferences**  
  Download the Sverchok [archive (zip) from GitHub](https://github.com/nortikin/sverchok/archive/refs/heads/master.zip)
  - Do not unpack the archive after downloading — Blender will handle this
    - Mac OS users may need to [recompress the folder](https://support.apple.com/guide/mac-help/zip-and-unzip-files-and-folders-on-mac-mchlp2528/mac) if Safari automatically extracted and deleted the `.zip`
  - Go to Edit > Preferences > Add-ons
  - Click the `Install...` button
  - Browse to the zip file location, select it, and click "Install Add-on"
  - Blender will unpack the addon and present an option to enable it
  - Enable it by checking the box next to `Node: Sverchok`
  - Allow Blender a few seconds to complete the installation
  - When complete, Blender will display:
    - [x] Node: Sverchok

  By default, Blender (version 2.80 and above) will remember enabled addons for future sessions.

- **Updating Sverchok**  
  Use the `Check for new version` button in Sverchok's panel in the Node Editor (press `N` to open the panel)  
  Click the `Update Sverchok` button  
  Press F8 to reload addons—the new version number will appear in the N-panel

- **Additional Dependencies**  
  Sverchok provides many features out-of-the-box, but additional nodes and scripts utilize third-party libraries including:
  - scipy
  - marching cubes
  - geomdl
  - SciKit-image
  - shapely
  - circlify
  - freecadpython3lib

  Installation instructions for these dependencies are available on this [wiki page](https://github.com/nortikin/sverchok/wiki/Dependencies)

### Troubleshooting Installation Errors

If installing from a release zip containing a folder named `sverchok-master.x.y.z`, rename it to `sverchok-master` since folder names with dots are invalid Python package names.

If using releases from [here](https://github.com/nortikin/sverchok/releases), note that these versioned zips are intended for testing older Sverchok versions with legacy .blend files and Blender versions, not for initial installations.

##### Errors during installation or enabling

If you encounter errors like:

> `NameError: name 'nodes' is not defined`

Exit and restart Blender, then enable Sverchok again. The addon may take up to 10 seconds to initialize depending on your system performance.

##### Other installation issues

If Sverchok still fails to install, we've compiled troubleshooting solutions [here](http://nortikin.github.io/sverchok/docs/installation.html). Please report any new issues you encounter.

Updating via the in-panel button may fail if you've renamed the installation folder. Follow [this guide](https://github.com/nortikin/sverchok/issues/669) for a bootstrap script solution.

### Contact and Credits
**Homepage**: [nortikin.github.io/sverchok/](http://nortikin.github.io/sverchok/)  
**Authors**:
- Alexander Nedovizin
- Nikita Gorodetskiy
- Linus Yng
- Agustin Gimenez
- Dealga McArdle
- Konstantin Vorobiew
- Ilya Portnov
- Eleanor Howick
- Walter Perdan
- Marius Giurgi
- Sergey Soluyanov
- Ivan Prytov
- Victor Doval
- Dion Moult
- Alessandro Zomparelli
- Alex (aka Satabol)
- @kevinsmia1939

**Email**: sverchok-b3d@yandex.ru
