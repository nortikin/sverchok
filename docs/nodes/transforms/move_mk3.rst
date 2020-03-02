Move
====

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


Moving vertices along Y direction with a random multiplier

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/move/move_vectors_blender_sverchok_example_2.png
   :alt: VectorMoveDemo2.PNG

The node will match different data structures, in this example a surface is generated from one Ngon

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/move/move_vectors_blender_sverchok_example_3.png


With the List Matching properties we can create different data matches, in this case with "Cycle" a complex rhythm is generated

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/move/move_vectors_blender_sverchok_example_4.png
   :alt: VectorMoveDemo4.PNG
