Polygon Sort
============

Functionality
-------------

Polygon Sort node sorts the input polygons by various criteria: distance, area and normal angle.

Inputs
------

All parameters except **Mode** and **Descending** are vectorized and can take single of multiple input values.

Parameters
----------

All parameters except **Mode** and **Descending** can be given by the node or an external input.

+----------------+-----------+-----------+--------------------------------------------------------+
| Param          | Type      | Default   | Description                                            |
+================+===========+===========+========================================================+
| **Mode**       | Enum      | "D"       | The sorting direction mode:                            |
|                |           |           |  P  : Sort by the the distance to a point P            |
|                |           |           |  D  : Sort by the projection along a direction D       |
|                |           |           |  A  : Sort by the area of the polygons                 |
|                |           |           |  NP : Sort by the normal angle relative to point P     |
|                |           |           |  ND : Sort by the normal angle relative to direction D |
+----------------+-----------+-----------+--------------------------------------------------------+
| **Descending** | Bool      | False     | Sort the polygons in the descending order.             |
+----------------+-----------+-----------+--------------------------------------------------------+
| **Verts**      | Vector    | none      | The vertices of the input mesh to be sorted.           |
+----------------+-----------+-----------+--------------------------------------------------------+
| **Polys**      | Polygon   | none      | The polygons of the input mesh to be sorted.           |
+----------------+-----------+-----------+--------------------------------------------------------+
| **Point P**    | Vector    | (1,0,0)   | The reference vector: Point P. [1]                     |
+----------------+-----------+-----------+--------------------------------------------------------+
| **Direction**  | Vector    | (1,0,0)   | The reference vector: Direction D. [1]                 |
+----------------+-----------+-----------+--------------------------------------------------------+

Notes:
[1] : "Point P" is shown in P and NP mode and "Direction" is shown in D and ND mode. These are used for distance and normal angle calculation. The area mode (A) does not use the input sorting vector.

Outputs
-------

**Indices**
The indices of the sorted polygons.

**Vertices**
The input vertices.

**Polygons**
The sorted polygons.

**Quantities**
The quantity by which the polygons are sorted. Depending on the selected mode the output quantities are either Distances, Projections, Angles or Areas.

Note: The output will be generated when the output sockets are connected.

Modes
-----
The modes corespond to different sorting criteria and each one has a quanitity by which the polygons are sorted.
* P : In this mode the polygons are sorted by the distance from the center of each polygon to the given point P.
* D : In this mode the polygons are sorted by the projection component of polygon center vector along the given direction D.
* A : In this mode the polygons are sorted by the area of the polygons.
* ND : In this mode the polygons are sorted by the angle between the polygon normal and the given direction vector D.
* NP : In this mode the polygons are sorted by the angle between the polygon normal and the vector pointing form the center of the polygon to the given point P.

Presets
-------
The node provides a set of predefined sort directions: along X, Y and Z. These buttons will set the mode to "D" and the sorting vector (Direction) to one of the X, Y or Z directions: (1,0,0), (0,1,0) and (0,0,1) respectively. The preset buttons are only visible as long as the sorting vector socket is not connected.

References:
The algorythm to compute the area is based on descriptions found at this address: http://geomalgorithms.com/a01-_area.html#3D%20Polygons


