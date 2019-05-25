Linear Approximation
====================

Functionality
-------------

This node tries to approximate provided set of vertices by either a plane or
a straight line. In other words, it searches for such a plane / line, that all
provided vertices have the minimum distance to it.

More technically, it searches for a plane or a line A, such that

.. image:: https://user-images.githubusercontent.com/284644/58372582-e6e25700-7f38-11e9-844f-aaa4fa2bb562.gif

The plane is represented by a point on the plane and a normal vector.

The line is represented by a point on the line and a direction vector.

That point on line or plane is calculated as a geometrical center of all
provided vertices.

Inputs
------

This node has one input: **Vertices** - the vertices to be approximated.

Parameters
----------

This node has one parameter - **Mode**. Two modes are supported:

* **Line** - approximate vertices by straight line. This is the default mode.
* **Plane** - approximate vertices by a plane.

Outputs
-------

This node has the following outputs:

* **Center** - the point on the line or plane. This is geometrical center of all input vertices.
* **Normal** - the normal vector of a plane. This output is only available in the **Plane** mode.
* **Direction** - the direction vector of a line. This output is only available in the **Line** mode.
* **Projections** - the projections of input vertices to the line or plane.
* **Diffs** - difference vectors between the input vertices and their projections to line or plane.
* **Distances** - distances between the input vertices and their projections to line or plane.

Examples of usage
-----------------

The simplest example: approximate 3D curve by a line. Here black curve is a
grease pencil, green one - it's representation in Sverchok, red line - result
of linear approximation of green line.

.. image:: https://user-images.githubusercontent.com/284644/58330560-8e378f00-7e50-11e9-9bf5-8612c420ed91.png

A simple example with plane.

.. image:: https://user-images.githubusercontent.com/284644/58274029-63472f80-7dab-11e9-9c8b-1953633cf2be.png

The node can calculate approximation for several sets of vertices at once:

.. image:: https://user-images.githubusercontent.com/284644/58273750-cd130980-7daa-11e9-8f99-3ec57b37965c.png


You can also find more examples and some discussion `in the development thread <https://github.com/nortikin/sverchok/pull/2421>`_.

