Polygon Face (Solid)
====================

Dependencies
------------

This node requires FreeCAD_ library to work.

.. _FreeCAD: ../../solids.rst

Functionality
-------------

This node generates a Solid Face object, i.e. a Surface trimmed with an edge,
from a polygon, i.e. set of vertices and edges.

**NOTE**: The polygon provided must be planar (flat), i.e. all vertices must
lie in the same plane. Otherwise, the node will fail (become red).

Solid Face object can be later used for construction of Solids (by extrusion, for example).

Inputs
------

This node has the following inputs:

* **Vertices**. Polygon vertices. This input is mandatory.
* **Faces**. Polygon faces. This input is mandatory.

Outputs
-------

* **SolidFaces**. Generated Solid Face objects.

Example of usage
----------------

Build a face from pentagon, and then make a solid of revolution from it:

.. image:: https://user-images.githubusercontent.com/284644/92300247-dc53a180-ef72-11ea-9abf-1bc3f5e3b662.png

