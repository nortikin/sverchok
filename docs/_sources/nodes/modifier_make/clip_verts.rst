Clip Vertices
=============

.. image:: https://user-images.githubusercontent.com/14288520/200960985-def2d5c6-85cf-422c-9617-3bb3d916a417.png
  :target: https://user-images.githubusercontent.com/14288520/200960985-def2d5c6-85cf-422c-9617-3bb3d916a417.png

Functionality
-------------

This node cuts off (clips, truncates) all vertices of original mesh, by cutting
each edge in half, and then connecting centers of all edges incidental to each
vertex, to produce new faces. Please refer to usage examples for better
understanding.

This can give interesting topology, especially in combination with
"dual mesh" and/or "triangulate" and/or "join triangles" and/or "limited
dissolve" nodes.

.. image:: https://user-images.githubusercontent.com/14288520/201035921-1bb5ab23-7f33-430c-9be4-590d3dc227f7.png
  :target: https://user-images.githubusercontent.com/14288520/201035921-1bb5ab23-7f33-430c-9be4-590d3dc227f7.png

Inputs
------

This node has the following inputs:

- **Vertices**. Vertices of original mesh. This input is mandatory.
- **Edges**. Edges of original mesh.
- **Faces**. Faces of original mesh. This input is mandatory.

Outputs
-------

This node has the following outputs:

- **Vertices**. Vertices of the new mesh.
- **Edges**. Edges of the new mesh.
- **Faces**. Faces of the new mesh.

Examples of Usage
-----------------

Clip a simple plane / grid:

.. image:: https://user-images.githubusercontent.com/14288520/201036656-26edc580-2810-4794-99ce-6376b9891f56.png
  :target: https://user-images.githubusercontent.com/14288520/201036656-26edc580-2810-4794-99ce-6376b9891f56.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Clip vertices of a cube:

.. image:: https://user-images.githubusercontent.com/14288520/201037590-83643a05-f856-4db0-b80d-29bd6ae98415.png
  :target: https://user-images.githubusercontent.com/14288520/201037590-83643a05-f856-4db0-b80d-29bd6ae98415.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Applied to a cylinder:

.. image:: https://user-images.githubusercontent.com/14288520/201038962-4e65f478-cf6f-4171-934a-fe7e96b0c108.png
  :target: https://user-images.githubusercontent.com/14288520/201038962-4e65f478-cf6f-4171-934a-fe7e96b0c108.png

* Generator-> :doc:`Cylinder </nodes/generator/cylinder_mk2>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Applied to Suzanne:

.. image:: https://user-images.githubusercontent.com/14288520/201039845-46541257-eb9c-4a8f-b3e0-9ea94eaafda2.png
  :target: https://user-images.githubusercontent.com/14288520/201039845-46541257-eb9c-4a8f-b3e0-9ea94eaafda2.png

* Generator-> :doc:`Suzanne </nodes/generator/suzanne>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Apply node several times:

.. image:: https://user-images.githubusercontent.com/14288520/201617752-5703d4be-d2ae-45e1-82e2-4a890a5081b6.png
  :target: https://user-images.githubusercontent.com/14288520/201617752-5703d4be-d2ae-45e1-82e2-4a890a5081b6.png

* Generator-> :doc:`Cylinder </nodes/generator/cylinder_mk2>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
