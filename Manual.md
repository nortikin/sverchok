## Documentation

## User Manual

The user manual is an essential reference for new and existing users. Each node has at least one page dedicated to explaining what it does, what inputs to use and what kind of output to expect. We are humans and do make mistakes, if you find any node references missing, incomplete, or factually inaccurate please make a [new issue on the issue tracker](https://github.com/nortikin/sverchok/issues). We will act on this information at our earliest convenience.

**[Read User Documentation Online](docs/main.html)**

## Developer API Documentation

Nowadays Sverchok has a large set of modules, classes and funtions, allowing to manipulate data structures, meshes, basic geometry objects, curves and surfaces (including NURBS), fields and solids (with help of FreeCAD library). These methods are used by Sverchok nodes internally. But also this API can be used by developers of scripted nodes and addons which extend Sverchok functionality.

Disclaimer: although this API is more or less documented, we do not provide any guarantees of it's stability. Please be warned that there may be changes in API during Sverchok development. The API documentation is generated automatically, so it will be always up to date. If you want to see what is changed in API since some time, for now the best way is to look into git history.

At the moment, documentation strings are rare and in many cases not detailed enough. But even so, we gather even the list of modules, classes and methods can be useful for developers.

There is documentation for the following modules:

* [sverchok.data_structure - basic data structures (lists and tuples) manipulation](apidocs/sverchok/data_structure.html)
* [sverchok.node_tree - basic node and node tree classes and tools](apidocs/sverchok/node_tree.html)
* [sverchok.core - Sverchok core](apidocs/sverchok/core/index.html)
* [sverchok.utils - meshes, geometry manipulation tools and other utilities](apidocs/sverchok/utils/index.html)

