Distance Line Line
==================

Functionality
-------------

The node is designed to get the distance between two endless lines (defined by a segment) in space, also provides the point in each line that is closest to the other line and if they intersect.


Inputs / Parameters
-------------------


+------------------+-------------+----------------------------------------------------------------------+
| Param            | Type        | Description                                                          |  
+==================+=============+======================================================================+
| **Verts_Line A** | Vertices    |  It will get the first and last vertices's to define the line segment| 
+------------------+-------------+----------------------------------------------------------------------+
| **Verts_Line B** | Vertices    | It will get the first and last vertices's to define the line segment |
+------------------+-------------+----------------------------------------------------------------------+

Advanced Parameters
-------------------

In the N-Panel you can use the toggle:
 
**Tolerance**: Minimal distance to accept is intersecting.

**Match List**: Define how list with different lengths should be matched. 

Outputs
-------

**Distance**: Distance between the lines.

**Intersect**: Returns true if the lines intersect. (Distance < Tolerance)

**Closest Point A**: Returns the closest point to the line B in the line A

**Closest Point B**: Returns the closest point to the line A in the line B

**A in segment**: Returns true if the closest point A is in the provided segment

**B in segment**: Returns true if the closest point B is in the provided segment


Example of usage
----------------

.. image:: https://github.com/vicdoval/sverchok/raw/docs_images/images_for_docs/analyzer/distance_line_line/blender_sverchok_distance_line_line.png
  :alt: Distance_line_line_procedural.PNG

To trim lines to its intersection point:

.. image:: https://github.com/vicdoval/sverchok/raw/docs_images/images_for_docs/analyzer/distance_line_line/blender_sverchok_parametric_distance_line_line.png
  :alt: Sverchok_Distance_line_line.PNG

