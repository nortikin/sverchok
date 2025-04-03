==========================
Sverchok API Documentation
==========================

Nowadays Sverchok has a large set of modules, classes and functions, allowing to
manipulate data structures, meshes, basic geometry objects, curves and surfaces
(including NURBS), fields and solids (with help of FreeCAD library). These
methods are used by Sverchok nodes internally. But also this API can be used by
developers of scripted nodes and addons which extend Sverchok functionality.

**Disclaimer**: although this API is more or less documented, we do not provide any
guarantees of it's stability. Please be warned that there may be changes in API
during Sverchok development. The API documentation is generated automatically,
so it will be always up to date. If you want to see what is changed in API
since some time, for now the best way is to look into git history.

At the moment, documentation strings are rare and in many cases not detailed
enough. But even so, we gather even the list of modules, classes and methods
can be useful for developers.

There is documentation for the following modules:

* `sverchok.data_structure <../../apidocs/sverchok/data_structure.html>`_ - basic data structures (lists and tuples) manipulation
* `sverchok.node_tree <../../apidocs/sverchok/node_tree.html>`_ - basic node and node tree classes and tools
* `sverchok.dependencies <../../apidocs/sverchok/dependencies.html>`_ - tools for handling external dependencies
* `sverchok.core <../../apidocs/sverchok/core/index.html>`_ - Sverchok core
* `sverchok.utils <../../apidocs/sverchok/utils/index.html>`_ - meshes, geometry manipulation tools and other utilities

