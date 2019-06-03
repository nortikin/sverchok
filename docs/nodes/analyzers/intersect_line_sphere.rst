Compass 3D
==========

Functionality
-------------

The node is designed to get the intersection between a sphere and one endless straight line.

This problem has three possible solutions:

    No intersection: the distance of the center of the sphere to the line is bigger than its radius

    One intersection: the line is tangent to the sphere.

    Two intersections: the line passes through the sphere intersecting it surface in two points.

The line by two vector creating one segment.

Inputs / Parameters
-------------------

+---------------------+-------------+----------------------------------------------------------------------+
| Param               | Type        | Description                                                          |
+=====================+=============+======================================================================+
| **Vertices**        | Vector      | Points to calculate                                                  |
+---------------------+-------------+----------------------------------------------------------------------+
| **Edges**           | Int List    | Edges data to define the segments (to define the line)               |
+---------------------+-------------+----------------------------------------------------------------------+
| **Center**          | Vectors     | It will get the first and last vertices's to define the line segment |
+---------------------+-------------+----------------------------------------------------------------------+
| **Radius**          | Float       | Radius of the intersecting sphere                                    |
+---------------------+-------------+----------------------------------------------------------------------+

Advanced Parameters
-------------------

In the N-Panel (and on the right-click menu) you can find:

**Output NumPy**: to get NumPy arrays in stead of regular lists (makes the node faster). Only in the NumPy implementation.

**Match List Global**: Define how list with different lengths should be matched. Refers to the matching of groups (one line per group)

**Match List Local**: Define how list with different lengths should be matched. Refers to the matching of tolerances and vertices


Outputs
-------

**Intersect Line**: Returns True if the there is valid intersection.

**Intersection A**: Returns the intersection nearer to the end point of the segment. In case of no intersection returns the closest point on the line.

**Intersection B**: Returns the intersection nearer to the start point of the segment. In case of no intersection returns the closest point on the line.

**Int. A in segment**: Returns True if A intersection is over the segment.

**Int. B in segment**: Returns True if B intersection is over the segment.

**First in segment**: Returns the first valid value between Int. A, Int. B and Closest point.

**Int. with segment**: Returns True if the closest point is between the input vertices.

**All Segment int.**: Returns a flat list of all the intersections.


Example of usage
----------------

Basic explanation of Compass 3d intersections.

.. image:: https://github.com/vicdoval/sverchok/raw/docs_images/images_for_docs/analyzer/intersect_line_sphere/compass_3d_sverchok_blender_example.png
  :alt: compass_3d_sverchok_blender_example.png

In this example the node is used to join one arc with one line with segments of 6 units.

.. image:: https://github.com/vicdoval/sverchok/raw/docs_images/images_for_docs/analyzer/intersect_line_sphere/compass_3d_sverchok_blender_first_intersection_arc_line_constant_dist.png
  :alt: compass_3d_sverchok_blender_first_intersection_arc_line_constant_dist.png

In this example the node is used find all intersections of one sphere over the edges of a cylinder.

.. image:: https://github.com/vicdoval/sverchok/raw/docs_images/images_for_docs/analyzer/intersect_line_sphere/compass_3d_sverchok_blender_all_intersections_sphere_cylinder.png
  :alt: all_intersections_sphere_cylinder.png

In this example the node is used to simulate a mechanism. The yellow line keeps constant length while connects a moving point with a horizontal rail

.. image:: https://github.com/vicdoval/sverchok/raw/docs_images/images_for_docs/analyzer/intersect_line_sphere/compass_3d_sverchok_blender_mechanism.gif
  :alt: compass_3d_sverchok_blender_mechanism.gif
