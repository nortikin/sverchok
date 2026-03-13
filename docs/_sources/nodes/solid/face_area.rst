Solid Face Area
===============

Dependencies
------------

This node requires FreeCAD_ library to work.

.. _FreeCAD: ../../solids.rst

Functionality
-------------

This node calculates the area of a given Solid Face object (i.e. a Surface trimmed by some edges).

Solid Face object can be created with nodes from "Make Face" submenu (such as
"Face from Curve"); also any NURBS or NURBS-like surface can be used as a Solid
Face.

Inputs
------

This node has the following input:

* **SolidFace**. Solid Face object, for which it is required to calculate the area. This input is mandatory.

Outputs
-------

This node has the following output:

* **Area**. The area of the input Solid Face object.

