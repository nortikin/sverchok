Move
====

.. image:: https://user-images.githubusercontent.com/14288520/191294374-44c0cc8f-c01f-4c65-a7c4-28b9643ce6ad.png
  :target: https://user-images.githubusercontent.com/14288520/191294374-44c0cc8f-c01f-4c65-a7c4-28b9643ce6ad.png

Functionality
-------------

**equivalent to a Translate Transform**

Moves incoming sets of Vertex Lists by a *Vector*. The Vector is bound to a multiplier (Scalar) which amplifies all components of the Vector. The resulting Vector is added to the locations of the incoming Vertices.

Inputs & Parameters
-------------------

+------------+-------------------------------------------------------------------------------------+
|            | Description                                                                         |
+============+=====================================================================================+
| Vertices   | Vertex or Vertex Lists representing one or more objects                             |
+------------+-------------------------------------------------------------------------------------+
| Movement   | Vector to use for Translation, this is simple element wise addition to the Vector   |
|            |                                                                                     |
| Vectors    | of the incoming vertices.                                                           |
+------------+-------------------------------------------------------------------------------------+
| Strength   | Straightforward ``Vector * Scalar``, amplifies each movement vector                 |
+------------+-------------------------------------------------------------------------------------+

Advanced Parameters
-------------------

In the N-Panel (and on the right-click menu) you can find:

**Output NumPy**: Output NumPy arrays in stead of regular lists (makes the node faster)

**List Match**: Define how list with different lengths should be matched

Outputs
-------

A Vertex or nested Lists of Vertices


Examples
--------

Moving a circle:

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/move/move_vectors_blender_sverchok_example_1.png
   :target: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/move/move_vectors_blender_sverchok_example_1.png

* Generator-> :doc:`Circle </nodes/generator/circle>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Moving vertices along Y direction with a random multiplier

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/move/move_vectors_blender_sverchok_example_2.png
   :target: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/move/move_vectors_blender_sverchok_example_2.png
   :alt: VectorMoveDemo2.PNG

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Number-> :doc:`Random Num Gen </nodes/number/random_num_gen>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

The node will match different data structures, in this example a surface is generated from one Ngon

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/move/move_vectors_blender_sverchok_example_3.png
   :target: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/move/move_vectors_blender_sverchok_example_3.png

* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Modifiers->Modifier Make-> :doc:`UV Connection </nodes/modifier_make/uv_connect>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* MUL X, ADD X,Y: Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* Vector-> :doc:`Vector Math </nodes/vector/math_mk3>`
* Vector-> :doc:`Vector Noise </nodes/vector/noise_mk3>`
* List->List Struct-> :doc:`List Split </nodes/list_struct/split>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

---------

With the List Matching properties we can create different data matches, in this case with "Cycle" a complex rhythm is generated

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/move/move_vectors_blender_sverchok_example_4.png
   :target: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/move/move_vectors_blender_sverchok_example_4.png
   :alt: VectorMoveDemo4.PNG

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Combine a Z-Line with a circle. Change a List Match Property of Move node.

.. image:: https://user-images.githubusercontent.com/14288520/191324067-681349b7-44c0-428c-a65e-a34790e672e4.png
  :target: https://user-images.githubusercontent.com/14288520/191324067-681349b7-44c0-428c-a65e-a34790e672e4.png

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Generator-> :doc:`Segment </nodes/generator/segment>`
* Generator-> :doc:`Circle </nodes/generator/circle>`
* List->List Struct-> :doc:`List Item </nodes/list_struct/item>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`