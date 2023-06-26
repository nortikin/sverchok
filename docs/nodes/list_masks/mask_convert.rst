Mask Converter
==============

.. image:: https://user-images.githubusercontent.com/14288520/188221908-30557dfb-9fb6-434a-ac7e-fce30ab8658a.png
  :target: https://user-images.githubusercontent.com/14288520/188221908-30557dfb-9fb6-434a-ac7e-fce30ab8658a.png

Functionality
-------------

This node allows to convert masks that are to be applied to different types of mesh elements. For example, it can convert mask on vertices to mask for faces, or mask for edges to mask for vertices, and so on.

Type of mask which is provided at input is defined by **From** parameter. Masks of all other types are available as outputs.

Inputs
------

This node has the following inputs:

* **Vertices**. This input is available and required only when parameter **From** is set to **Edges** or **Faces**.
* **VerticesMask**. Mask for vertices. This input is available only when parameter **From** is set to **Vertices**.
* **EdgesMask**. Mask for edges. This input is available only when parameter **From** is set to **Edges**.
* **FacesMask**. Mask for faces. This input is available only when parameter **From** is set to **Faces**.

Parameters
----------

This node has the following parameters:

- **From**. This parameter determines what type of mask you have as input. The following values are supported:

  - **Vertices**. Convert mask for vertices to masks for edges and faces.
  - **Edges**. Convert mask for edges to masks for vertices and faces.
  - **Faces**. Convert mask for faces to masks for vertices and edges.
- **Include partial selection**. If checked, then partially selected elements will be accounted as selected.

  - **Vertex** can be never partially selected, it is either selected or not.
  - **Edge** is partially selected if it has only one of its vertices selected.
  - **Face** is partially selected if only some of its vertices or faces are selected.

Outputs
-------

This node has the following outputs:

* **VerticesMask**. Mask for vertices. This output is not available if parameter **From** is set to **Vertices**.
* **EdgesMask**. Mask for edges. This output is not available if parameter **From** is set to **Edges**.
* **FacesMask**. Mask for faces. This output is not available if parameter **From** is set to **Faces**.

See also
--------

* Transform-> :doc:`Transform Select </nodes/transforms/transform_select>`

Examples of usage
-----------------

**Show part of cube with vertex selected by edges:**

.. image:: https://user-images.githubusercontent.com/14288520/188229456-1fe95a77-f3be-42dd-9a7f-943cb2ede6c9.png
  :target: https://user-images.githubusercontent.com/14288520/188229456-1fe95a77-f3be-42dd-9a7f-943cb2ede6c9.png

* Number-> :doc:`List Input </nodes/number/list_input>`
* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Modifiers->Modifier Change-> :doc:`Mask Vertices </nodes/modifier_change/vertices_mask>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Viewer Index+ </nodes/viz/viewer_idx28>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

---------

**Select face of cube by selecting its vertices, and extrude it:**

.. image:: https://user-images.githubusercontent.com/14288520/188221928-47e369de-3ef5-4044-aa76-53397f9f1dee.png
  :target: https://user-images.githubusercontent.com/14288520/188221928-47e369de-3ef5-4044-aa76-53397f9f1dee.png

* Number-> :doc:`List Input </nodes/number/list_input>`
* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Modifiers->Modifier Change-> :doc:`Extrude Region </nodes/modifier_change/extrude_region>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Viewer Index+ </nodes/viz/viewer_idx28>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

---------

**Select faces of sphere with small area, and move corresponding vertices:**

.. image:: https://cloud.githubusercontent.com/assets/284644/25284914/5843a476-26da-11e7-908a-5eb9ed694ccb.png
  :target: https://cloud.githubusercontent.com/assets/284644/25284914/5843a476-26da-11e7-908a-5eb9ed694ccb.png

---------

**Select edges of randomly selected faces:**

.. image:: https://user-images.githubusercontent.com/28003269/83627743-7a1c8680-a5a8-11ea-99d1-ff9f01762216.png
  :target: https://user-images.githubusercontent.com/28003269/83627743-7a1c8680-a5a8-11ea-99d1-ff9f01762216.png

---------

Filter vertices and edges if some faces hidden:

.. image:: https://user-images.githubusercontent.com/14288520/188969070-a084e68a-a657-4106-b9bf-a538f218a16c.png
  :target: https://user-images.githubusercontent.com/14288520/188969070-a084e68a-a657-4106-b9bf-a538f218a16c.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Modifiers->Modifier Change-> :doc:`Mask Vertices </nodes/modifier_change/vertices_mask>`
* Number-> :doc:`Random Num Gen </nodes/number/random_num_gen>`
* List-> :doc:`List Mask (Out) </nodes/list_masks/mask>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`
* Logic-> :doc:`Logic Functions (Not) </nodes/logic/logic_node>`

.. image:: https://user-images.githubusercontent.com/14288520/188969187-0dafea41-0015-4eda-ae8d-ae8384b7f060.gif
  :target: https://user-images.githubusercontent.com/14288520/188969187-0dafea41-0015-4eda-ae8d-ae8384b7f060.gif