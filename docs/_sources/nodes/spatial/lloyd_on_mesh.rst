Lloyd on Mesh
=============

.. image:: https://user-images.githubusercontent.com/14288520/202813275-96c4f11c-a95e-4cc2-aba1-420dd258ca36.png
  :target: https://user-images.githubusercontent.com/14288520/202813275-96c4f11c-a95e-4cc2-aba1-420dd258ca36.png

Dependencies
------------

This node requires SciPy_ library to work.

.. _SciPy: https://scipy.org/

Functionality
-------------

This node uses Lloyd_ algorithm to redistribute a set of points on the surface
of arbitrary mesh uniformly. If provided points do not lie on the mesh, they
will be projected onto the mesh first.

To generate Lloyd distribution on the mesh, Voronoi diagram is generated in the
region of space, defined by some maximum distance from the mesh (layer of some
thickness). Thickness of this layer can affect resulting distribution slightly.

Optionally, weighted Lloyd algorithm can be used, to put points more dense in
places to which higher weight is assigned.

.. _Lloyd: https://en.wikipedia.org/wiki/Lloyd%27s_algorithm

Inputs
------

This node has the following inputs:

* **Vertices**. Vertices of the mesh, on which the points are to be
  distributed. This input is mandatory.
* **Faces**. Faces of the mesh, on which the points are to be
  distributed. This input is mandatory.
* **Sites**. Initial points to be redistributed. This input is mandatory.
* **Iterations**. Number of Lloyd's algorithm iterations. The default value is 3.
* **Thickness**. Thickness of region where Voronoi diagram is generated. The
  default value is 1.0.
* **Weights**. Scalar Field object used to assign different weights for
  different places in 3D space. More points will be put in places which have
  bigger weight. This input is optional. If not connected, uniform Lloyd
  algorithm will be used.

Outputs
-------

This node has the following output:

* **Sites**. Redisrtibuted points.

Example of Usage
----------------

.. image:: https://user-images.githubusercontent.com/14288520/202814364-f58907d3-67a4-467e-93e7-44acbe22be2b.png
  :target: https://user-images.githubusercontent.com/14288520/202814364-f58907d3-67a4-467e-93e7-44acbe22be2b.png

* Generator-> :doc:`Suzanne </nodes/generator/suzanne>`
* Spatial-> :doc:`Populate Mesh </nodes/spatial/populate_mesh_mk2>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

.. image:: https://user-images.githubusercontent.com/14288520/202815217-e3ce3c1c-1855-46b3-ae01-af3d36433fa9.png
  :target: https://user-images.githubusercontent.com/14288520/202815217-e3ce3c1c-1855-46b3-ae01-af3d36433fa9.png

* Generator-> :doc:`Suzanne </nodes/generator/suzanne>`
* Spatial-> :doc:`Populate Mesh </nodes/spatial/populate_mesh_mk2>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://user-images.githubusercontent.com/14288520/202814946-ae47a3b1-3063-4254-aec2-f404327a590f.gif
  :target: https://user-images.githubusercontent.com/14288520/202814946-ae47a3b1-3063-4254-aec2-f404327a590f.gif
