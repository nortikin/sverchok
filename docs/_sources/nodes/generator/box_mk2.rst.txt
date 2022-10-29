Box
===

.. image:: https://user-images.githubusercontent.com/14288520/188669831-ad397459-d35c-4657-8bb4-b1dcfa4af392.png
  :target: https://user-images.githubusercontent.com/14288520/188669831-ad397459-d35c-4657-8bb4-b1dcfa4af392.png

Functionality
-------------

Offers a Box primitive with variable X,Y and Z divisions, and overall Size.

.. image:: https://user-images.githubusercontent.com/14288520/191239876-74a9a2de-0e48-47f5-9c21-bd12977874a6.png
  :target: https://user-images.githubusercontent.com/14288520/191239876-74a9a2de-0e48-47f5-9c21-bd12977874a6.png

Inputs
------

All inputs are vectorized and the data will be matched according to the advanced properties 'Match List Global' and 'Match List Local'

* **Size**: Base size of the box
* **Div X**: Divisions along X axis, it will cast incoming `floats` to `int`.
* **Div Y**: Divisions along Y axis, it will cast incoming `floats` to `int`.
* **Div Z**: Divisions along Z axis, it will cast incoming `floats` to `int`.
* **Matrix**: Input to control position, scale and rotation of the box

Parameters
----------

* **Origin**: Set where the origin of the box will be. It can be Center, Bottom (bottom center) or Corner (the bottom left front corner)

Advanced Parameters
-------------------

In the N-Panel (and on the right-click menu) you can find:

**Simplify Output**: Method to keep output data suitable for most of the rest of the Sverchok nodes
  - None: Do not perform any change on the data. Only for advanced users
  - Join: The node will join the deepest level of boxes in one object
  - Flat: It will flat the output to keep the one box per object

**Match List Global**: Define how list with different lengths should be matched. Refers to the matching of groups (level 1)

**Match List Local**: Define how list with different lengths should be matched. Refers to the matching inside groups (level 2)

**Output NumPy**: Get NumPy arrays in stead of regular lists (makes the node faster). Available for Vertices, Edges and Pols

Outputs
-------

- Verts
- Edges
- Faces

Examples
--------

Basic example generating a box 5 x 3  x 1

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/generators/box/box_node_sverchok_example_0.png
  :target: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/generators/box/box_node_sverchok_example_0.png

* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

All inputs are vectorized, note that to match the first inputs structure the *Flat Output* checkbox of the Matrix In node is un-checked.


.. image:: https://user-images.githubusercontent.com/14288520/188686962-13dad19a-1bcb-4547-8f42-7ff7a82bb678.png
  :target: https://user-images.githubusercontent.com/14288520/188686962-13dad19a-1bcb-4547-8f42-7ff7a82bb678.png

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/generators/box/box_node_sverchok_example.png
  :target: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/generators/box/box_node_sverchok_example.png

* Number-> :doc:`Random Num Gen </nodes/number/random_num_gen>`
* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

The *Flat Output* checkbox of the second Matrix In node is un-checked. On the first 6 boxes are generated, on the second just 3 boxes are created.

.. image:: https://user-images.githubusercontent.com/14288520/188686507-01c9981a-03fb-4f98-8b9f-394fd27ada4e.png
  :target: https://user-images.githubusercontent.com/14288520/188686507-01c9981a-03fb-4f98-8b9f-394fd27ada4e.png

* Number-> :doc:`Number Range </nodes/number/number_range>`
* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

Boxes in the corner of boxes repeatedly

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/generators/box/box_node_sverchok_example_2.png
  :target: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/generators/box/box_node_sverchok_example_2.png

* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

Different data shapes output depending on "Simplify Output" advanced property

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/generators/box/box_node_sverchok_example_3.png
  :target: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/generators/box/box_node_sverchok_example_3.png

* Number-> :doc:`Number Range </nodes/number/number_range>`
* List->List Struct-> :doc:`List Split </nodes/list_struct/split>`
* Text-> :doc:`Data Shape </nodes/text/shape>`
* Text-> :doc:`Note </nodes/text/note>`