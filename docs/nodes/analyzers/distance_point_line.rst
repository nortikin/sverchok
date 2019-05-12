Distance Point LIne
===========

Functionality
-------------

The node is designed to get the distance between a point and one line


Inputs / Parameters
-------------------


+------------------+-------------+----------------------------------------------------------------------+
| Param            | Type        | Description                                                          |  
+==================+=============+======================================================================+
| **Verts**        | Vertices    | Points to calculate                                                  | 
+------------------+---------------+-------------+------------------------------------------------------+
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

**Closest Point": Returns the closest point in the line

**Closest in Segment**": Returns true if the closest point is between the input vertices


Example of usage
----------------

.. image:: https://user-images.githubusercontent.com/10011941/51251936-c4449e00-199a-11e9-89a7-557cc7e93731.png
  :alt: PathLengthDemo1.PNG

Measuring a Bender curve with the default vertices, with a higher interpolation and by segments

.. image:: https://user-images.githubusercontent.com/10011941/51251933-c4449e00-199a-11e9-99b8-fa53c8586484.png
  :alt: PathLengthDemo2.PNG

Using the node to know the linear distance needed to build a 3 meter radius geodesic dome

.. image:: https://user-images.githubusercontent.com/10011941/51251931-c4449e00-199a-11e9-9e75-69ead34fad64.png
  :alt: PathLengthDemo2.PNG

Using the *Path Length* node to place circles of one meter of diameter along a given curve