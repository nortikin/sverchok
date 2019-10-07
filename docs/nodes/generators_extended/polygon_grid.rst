Polygonal Grid
=========

Functionality
-------------

The Polygonal Grid node creates a polygon array assambled to fill the plane. It can work with triangles, squares and hexagons 

The generated lattice points and tiles are confined to one of the selected layouts: rectangle, triangle, diamond and hexagon.

Inputs
------

All inputs are vectorized and they will accept single or multiple values.

- **Size**
- **Scale**
- **Angle**
- **NumX**   [1]
- **NumY**   [1]
- **Level**  [2]

Notes:
[1] : NumX, NumY are available for the **rectangular** layout type
[2] : Level input is available for the **triangle**, **diamond** and **hexagon** layout types

Parameters
----------

The **Type** parameter allows to select the type of polygon: TRIANGLE, RECTANGLE and HEXAGON 

The **Layout** parameter allows to select one of the layout types: RECTANGLE, TRIANGLE, DIAMOND and HEXAGON. The lattice points and the hexagonal tiles will be generated to fit within one of these layouts.

The **Center** parameter allows to center the grid around the origin.

The **Size Mode** parameter allows to determine how to define polygons size

The **Separate** parameter allows for the individual tiles (vertices, edges & polygons) to be separated into individual lists in the corresponding outputs.

All parameters except **Layout**, **Size Mode**, **Separate** and **Center** can be given by the node or an external input.

Most inputs are "sanitized" to restrict their values:
- Radius is a float with value >= 0.0
- Scale is a float with value >= 0.0
- Level, NumX and NumY are integer with values >= 1

+-------------+--------+---------+------------------------------------------------+
| Param       | Type   | Default | Description                                    |
+=============+========+=========+================================================+
| **Radius**  | Float  | 1.0     | Radius of the grid tile                        |
+-------------+--------+---------+------------------------------------------------+
| **Scale**   | Float  | 1.0     | Scale of each tile around its center           |
+-------------+--------+---------+------------------------------------------------+
| **Angle**   | Float  | 0.0     | Rotate the grid around origin by this amount   |
+-------------+--------+---------+------------------------------------------------+
| **NumX**    | Int    | 7       | Number of points along X [1]                   |
+-------------+--------+---------+------------------------------------------------+
| **NumY**    | Int    | 6       | Number of points along Y [1]                   |
+-------------+--------+---------+------------------------------------------------+
| **Level**   | Int    | 3       | Number of levels around the center point [2]   |
+-------------+--------+---------+------------------------------------------------+

Notes:
[1] : NumX/NumY inputs are available for the RECTANGULAR layout type.
[2] : Level input is available for the TRIANGLE, DIAMOND AND HEXAGON layout type.

Outputs
-------
Outputs will be generated when connected.

**Centers**
These are the the centers of the tiles.

**Vertices**, **Edges**, **Polygons**
These are the vertices, edges and polygons of the hexagonal tiles centered on the lattice points of the selected layout.

Notes:
- When the **Separate** is ON the output is a single list (joined mesh) of all the tile vertices/edges/polygons in the grid. When **Separate** is OFF the output is a list of grouped (list) tile vertices/edges/polygons (separate meshes).
- If **Separate** is OFF (joined tiles) at **scale** = 1, when the tiles are tightly packed, the overlaping vertices will be merged.

Example of usage
----------------

.. image:: https://user-images.githubusercontent.com/10011941/42779991-581204a4-8942-11e8-8339-19ef08408246.png

.. image:: https://user-images.githubusercontent.com/10011941/42779982-508f8026-8942-11e8-837e-a909fb784127.png

