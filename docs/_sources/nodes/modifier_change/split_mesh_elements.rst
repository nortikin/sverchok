===================
Split Mesh Elements
===================

.. image:: https://user-images.githubusercontent.com/14288520/199832286-b909233f-7b40-4d38-9920-e56ca6b8f8b6.png
  :target: https://user-images.githubusercontent.com/14288520/199832286-b909233f-7b40-4d38-9920-e56ca6b8f8b6.png

Functionality
-------------

The node split selected by mask elements. It has two modes:

edges
  It's similar to Split -> Faces by Edges Blender tool. When two or more
  touching interior edges, or a border edge is selected, a hole will be created,
  and the selected edges will be duplicated to form the border of the hole.

verts
  It's similar to Split -> Faces & Edges by Vertices Blender tool. It in the
  same way as in edges mode except that it also splits the vertices of the
  adjacent connecting edges.

.. image:: https://user-images.githubusercontent.com/14288520/199840145-a77199a7-7dbc-4736-a1f2-805015a99b82.png
  :target: https://user-images.githubusercontent.com/14288520/199840145-a77199a7-7dbc-4736-a1f2-805015a99b82.png

Inputs
------

* **Vertices** - Vertices of the input object
* **Edges** - Edges of the input object
* **Faces** - Faces of the input object
* **FaceData** - Face attribute of the input object
* **Mask** - Selection mask. It also has option which type of selection is given (vertexes, edges or faces selection)

Outputs
-------

* **Vertices** - Vertices of the final object
* **Edges** - Edges of the final object
* **Faces** - Faces of the final object
* **FaceData** - Face attribute of the final object

Examples
--------

Split a mesh into random pieces

.. image:: https://user-images.githubusercontent.com/14288520/199853840-5d9fcb66-98fd-4621-97ed-1aefbc75a906.png
  :target: https://user-images.githubusercontent.com/14288520/199853840-5d9fcb66-98fd-4621-97ed-1aefbc75a906.png

* Generator-> :doc:`Suzanne </nodes/generator/suzanne>`
* Modifiers->Modifier Change :doc:`Separate Loose Parts </nodes/modifier_change/mesh_separate>`
* Number-> :doc:`List Input </nodes/number/list_input>`
* Number-> :doc:`Random Num Gen </nodes/number/random_num_gen>`
* List->List Struct-> :doc:`List Levels </nodes/list_struct/levels>`
* Viz-> :doc:`Mesh Viewer </nodes/viz/mesh_viewer>`

.. image:: https://user-images.githubusercontent.com/14288520/199854590-62cdcaa6-6b30-4aef-a94d-64aa7a9cbdb3.gif
  :target: https://user-images.githubusercontent.com/14288520/199854590-62cdcaa6-6b30-4aef-a94d-64aa7a9cbdb3.gif