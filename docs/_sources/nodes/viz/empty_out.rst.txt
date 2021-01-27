Empty out
==============

Functionality
-------------

Making an Empty in scene from matrix in sverchok

Inputs
------

The most versatile input is Matrix (scale, rotation and location information), 
but the node accepts vectors as input too, vectors will only pass location information.

Parameters
----------

+-------------+-----------------------------------------------------------------------------------+
| Feature     | info                                                                              |
+=============+===================================================================================+
| Base name   | Name for new Empty objects                                                        |
+-------------+-----------------------------------------------------------------------------------+

Limitations
-----------

The node will read the first matrix or vector from the input stream, and use that to transform
or place the empty.

There is no mode to output multiple matrices if the input contains more than one.


Outputs
-------

Object - Emptys
