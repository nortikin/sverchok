Dual Mesh
=========

.. image:: https://user-images.githubusercontent.com/14288520/200945022-5dce027f-28ce-4370-8783-f02c358ac76b.png
  :target: https://user-images.githubusercontent.com/14288520/200945022-5dce027f-28ce-4370-8783-f02c358ac76b.png

Functionality
-------------

This node generates dual mesh for the given mesh. Dual mesh is defined as a
mesh which has vertices at center of each face of source mesh; edges of the
dual mesh connect the vertices, which correspond to faces of original mesh with
common edge.

This node may be useful to convert the mesh consisting of Tris to mesh
consisting to NGons, or backwards.

Note that the volume of dual mesh is always a bit smaller than that of original mesh.

.. image:: https://user-images.githubusercontent.com/14288520/200946357-32156894-b4dd-43f3-b1af-918c920a619d.png
  :target: https://user-images.githubusercontent.com/14288520/200946357-32156894-b4dd-43f3-b1af-918c920a619d.png

Inputs
------

This node has the following inputs:

- **Vertices**. Vertices of original mesh. This input is mandatory.
- **Edges**. Edges of original mesh.
- **Faces**. Faces of original mesh. This input is mandatory.

Outputs
-------

This node has the following outputs:

- **Vertices**. Vertices of the dual mesh.
- **Faces**. Faces of the dual mesh.

Examples of Usage
-----------------

Dual mesh for cube is an octahedron:

.. image:: https://user-images.githubusercontent.com/284644/68086032-278bb800-fe69-11e9-80d5-5b46bde8d9b0.png
  :target: https://user-images.githubusercontent.com/284644/68086032-278bb800-fe69-11e9-80d5-5b46bde8d9b0.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Dual mesh for Voronoi diagram is Delaunay triangulation:

.. image:: https://user-images.githubusercontent.com/14288520/200948444-d01e794a-b3df-4422-bb72-c75434326422.png
  :target: https://user-images.githubusercontent.com/14288520/200948444-d01e794a-b3df-4422-bb72-c75434326422.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Transform-> :doc:`Randomize </nodes/transforms/randomize>`
* Modifiers->Modifier Change-> :doc:`Voronoi 2D </nodes/modifier_change/holes_fill>`
* Modifiers->Modifier Change-> :doc:`Fill Holes </nodes/modifier_change/holes_fill>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`