Sphere Fit
==========

Functionality
-------------

This node tries to approximate the provided set of vertices by a sphere (in
other words, fit a sphere through given set of vertices). It searches for such
a sphere, that all provided vertices have the minimum distance to it.

The sphere is represented by it's center point and radius.

For this node to work correctly, it needs at least 4 vertices on the input.

Inputs
------

This node has the following input:

* **Vertices** - the vertices to be approximated with a sphere.

Outputs
-------

This node has the following outputs:

* **Center** - the center of the sphere.
* **Radius** - the radius of the sphere.
* **Projections** - projections of the input vertices to the sphere surface.
* **Diffs** - difference vectors, i.e. vectors pointing from original vertices
  to their projections to the sphere.
* **Distances** - distances from the original vertices to the sphere surface.

Examples of usage
-----------------

Fit a sphere for vertices from arbitrary mesh:

.. image:: https://user-images.githubusercontent.com/284644/74602397-d925c080-50c9-11ea-8981-9278eb618539.png

