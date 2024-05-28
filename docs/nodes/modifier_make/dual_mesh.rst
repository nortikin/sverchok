Dual Mesh
=========

.. image:: https://github.com/satabol/pyQuadriFlow/assets/14288520/3f124c3b-1974-47a3-9cd0-8be2df01c496
  :target: https://github.com/satabol/pyQuadriFlow/assets/14288520/3f124c3b-1974-47a3-9cd0-8be2df01c496

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

.. image:: https://github.com/nortikin/sverchok/assets/14288520/982ac4df-55df-4301-a3ba-bcb986904b35
  :target: https://github.com/nortikin/sverchok/assets/14288520/982ac4df-55df-4301-a3ba-bcb986904b35

This node has the following inputs:

- **Vertices**. Vertices of original mesh. This input is mandatory.
- **Edges**. Edges of original mesh.
- **Polygons**. Faces of original mesh. This input is mandatory.
- **Levels**. Levels of Dual Mesh (recursion)

  .. image:: https://github.com/nortikin/sverchok/assets/14288520/080a9e60-bc6c-451e-97d3-4d29d8596121
    :target: https://github.com/nortikin/sverchok/assets/14288520/080a9e60-bc6c-451e-97d3-4d29d8596121

Parameters
----------

.. image:: https://github.com/nortikin/sverchok/assets/14288520/96d5b2d9-2a25-4bea-b50a-573ee0de6927
  :target: https://github.com/nortikin/sverchok/assets/14288520/96d5b2d9-2a25-4bea-b50a-573ee0de6927

- **Keep Boundaries** - Keep non-manifold boundaries of the mesh in place by avoiding the dual transformation there. Has no influence if Levels==0

  .. image:: https://github.com/nortikin/sverchok/assets/14288520/1c27f774-4d50-4db6-9f87-131a3f594590
    :target: https://github.com/nortikin/sverchok/assets/14288520/1c27f774-4d50-4db6-9f87-131a3f594590

  This parameter can do strange results sometime:

  .. image:: https://github.com/nortikin/sverchok/assets/14288520/eccf9081-9c3c-472d-bbff-4fa4b9ede04c
    :target: https://github.com/nortikin/sverchok/assets/14288520/eccf9081-9c3c-472d-bbff-4fa4b9ede04c

Outputs
-------
.. image:: https://github.com/nortikin/sverchok/assets/14288520/9f82d3f2-c3d6-49ee-9b03-e871d4c7652a
  :target: https://github.com/nortikin/sverchok/assets/14288520/9f82d3f2-c3d6-49ee-9b03-e871d4c7652a

This node has the following outputs:

- **Vertices**. Vertices of the dual mesh.
- **Edges**. Edges of the dual mesh.
- **Polygons**. Faces of the dual mesh.
- **Levels**. Repeat Levels input. For your convinience to use it as a Number node.

Examples of Usage
-----------------

Dual mesh for lowpoly cylinder:

.. image:: https://github.com/nortikin/sverchok/assets/14288520/7af16514-cbe3-40d9-8c58-5058521ddd72
  :target: https://github.com/nortikin/sverchok/assets/14288520/7af16514-cbe3-40d9-8c58-5058521ddd72

* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Scene-> :doc:`Get Objects Data </nodes/scene/get_objects_data>`

---------

Dual mesh for Voronoi diagram is Delaunay triangulation:

.. image:: https://user-images.githubusercontent.com/14288520/200948444-d01e794a-b3df-4422-bb72-c75434326422.png
  :target: https://user-images.githubusercontent.com/14288520/200948444-d01e794a-b3df-4422-bb72-c75434326422.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Transform-> :doc:`Randomize </nodes/transforms/randomize>`
* Modifiers->Modifier Change-> :doc:`Voronoi 2D </nodes/modifier_change/holes_fill>`
* Modifiers->Modifier Change-> :doc:`Fill Holes </nodes/modifier_change/holes_fill>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`