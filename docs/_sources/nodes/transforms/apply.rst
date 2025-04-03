Matrix Apply (verts)
====================

.. image:: https://user-images.githubusercontent.com/14288520/191355240-fce681b0-6b16-42bd-977c-65a7b2c0403d.png
  :target: https://user-images.githubusercontent.com/14288520/191355240-fce681b0-6b16-42bd-977c-65a7b2c0403d.png

Functionality
-------------

Applies a Transform Matrix to a list or nested lists of vectors (and therefore vertices)


Inputs
------

+----------+-----------------------------------------------------------------------------+
| Inputs   | Description                                                                 |
+==========+=============================================================================+
| Vectors  | Represents vertices or intermediate vectors used for further vector math    |
+----------+-----------------------------------------------------------------------------+
| Matrices | One or more, never empty                                                    |
+----------+-----------------------------------------------------------------------------+

Advanced Parameters
-------------------

In the N-Panel (and on the right-click menu) you can find:

**Output NumPy**: Output NumPy arrays in stead of regular lists (makes the node faster)

Outputs
-------

Nested list of vectors / vertices, matching the number nested incoming *matrices*.


Examples
--------

.. image:: https://user-images.githubusercontent.com/14288520/191473968-81b859bb-707f-42b9-90d4-272dce5ddfab.png
  :target: https://user-images.githubusercontent.com/14288520/191473968-81b859bb-707f-42b9-90d4-272dce5ddfab.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* List->List Struct-> :doc:`List Repeater </nodes/list_struct/repeater>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

---------

.. image:: https://user-images.githubusercontent.com/14288520/191473995-62d2c0fc-8793-4a9a-8b2e-790cc2d261d8.png
  :target: https://user-images.githubusercontent.com/14288520/191473995-62d2c0fc-8793-4a9a-8b2e-790cc2d261d8.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Number-> :doc:`Random </nodes/number/random>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`
* List->List Struct-> :doc:`List Repeater </nodes/list_struct/repeater>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`