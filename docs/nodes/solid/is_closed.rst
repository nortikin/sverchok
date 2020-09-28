Is Solid Closed
===============

Dependencies
------------

This node requires FreeCAD_ library to work.

.. _FreeCAD: ../../solids.rst

Functionality
-------------

This node checks if the Solid object provided is closed. The body is called
closed if it does not have open edges. Most standard Sverchok nodes always
produce closed bodies, excluding "Solid from Faces" and, probably, scripted
nodes.

Inputs
------

This node has the following input:

* **Solid**. The Solid object to be analyzed. This input is mandatory.

Outputs
-------

This node has the following output:

* **IsClosed**. This output contains True for solids that are closed, and False
  for solids that are not.

