Area
=====

Functionality
-------------

Area node is one of the analyzer type. It is used to get the area of any polygon, no matter the number of its vertices or its world position.

Inputs
------

**Vertices** and **Polygons** are needed. 
Both inputs need to be of the kind Vertices and Strings, respectively

Parameters
----------

All parameters need to proceed from an external node.


+------------------+---------------+-------------+-----------------------------------------------+
| Param            | Type          | Default     | Description                                   |  
+==================+===============+=============+===============================================+
| **Vertices**     | Vertices      | None        | vertices of the polygons                      | 
+------------------+---------------+-------------+-----------------------------------------------+
| **Polygons**     | Strings       | None        | polygons referenced to vertices               |
+------------------+---------------+-------------+-----------------------------------------------+
| **Count Faces**  | Boolean       | True        | output individual faces or the sum of all     |
+------------------+---------------+-------------+-----------------------------------------------+

Outputs
-------

**Area** will be calculated only if both **Vertices** and **Polygons** inputs are linked.


Example of usage
----------------

.. image:: https://cloud.githubusercontent.com/assets/5990821/4187932/3208d26c-376e-11e4-92ba-76e86c589e91.png

In the example we have the inputs from a plane with 24 faces. We can use **Area** node to get the sum of all of them or all of them individually.