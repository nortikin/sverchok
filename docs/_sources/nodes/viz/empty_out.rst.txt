Empty out
==============

.. image:: https://user-images.githubusercontent.com/14288520/190487281-8477d806-c5af-4a69-b7f3-f8998ab53f22.png
  :target: https://user-images.githubusercontent.com/14288520/190487281-8477d806-c5af-4a69-b7f3-f8998ab53f22.png

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

Examples
--------

.. image:: https://user-images.githubusercontent.com/14288520/190487670-608066e3-4fb0-4b19-a85e-c5c4aa6a5f08.png
  :target: https://user-images.githubusercontent.com/14288520/190487670-608066e3-4fb0-4b19-a85e-c5c4aa6a5f08.png

* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Transform-> :doc:`Randomize </nodes/transforms/randomize>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

See limitations.