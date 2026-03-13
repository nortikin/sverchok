Concave Hull
============

.. image:: https://user-images.githubusercontent.com/14288520/202859436-2ad37262-2fb8-4331-877d-745e51da8780.png
  :target: https://user-images.githubusercontent.com/14288520/202859436-2ad37262-2fb8-4331-877d-745e51da8780.png

Dependencies
------------

This node requires SciPy_ library to work.

.. _SciPy: https://scipy.org/

Functionality
-------------

This node generates a "Concave Hull" mesh of given set of points, by use of
AlphaShape_ algorithm. Alpha Shape algorithm uses Delaunay_ triangulation to
work.

In many cases, Delaunay triangulation in 3D tends to generate almost flat
tetrahedrons on the boundary. This node can automatically skip generation of
such tetrahedrons.

.. _AlphaShape: https://en.wikipedia.org/wiki/Alpha_shape
.. _Delaunay: https://en.wikipedia.org/wiki/Delaunay_triangulation

Inputs
------

This node has the following inputs:

* **Vertices**. The vertices to generate concave hull for. This input is mandatory.
* **Alpha**. Alpha value for the Alpha Shape algorithm. Bigger values
  correspond to bigger volume of the generated mesh. If the value is too small,
  the mesh can be non-manifold (have holes in it). The default value is 2.0.

.. image:: https://user-images.githubusercontent.com/14288520/202859726-c3613e05-f9c5-4628-9b39-3988c4a21a3d.gif
  :target: https://user-images.githubusercontent.com/14288520/202859726-c3613e05-f9c5-4628-9b39-3988c4a21a3d.gif

Parameters
----------

This node has the following parameter:

* **Correct normals**. If checked, the node will recalculate the normals of
  generated mesh, so that they all point outside. Otherwise, the orientation of
  faces is not guaranteed. Checked by default.

.. image:: https://user-images.githubusercontent.com/14288520/202864738-ac3fba3f-efce-4429-98d2-0171230f951d.png
  :target: https://user-images.githubusercontent.com/14288520/202864738-ac3fba3f-efce-4429-98d2-0171230f951d.png

.. image:: https://user-images.githubusercontent.com/14288520/202864721-39e8a7c0-cd9d-4f26-b48f-b6979ec779a3.png
  :target: https://user-images.githubusercontent.com/14288520/202864721-39e8a7c0-cd9d-4f26-b48f-b6979ec779a3.png

Outputs
-------

This node has the following outputs:

* **Vertices**. Vertices of generated mesh.
* **Edges**. Edges of generated mesh.
* **Faces**. Faces of generated mesh.

Examples of Usage
-----------------

1. Generate points on Suzanne mesh, and generate concave hull for them:

.. image:: https://user-images.githubusercontent.com/14288520/202860801-f540fe36-6332-4575-bba1-705ae288fb46.png
  :target: https://user-images.githubusercontent.com/14288520/202860801-f540fe36-6332-4575-bba1-705ae288fb46.png

* Generator-> :doc:`Suzanne </nodes/generator/suzanne>`
* Spatial-> :doc:`Populate Mesh </nodes/spatial/populate_mesh_mk2>`
* Spatial-> :doc:`Lloyd on Mesh </nodes/spatial/lloyd_on_mesh>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

2. In some cases, together with "Dual Shape" node, this node can be used to
   generate Voronoi diagrams on surface of Solid or mesh objects:

.. image:: https://user-images.githubusercontent.com/14288520/202861218-c3528518-c425-487e-86bd-f0e86e80d3ec.png
  :target: https://user-images.githubusercontent.com/14288520/202861218-c3528518-c425-487e-86bd-f0e86e80d3ec.png

* Solids-> :doc:`Torus (Solid) </nodes/solid/torus_solid>`
* Spatial-> :doc:`Populate Solid </nodes/spatial/populate_solid>`
* Modifiers->Modifier Make-> :doc:`Dual Mesh </nodes/modifier_make/dual_mesh>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
