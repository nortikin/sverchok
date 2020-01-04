Pentagon Tiler
==============

Functionality
-------------

The Pentagon Tiler node creates a pentagon array assembled to fill the plane. It can work with different types of pentagons

The generated lattice points and tiles are confined to one of the selected layouts: rectangle, triangle, diamond and hexagon.

Parameters
----------

The **Type** parameter allows to select the type of pentagon.

The **Rotation** parameter allows to select the base angle, aligned with X axis, Y axis or aligned with the pentagon tile

The **Center** parameter allows to center the grid around the origin.

The **Separate** parameter allows for the individual primitive tiles (vertices, edges & polygons) to be separated into individual lists in the corresponding outputs.

Inputs
------

All inputs are vectorized and they will accept single or multiple values.

- **Angle** : Rotate the grid around origin by this amount

- **NumX** : Number of points along X

- **NumY** : Number of points along Y

- **A** and **B**: Angles of the pentagon

- **a, b, c and d**: Length of sides

Advanced Parameters
-------------------

In the N-Panel (and on the right-click menu) you can find:

**Angle Units**: Choose if the input angles will be interpreted as Degrees or Radians

**Flat output**: Flatten output by list-joining level 1 and unwarping it (default set to True)

**Match List Global**: Define how list with different lengths should be matched. Refers to the matching of groups (level 1)

**Match List Local**: Define how list with different lengths should be matched. Refers to the matching inside groups (level 2)

Outputs
-------
Outputs will be generated when connected.

**Vertices**, **Edges**, **Polygons**
These are the vertices, edges and polygons of the pentagonal tiles centered on the lattice points of the selected layout.

Notes:
- When the **Separate** is ON the output is a single list (joined mesh) of all the tile vertices/edges/polygons in the grid. When **Separate** is OFF the output is a list of grouped (list) tile vertices/edges/polygons (separate meshes).
- If **Separate** is OFF (joined tiles),  the overlapping vertices will be merged.

Example of usage
----------------

.. image:: https://user-images.githubusercontent.com/10011941/71754304-df4b3f00-2e85-11ea-8feb-99e375ffca8d.png
.. image:: https://user-images.githubusercontent.com/10011941/71755025-15d68900-2e89-11ea-83e0-3328446fa47d.png
.. image:: https://user-images.githubusercontent.com/10011941/71755215-e1af9800-2e89-11ea-9ba9-d23de15b2dbb.png
.. image:: https://user-images.githubusercontent.com/10011941/71755942-7f589680-2e8d-11ea-86de-938d1090fb66.png
