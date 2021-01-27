Concave Hull
============

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

Parameters
----------

This node has the following parameter:

* **Correct normals**. If checked, the node will recalculate the normals of
  generated mesh, so that they all point outside. Otherwise, the orientation of
  faces is not guaranteed. Checked by default.

Outputs
-------

This node has the following outputs:

* **Vertices**. Vertices of generated mesh.
* **Edges**. Edges of generated mesh.
* **Faces**. Faces of generated mesh.

Examples of Usage
-----------------

1. Generate points on Suzanne mesh, and generate concave hull for them:

.. image:: https://user-images.githubusercontent.com/284644/99681287-c8163f80-2a9f-11eb-8f30-4afd49fd338f.png

2. In some cases, together with "Dual Shape" node, this node can be used to
   generate Voronoi diagrams on surface of Solid or mesh objects:

.. image:: https://user-images.githubusercontent.com/284644/100535011-f7167900-3236-11eb-85d2-764ce1f99e6a.png

