:orphan:

Path Length
===========

Functionality
-------------

Path Length node is one of the analyzer type. It is used to get the length of any path, no matter the number of its vertices or its world position.


Inputs / Parameters
-------------------


+------------------+---------------+-------------+--------------------------------------------------+
| Param            | Type          | Default     | Description                                      |  
+==================+===============+=============+==================================================+
| **Vertices**     | Vertices      | None        | Vertices of the edges / path                     | 
+------------------+---------------+-------------+--------------------------------------------------+
| **Edges**        | Strings       | None        | Edges referenced to vertices                     |
+------------------+---------------+-------------+--------------------------------------------------+
| **Segment**      | Boolean       | True        | output the segments lengths or its sum           |
+------------------+---------------+-------------+--------------------------------------------------+

In the N-Panel you can use the toggle **Output NumPy** to get NumPy arrays in stead of regular lists (makes the node faster). 

Outputs
-------

**Length**: it will be calculated if **Vertices** input is linked. If no **Edges** are supplied the node will use the sequence order to calculate de length.


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