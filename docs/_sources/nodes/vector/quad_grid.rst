Sort Quad Grid
==============

.. image:: https://user-images.githubusercontent.com/14288520/189407906-66eb8edb-86a9-42c9-a643-84ae8030f1fb.png
  :target: https://user-images.githubusercontent.com/14288520/189407906-66eb8edb-86a9-42c9-a643-84ae8030f1fb.png

Functionality
-------------

Consider you want to use a quad grid, i.e. a mesh made of quads only, arranged
in topology equivalent to subdivided Plane object. If you make such mesh in
other way than by use of Sverchok's "Plane" node, for example, by using
Blender's standard "Subdivide" or "Extrude" operations, then most probably the
order of vertices in such mesh will be near to random. On the other hand,
sometimes you need these vertices to be ordered according to grid topology, row
by row, column by column. For example, it can be useful for creating Nurbs
surfaces with "Build NURBS Surface" node.

This node takes a mesh (vertices, edges and faces) and outputs the sorted
vertices. It can output a separate list of vertices for each row, or it can
join all rows into one list.

For cases when the mesh is placed in some non-trivial manner (for example,
imagine a plane rolled up like a cylinder or a torus, or something even more
complex), it can be not obvious from which corner the node should start
enumerating vertices, and in which direction. For such cases, the node has
parameters to manipulate the order of vertices.

If the input mesh's topology is not equivalent to subdivided plane (i.e. M rows
by N columns of vertices), the node will fail (become red).

Inputs
------

This node has the following inputs:

* **Vertices**. The vertices of the input mesh. This input is mandatory.
* **Edges**. Edges of the input mesh. Either edges or faces must be provided.
* **Faces**. Faces of the input mesh. Either edges or faces must be provided.

Parameters
----------

This node has the following parameters:

* **Reverse rows**. If checked, then the node will reverse the order of rows in the
  output list: it will output last row first, and so on. Unchecked by default.
* **Reverse columns**. If checked, the node will reverse the order of vertices in
  each row. Unchecked by default.
* **Transpose**. If checked, the node will transpose the resulting list of
  vertices, i.e turn all rows into columns and vice versa. Unchecked by
  default.
* **Join rows**. If checked, the node will concatenate all rows of vertices
  into one list. Otherwise, it will output a separate list of vertices for each
  row. Unchecked by default.

Outputs
-------

This node has the following outputs:

* **Vertices**. The sorted vertices.
* **Indexes**. For each vertex in the **Verices** output, this output contains
  the index of this vertex in the input list of vertices.

Examples of usage
-----------------

Take manually subdivided plane (on the left) and sort it's vertices:

.. image:: https://user-images.githubusercontent.com/284644/93013046-65e02080-f5be-11ea-9d0b-7369cf76b9e2.png
  :target: https://user-images.githubusercontent.com/284644/93013046-65e02080-f5be-11ea-9d0b-7369cf76b9e2.png

* Transform-> :doc:`Move </nodes/transforms/move_mk3>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Viewer Index+ </nodes/viz/viewer_idx28>`
* Scene-> :doc:`Objects In Lite </nodes/scene/objects_in_lite>`

Use together with "Build NURBS Surface" node:

.. image:: https://user-images.githubusercontent.com/284644/93013197-9eccc500-f5bf-11ea-905b-4e929f1ee2bb.png
  :target: https://user-images.githubusercontent.com/284644/93013197-9eccc500-f5bf-11ea-905b-4e929f1ee2bb.png

* Surfaces-> :doc:`Build Nurbs Surface </nodes/surface/nurbs_surface>`
* Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Scene-> :doc:`Objects In Lite </nodes/scene/objects_in_lite>`