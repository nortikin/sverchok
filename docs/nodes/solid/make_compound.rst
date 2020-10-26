Compound Solid
==============

Dependencies
------------

This node requires FreeCAD_ library to work.

.. _FreeCAD: ../../solids.rst

Functionality
-------------

This node combines several Solid, Curve and/or Surface object into one object
called Compound. Some nodes that work with Solids can work with Compounds as
well, but not all. Some nodes will behave strangely if you pass them with a
Compound instead of a Solid.

All Curve and Surface objects that are passed to this node must be NURBS-like.

This node, for example, can be used to export several Solid objects into one
BREP/STEP/IGES file.

Inputs
------

This node has the following inputs:

* **Solids**. Solid objects to be combined into Compound.
* **Curves**. Curve objects to be combined into Compound.
* **Surfaces**. Surface objects to be combined into Compound.

At least one of inputs must be linked in order for this node to work.

Outputs
-------

This node has the following output:

* **Compound**. Generated Compound object.

