Delaunay 3D
===========

Dependencies
------------

This node requires SciPy_ library to work.

.. _SciPy: https://scipy.org/

Functionality
-------------

This node generaets a Delaunay_ triangulation for a set of points in 3D space.

.. _Delaunay: https://en.wikipedia.org/wiki/Delaunay_triangulation

In many cases, Delaunay triangulation in 3D tends to generate almost flat
tetrahedrons on the boundary. This node can automatically skip generation of
such tetrahedrons.

Inputs
------

This node has the following inputs:

* **Vertices**. The vertices to generate Delaunay triangulation for. This input is mandatory.
* **Threshold**. This defines the threshold used to filter "too flat"
  tetrahedrons out. Smaller values of threshold mean more "almost flat"
  tetrahedrons will be generated. Set this to 0 to skip this filtering step and
  allow to generate any tetrahedrons. The default value is 0.0001.

Parameters
----------

This node has the following parameter:

* **Join**. If checked, then the node will generate one mesh object, composed
  of all faces of all tetrahedrons (without duplicating vertices and faces).
  Otherwise, the node will generate a separate mesh object for each
  tetrahedron. Unchecked by default.

Outputs
-------

This node has the following outputs:

* **Vertices**. Vertices of the Delaunay triangulation.
* **Edges**. Edges of the Delaunay triangulation.
* **Faces**. Faces of the Delaunay triangulation.

Example of usage
----------------

.. image:: https://user-images.githubusercontent.com/284644/87226668-b8c70d00-c3ae-11ea-900d-ad7bee54f4eb.png

