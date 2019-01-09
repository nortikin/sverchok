Length
=====

Functionality
-------------

Length node is one of the analyzer type. It is used to get the length of any path, no matter the number of its vertices or its world position.


Inputs / Parameters
-------------------


+------------------+---------------+-------------+--------------------------------------------------+
| Param            | Type          | Default     | Description                                      |  
+==================+===============+=============+==================================================+
| **Vertices**     | Vertices      | None        | Vertices of the edges / path                     | 
+------------------+---------------+-------------+--------------------------------------------------+
| **Edges**        | Strings       | None        | Edges referenced to vertices                     |
+------------------+---------------+-------------+--------------------------------------------------+
| **by Edges**     | Boolean       | True        | output individual edges length or the sum of all |
+------------------+---------------+-------------+--------------------------------------------------+

In the N-Panel you can use the toggle **Output NumPy** to get NumPy arrays in stead of regular lists (makes the node faster). 

Outputs
-------

**Length**: it will be calculated if **Vertices** inputs is linked. If no **Edges** are supplied the node will use the sequence order to calculate de distances.


Example of usage
----------------

.. image:: https://user-images.githubusercontent.com/10011941/50869102-f52d3d80-13b2-11e9-8316-01106c61e8d7.png
  :alt: LengthDemo1.PNG

Measuring a Bender curve with the default vertices, with a higher interpolation and by edges

.. image:: https://user-images.githubusercontent.com/10011941/50869357-f317ae80-13b3-11e9-88a0-05888e9bc2c6.png
  :alt: LengthDemo2.PNG

Using the length node to know the linear distance needed to build a 3 meter radius geodesic dome