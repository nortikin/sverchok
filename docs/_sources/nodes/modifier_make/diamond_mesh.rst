Diamond Mesh
============

.. image:: https://user-images.githubusercontent.com/14288520/200949333-22865d83-ab99-4e1b-afa6-ec87666565b8.png
  :target: https://user-images.githubusercontent.com/14288520/200949333-22865d83-ab99-4e1b-afa6-ec87666565b8.png

Functionality
-------------

This node generates a new (rhomboidal / diamond-like) mesh, by replacing each
edge of original mesh by a rhombus (connecting centers of two incidental
faces). This can give interesting topology, especially in combination with
"dual mesh" and/or "triangulate" and/or "join triangles" and/or "limited
dissolve" nodes.

.. image:: https://user-images.githubusercontent.com/14288520/200955270-c6cbac0c-e512-4c67-987e-f0cf7dae0a98.png
  :target: https://user-images.githubusercontent.com/14288520/200955270-c6cbac0c-e512-4c67-987e-f0cf7dae0a98.png

Inputs
------

This node has the following inputs:

- **Vertices**. Vertices of original mesh. This input is mandatory.
- **Edges**. Edges of original mesh.
- **Faces**. Faces of original mesh. This input is mandatory.

Outputs
-------

This node has the following outputs:

- **Vertices**. Vertices of the diamond mesh.
- **Edges**. Edges of the diamond mesh.
- **Faces**. Faces of the diamond mesh.

Examples of Usage
-----------------

The simplest example — diamond mesh for a plane / grid:

.. image:: https://user-images.githubusercontent.com/14288520/200955808-7c0d5780-dce8-4354-92a7-ee4b8c0b5375.png
  :target: https://user-images.githubusercontent.com/14288520/200955808-7c0d5780-dce8-4354-92a7-ee4b8c0b5375.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Diamond mesh for a cube:

.. image:: https://user-images.githubusercontent.com/14288520/200957358-c69b7738-4f6a-4594-b390-f7f8396d5633.png
  :target: https://user-images.githubusercontent.com/14288520/200957358-c69b7738-4f6a-4594-b390-f7f8396d5633.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Modifiers->Modifier Change-> :doc:`Split Faces </nodes/modifier_change/split_faces>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

In combination with "dual mesh" node:

.. image:: https://user-images.githubusercontent.com/14288520/200959724-5f9f906f-4583-40de-90ed-8ba931349e84.png
  :target: https://user-images.githubusercontent.com/14288520/200959724-5f9f906f-4583-40de-90ed-8ba931349e84.png

* Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`
* Modifiers->Modifier Make-> :doc:`Dual Mesh </nodes/modifier_make/dual_mesh>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

In another combination with "dual mesh" node:

.. image:: https://user-images.githubusercontent.com/14288520/200960269-25907776-a6fd-426a-8034-38822f6c6c84.png
  :target: https://user-images.githubusercontent.com/14288520/200960269-25907776-a6fd-426a-8034-38822f6c6c84.png

* Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`
* Modifiers->Modifier Make-> :doc:`Dual Mesh </nodes/modifier_make/dual_mesh>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
