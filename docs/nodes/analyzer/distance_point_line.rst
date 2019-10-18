Distance Point Line
===================

Functionality
-------------

The node is designed to get the distance between a point and one endless straight line.

The line is defined by a segment of two vectors.

As an extra results you can get:

- If the point is in the line

- If the point is in the segment

- Which is the closest point in the line

- If the closest point is in the segment


Inputs / Parameters
-------------------


+---------------------+-------------+----------------------------------------------------------------------+
| Param               | Type        | Description                                                          |  
+=====================+=============+======================================================================+
| **Vertices**        | Vertices    | Points to calculate                                                  | 
+---------------------+-------------+----------------------------------------------------------------------+
| **Line Vertices**   | Vertices    | It will get the first and last vertices's to define the line segment |
+---------------------+-------------+----------------------------------------------------------------------+
| **Tolerance**       | Float       | Minimal distance to accept one point is intersecting.                |
+---------------------+-------------+----------------------------------------------------------------------+

Advanced Parameters
-------------------

In the N-Panel (and on the right-click menu) you can find:

**Implementation**: Choose between MathUtils and NumPy (Usually faster)

**Output NumPy**: to get NumPy arrays in stead of regular lists (makes the node faster). Only in the NumPy implementation.

**Match List Global**: Define how list with different lengths should be matched. Refers to the matching of groups (one line per group)

**Match List Local**: Define how list with different lengths should be matched. Refers to the matching of tolerances and vertices


Outputs
-------

**Distance**: Distance to the line.

**In Segment**: Returns True if point distance is less than tolerance and the point is between the input vertices.

**In Line**: Returns True if point distance is less than tolerance with input vertices.

**Closest Point**: Returns the closest point in the line.

**Closest in Segment**: Returns True if the closest point is between the input vertices.


Example of usage
----------------

.. image:: https://github.com/vicdoval/sverchok/raw/docs_images/images_for_docs/analyzer/distance_point_line/distance_point_line_sverchok_blender.png
  :alt: Distance_point_line_procedural.PNG

It can be used to create perpendicular lines from input points

.. image:: https://github.com/vicdoval/sverchok/raw/docs_images/images_for_docs/analyzer/distance_point_line/distance_point_line_sverchok_blender_perpendicular_to_line.png
  :alt: Sverchok_Distance_point_line.PNG

In this example the node is used to separate the points which are at less than two units from the line.

.. image:: https://github.com/vicdoval/sverchok/raw/docs_images/images_for_docs/analyzer/distance_point_line/distance_point_line_sverchok_blender_procedural.png
  :alt: Blender_distance_point_line.PNG

In this example the Inset Polygon node gets the inset and distance inputs from the distance of the polygon to the line.

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/analyzer/distance_point_line/distance_point_line_sverchok_blender_from_polygon.png 
  :alt: Sverchok_Distance_polygon_line.PNG
  
This example uses the node to scale geometry along a custom axis.

.. image:: https://github.com/vicdoval/sverchok/raw/docs_images/images_for_docs/analyzer/distance_point_line/distance_point_line_sverchok_blender_scale_custom_axis.png
  :alt: Sverchok_scale_along_custom_axis.PNG