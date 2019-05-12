Distance Point Line
===================

Functionality
-------------

The node is designed to get the distance between a point and one line


Inputs / Parameters
-------------------


+------------------+-------------+----------------------------------------------------------------------+
| Param            | Type        | Description                                                          |  
+==================+=============+======================================================================+
| **Verts**        | Vertices    | Points to calculate                                                  | 
+------------------+-------------+----------------------------------------------------------------------+
| **Verts_Line**   | Vertices    | It will get the first and last vertices's to define the line segment |
+------------------+-------------+----------------------------------------------------------------------+

Advanced Parameters
-------------------

In the N-Panel you can use the toggle:
 
**Implementation**: Choose between MathUtils and NumPy (Usually faster)

**Output NumPy**: to get NumPy arrays in stead of regular lists (makes the node faster). Only in the NumPy implementation.

Outputs
-------

**Distance**: Distance to the line.

**In Segment**: Returns true if the point is between the input vertices

**In Line**: Returns true if point is aligned with input vertices.

**Closest Point**: Returns the closest point in the line

**Closest in Segment**": Returns true if the closest point is between the input vertices


Example of usage
----------------

.. image:: https://user-images.githubusercontent.com/10011941/57584308-0067b580-74da-11e9-966e-fe32cae35d29.png
  :alt: Distance_point_line_procedural.PNG

It can be used to create perpendicular lines from input points

.. image:: https://user-images.githubusercontent.com/10011941/57584321-3147ea80-74da-11e9-8da4-18fc028bcfdd.png
  :alt: Sverchok_Distance_point_line.PNG

Or to select the points in a distance range 

.. image:: https://user-images.githubusercontent.com/10011941/57584309-03fb3c80-74da-11e9-9f90-811731330189.png
  :alt: Blender_distance_point_line.PNG

