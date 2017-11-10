Vector P Field
==============

Functionality
-------------

Makes a 3d vector grid, with option to slightly randomize (with seed) each vertex, and apply a 'remove doubles' distance to the product.

Inputs
-------

**xdim__** - Number of rows in x-axis

**ydim__** - Number of rows in y-axis

**zdim__** - Number of rows in z-axis

**sizex__** - Distance between rows along x-axis

**sizey__** - Distance between rows along y-axis

**sizez__** - Distance between rows along z-axis

Parameters
----------

**randomize** - Amount of position randomization of each vertex

**rm distance** - If distance between vertices is less than this value, those vertices will be removed

**seed** - Position randomization seed

Outputs
-------

**verts** - list of vertices

Examples
--------
