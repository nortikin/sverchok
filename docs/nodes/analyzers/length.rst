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

**Length** will be calculated if **Vertices** inputs are linked, if no **Edges** are supplied the node will use the sequence order to calculate de distances.


Example of usage
----------------

.. image:: https://cloud.githubusercontent.com/assets/5990821/4188452/8f9cbf66-3772-11e4-8735-34462b7da54b.png
  :alt: LengthDemo1.PNG

Measuring a Bender curve with the default vertices, with a higher interpolation and by edges