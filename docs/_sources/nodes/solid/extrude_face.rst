Extrude Face (Solid)
====================

Functionality
-------------

This node takes a Solid Face object (i.e. a Surface trimmed by some edges), and
makes a Solid object from it, by extruding the face along a vector.

Solid Face object can be created with nodes from "Make Face" submenu (such as
"Face from Curve"); also any NURBS or NURBS-like surface can be used as a Solid
Face.

Inputs
------

This node has the following inputs:

* **SolidFace**. Solid Face object to be extruded. This input is mandatory.
* **Vector**. The extrusion vector. The default value is ``(0, 0, 1)``.

Outputs
-------

This node has the following output:

* **Solid**. The generated Solid object.

Example of Usage
----------------

Make a Face from a closed NURBS curve, then extrude it along a vector to make a Solid object:

.. image:: https://user-images.githubusercontent.com/284644/92301217-1cb71d80-ef7b-11ea-9fae-69f021da7fc2.png

