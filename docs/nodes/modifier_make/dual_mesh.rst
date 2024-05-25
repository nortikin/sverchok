Dual Mesh
=========

.. image:: https://github.com/nortikin/sverchok/assets/14288520/a7aff115-49ef-4136-b627-dda87f6baa4d
  :target: https://github.com/nortikin/sverchok/assets/14288520/a7aff115-49ef-4136-b627-dda87f6baa4d

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

.. image:: https://github.com/nortikin/sverchok/assets/14288520/307d5cfd-3998-4cfb-86e1-0cc8e264316c
  :target: https://github.com/nortikin/sverchok/assets/14288520/307d5cfd-3998-4cfb-86e1-0cc8e264316c

This node has the following inputs:

- **Vertices**. Vertices of original mesh. This input is mandatory.
- **Edges**. Edges of original mesh.
- **Polygons**. Faces of original mesh. This input is mandatory.
- **Levels**. Levels of Dual Mesh (recursion)

  .. image:: https://github.com/nortikin/sverchok/assets/14288520/080a9e60-bc6c-451e-97d3-4d29d8596121
    :target: https://github.com/nortikin/sverchok/assets/14288520/080a9e60-bc6c-451e-97d3-4d29d8596121

Parameters
----------

.. image:: https://github.com/nortikin/sverchok/assets/14288520/a6b74434-df6b-4b57-abbf-24fc08e5c455
  :target: https://github.com/nortikin/sverchok/assets/14288520/a6b74434-df6b-4b57-abbf-24fc08e5c455

- **Keep Boundaries** - Keep non-manifold boundaries of the mesh in place by avoiding the dual transformation there. Has no influence if Levels==0

  .. image:: https://github.com/nortikin/sverchok/assets/14288520/1c27f774-4d50-4db6-9f87-131a3f594590
    :target: https://github.com/nortikin/sverchok/assets/14288520/1c27f774-4d50-4db6-9f87-131a3f594590

Outputs
-------
.. image:: https://github.com/nortikin/sverchok/assets/14288520/919676b2-6d15-4148-9bcd-1921577fda1c
  :target: https://github.com/nortikin/sverchok/assets/14288520/919676b2-6d15-4148-9bcd-1921577fda1c

This node has the following outputs:

- **Vertices**. Vertices of the dual mesh.
- **Edges**. Edges of the dual mesh.
- **Polygons**. Faces of the dual mesh.
- **Edges Mask as Boundaries**. Process Manifold/Non manifold edges as Boundary Edge (For the first level only. For Levels 2,3 and so on this mask will be skipped).
- **Levels**. Repeat Levels input. For your convinience to use it as a Number node.

Examples of Usage
-----------------

Dual mesh for lowpoly cylinder:

.. image:: https://github.com/nortikin/sverchok/assets/14288520/493b98a1-65af-4d8c-b4dd-f7fda2a9586d
  :target: https://github.com/nortikin/sverchok/assets/14288520/493b98a1-65af-4d8c-b4dd-f7fda2a9586d

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