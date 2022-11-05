Separate Parts To Indexes
=========================

.. image:: https://user-images.githubusercontent.com/14288520/199354331-3bb1f195-f53e-40a8-8e7f-ba5ab71eb454.png
  :target: https://user-images.githubusercontent.com/14288520/199354331-3bb1f195-f53e-40a8-8e7f-ba5ab71eb454.png

Functionality
-------------
Marks mesh elements by indexes. All disjoint parts of mesh have different indexes.
Elements of one part have a same index.

.. image:: https://user-images.githubusercontent.com/14288520/199355029-bad0b7bc-f5be-4b5f-b0fb-9961abae9178.png
  :target: https://user-images.githubusercontent.com/14288520/199355029-bad0b7bc-f5be-4b5f-b0fb-9961abae9178.png

Category
--------

Modifiers -> modifier change -> Separate perts to indexes

Inputs
------

- **Vertices** - vertices
- **Edges** - edges (optionally if faces are connected)
- **Faces** - faces (optionally if edges are connected)

Outputs
-------

- **Vert index** - index mask of verts
- **Edge index** - index mask of edges
- **Face index** - index mask of faces

.. image:: https://user-images.githubusercontent.com/14288520/199355010-98eef441-4a08-40ff-89e1-8ca56f2cb90c.png
  :target: https://user-images.githubusercontent.com/14288520/199355010-98eef441-4a08-40ff-89e1-8ca56f2cb90c.png

Examples
--------

.. image:: https://user-images.githubusercontent.com/14288520/199355473-75e689d0-fa9d-45ae-8056-529805ac29a9.png
  :target: https://user-images.githubusercontent.com/14288520/199355473-75e689d0-fa9d-45ae-8056-529805ac29a9.png

* Generator-> :doc:`Cricket </nodes/generator/cricket>`
* DIV: Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* List->List Main-> :doc:`Selected Statistics </nodes/list_main/statistics>`
* List->List Struct-> :doc:`List First & Last </nodes/list_struct/start_end>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Color-> :doc:`Color Ramp </nodes/color/color_ramp>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Using index mask for assigning material to separate parts of mesh:

.. image:: https://user-images.githubusercontent.com/28003269/72244444-b6564700-3607-11ea-8662-51727aaddfb4.png
  :target: https://user-images.githubusercontent.com/28003269/72244444-b6564700-3607-11ea-8662-51727aaddfb4.png

* Generator-> :doc:`Suzanne </nodes/generator/suzanne>`
* Viz-> :doc:`Mesh Viewer </nodes/viz/mesh_viewer>`
* BPY Data-> :doc:`Assign Materials List </nodes/object_nodes/assign_materials>`
* BPY Data-> :doc:`Set Material Index </nodes/object_nodes/material_index>`

---------

Moving disjoint parts =):

.. image:: https://user-images.githubusercontent.com/28003269/73347608-53201200-42a1-11ea-96bb-358ada087da4.png
  :target: https://user-images.githubusercontent.com/28003269/73347608-53201200-42a1-11ea-96bb-358ada087da4.png

* Generator-> :doc:`Cricket </nodes/generator/cricket>`
* Transform-> :doc:`Transform Mesh </nodes/transforms/transform_mesh>`
* MUL: Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Set: List-> :doc:`List Modifier </nodes/list_mutators/modifier>`
* Scene-> :doc:`Frame Info </nodes/scene/frame_info_mk2>`

.. image:: https://user-images.githubusercontent.com/28003269/73347577-469bb980-42a1-11ea-889b-b4d87c754f2d.gif
  :target: https://user-images.githubusercontent.com/28003269/73347577-469bb980-42a1-11ea-889b-b4d87c754f2d.gif
