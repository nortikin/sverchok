Voronoi Sphere
==============

Dependencies
------------

This node requires SciPy_ library to work.

.. _SciPy: https://scipy.org/

Functionality
-------------

This node generates a Voronoi_ diagram for set of points (sites) on a spherical
surface. If provided vertices are not lying on a sphere, they will be projected
to the sphere first.

.. _Voronoi: https://en.wikipedia.org/wiki/Voronoi_diagram

Inputs
------

This node has the following inputs:

* **Vertices**. The vertices to generate a Voronoi diagram for. This input is
  mandatory.
* **Center**. The sphere center. The default value is ``(0, 0, 0)``.
* **Radius**. The sphere radius. The default value is 1.0.

Outputs
-------

This node has the following outputs:

* **Vertices**. Vertices of the generated Voronoi diagram.
* **Edges**. Edges of the generated diagram.
* **Faces**. Faces of the generated diagram.

Example of usage
----------------

.. image:: https://user-images.githubusercontent.com/284644/87226285-38071180-c3ac-11ea-84c7-a875e4980e08.png

