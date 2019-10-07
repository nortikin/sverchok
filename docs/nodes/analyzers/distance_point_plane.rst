Distance Point Plane
====================

.. image:: https://github.com/vicdoval/sverchok/raw/docs_images/images_for_docs/analyzer/distance_point_plane/distance_point_plane_sverchok_blender_nodes.png
  :alt: Distance_point_plane_procedural.PNG

Functionality
-------------

The node is designed to find the distance between a point and one plane.

The plane is defined by three points.

As extra results you can get from the node:

- If the point is in the triangle.

- If point is in the plane. 

- Closest point in the plane. 

- If the closest point is inside the triangle.

 


Inputs / Parameters
-------------------


+---------------------+-------------+---------------------------------------------------------------------------------------------+
| Param               | Type        | Description                                                                                 |  
+=====================+=============+=============================================================================================+
| **Vertices**        | Vertices    | Points to calculate                                                                         | 
+---------------------+-------------+---------------------------------------------------------------------------------------------+
| **Verts Plane**     | Vertices    | It will get the first three vertices of the input list to define the triangle and the plane |
+---------------------+-------------+---------------------------------------------------------------------------------------------+
| **Tolerance**       | Float       | Minimal distance to accept one point is intersecting.                                       |
+---------------------+-------------+---------------------------------------------------------------------------------------------+

Advanced Parameters
-------------------

In the N-Panel (and on the right-click menu) you can find:

**Implementation**: Choose between MathUtils and NumPy (Usually faster)

**Output NumPy**: Get NumPy arrays in stead of regular lists (makes the node faster). Only in the NumPy implementation.

**Match List Global**: Define how list with different lengths should be matched. Refers to the matching of groups (one plane per group)

**Match List Local**: Define how list with different lengths should be matched. Refers to the matching of tolerances and vertices

Outputs
-------

**Distance**: Distance to the line.

**In Triangle**: Returns True if the point  coplanar and inside the triangle formed by the input vertices

**In Plane**: Returns True if point is in the same plane as with input vertices.

**Closest Point**: Returns the closest point in the plane

**Closest in Triangle**": Returns true if the closest point is is in the same plane as with input vertices.


Example of usage
----------------

In this example the node is used to split the points depending of the side of the plane. Also the ones that are near to the plane (under intersection tolerance).

.. image:: https://github.com/vicdoval/sverchok/raw/docs_images/images_for_docs/analyzer/distance_point_plane/distance_point_plane_sverchok_blender_parametric_plane_split.png
  :alt: distance_point_plane_sverchok_blender_parametric_plane_split.png

It can be used to project the geometry over a plane.

.. image:: https://github.com/vicdoval/sverchok/raw/docs_images/images_for_docs/analyzer/distance_point_plane/distance_point_plane_sverchok_blender_project_on_plane.png
  :alt: distance_point_plane_sverchok_blender_project_on_plane.png

