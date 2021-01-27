Circle Fit
==========

Functionality
-------------

This node tries to approximate the provided set of vertices by a circle (i.e.,
fit a cirle through given set of vertices). It searches for such a circle, that
all provided vertices have minimum distance to it.

The circle is represented by it's center, it's radius, and a normal of a plane
it is lying in.

For this node to work correctly, it needs at least 3 vertices on the input.

Inputs
------

This node has the following input:

* **Vertices** - the vertices to be approximated with a circle.

Outputs
-------

This node has the following outputs:

* **Center** - the center of the circle.
* **Radius** - the radius of the circle.
* **Normal** - normal of the plane to which the circle belongs.
* **Matrix** - matrix mapping to the circle local coordinates; Z axis of this
  matrix is parallel to the normal vector of the plane.
* **Projections** - projections of the input vertices to the circle.
* **Diffs** - difference vectors, i.e. vectors pointing from original vertices
  to their projections to the circle.
* **Distances** - distances from the original vertices to the circle.

Examples of usage
-----------------

Fit a circle for vertices from arbitrary mesh object:

.. image:: https://user-images.githubusercontent.com/284644/74602398-daef8400-50c9-11ea-8670-657ffa8e1735.png

