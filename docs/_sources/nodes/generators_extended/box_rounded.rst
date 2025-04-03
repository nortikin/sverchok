Rounded box
===========

.. image:: https://user-images.githubusercontent.com/14288520/190874840-96e656e5-765a-4d7a-83fc-2654a728bca6.png
  :target: https://user-images.githubusercontent.com/14288520/190874840-96e656e5-765a-4d7a-83fc-2654a728bca6.png

.. image:: https://user-images.githubusercontent.com/14288520/190875021-db05b31b-e960-442f-83d9-bb9b8eba8ef7.png
  :target: https://user-images.githubusercontent.com/14288520/190875021-db05b31b-e960-442f-83d9-bb9b8eba8ef7.png

Functionality
-------------
See the BlenderArtists thread by original author Phymec. This node merely encapsulates 
the code into a form that works for Sverchok. Internally the main driver is the amount of 
input vectors, each vector represents the x y z dimensions of a box. Each box can have
unique settings. If fewer parameters are provided than sizes, then a default or the last
parameter is repeated.

Inputs & Parameters
-------------------

+----------------+-----------------------+----------------------------------------------------------------------------+
| name           | type                  | info                                                                       |
+================+=======================+============================================================================+
| radius         | single value or list  | radius of corner fillets                                                   |
+----------------+-----------------------+----------------------------------------------------------------------------+
| arc div        | single value or list  | number of divisions in the fillet                                          |
+----------------+-----------------------+----------------------------------------------------------------------------+
| lin div        | single value or list  | number of internal divisions on straight parts (``[0..1]`` or ``[1..20]``) |
+----------------+-----------------------+----------------------------------------------------------------------------+
| Vector Size    | single vector or list | x y z dimensions for each box                                              |
+----------------+-----------------------+----------------------------------------------------------------------------+
| div type       | 3way switch, integers | just corners, corners and edges, all                                       |
+----------------+-----------------------+----------------------------------------------------------------------------+
| odd axis align | 0..1 on or off        | internal rejiggery, not sure.                                              |
+----------------+-----------------------+----------------------------------------------------------------------------+

Outputs
-------

Depending on how many objects the input asks for, you get a Verts and Polygons list of rounded box representations.


Examples
--------

.. image:: https://cloud.githubusercontent.com/assets/619340/4471754/4987c79a-493e-11e4-89fe-bb9210af45c9.png
    :target: https://cloud.githubusercontent.com/assets/619340/4471754/4987c79a-493e-11e4-89fe-bb9210af45c9.png

* Number-> :doc:`A Number </nodes/number/numbers>`
* Number-> :doc:`Random Num Gen </nodes/number/random_num_gen>`
* MUL X, ADD X, /2: Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Vector-> :doc:`Vector Out </nodes/vector/vector_out>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://cloud.githubusercontent.com/assets/619340/4470969/f7dca97c-4930-11e4-9cae-63f8b17826be.png
    :target: https://cloud.githubusercontent.com/assets/619340/4470969/f7dca97c-4930-11e4-9cae-63f8b17826be.png

---------

.. image:: https://user-images.githubusercontent.com/14288520/190872241-80590f4b-0468-4648-ac84-592472317a5a.png
  :target: https://user-images.githubusercontent.com/14288520/190872241-80590f4b-0468-4648-ac84-592472317a5a.png

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Number-> :doc:`Float to Integer </nodes/number/float_to_int>`
* MUL X: Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* Number-> :doc:`Random Num Gen </nodes/number/random_num_gen>`
* List->List Struct-> :doc:`List Split </nodes/list_struct/split>`
* List->List Struct-> :doc:`List Slice </nodes/list_struct/slice>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

Notes
-----

see: 

**Round Cube, real Quadsphere, Capsule (snipped thread title):**

`original thread <http://blenderartists.org/forum/showthread.php?348741-Round-Cube-real-Quadsphere-Capsule-Rounded-Cuboid-3D-Grid-Convex-Hull-Margin>`_