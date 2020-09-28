Solidify Face (Solid)
=====================

Dependencies
------------

This node requires FreeCAD_ library to work.

.. _FreeCAD: ../../solids.rst

Functionality
-------------

This node takes a Solid Face (i.e. a Surface trimmed by some edges), and makes
a Solid object from it, by offsetting the face along it's normals. In a way, it
is similar to what "Solidify" node does to mesh.

Solid Face object can be created with nodes from "Make Face" submenu (such as
"Face from Curve"); also any NURBS or NURBS-like surface can be used as a Solid
Face.

Inputs
------

This node has the following inputs:

* **SolidFace**. Solid Face object to be used for Solid generation. This input is mandatory.
* **Offset**. Offset value. The default value is 0.1.
* **Tolerance**. Calculation tolerance. The default value is 0.01.

Outputs
-------

This node has the following output:

* **Solid**. The generated Solid object.

Example of Usage
----------------

Make a Face from a closed NURBS curve, then offset it along normal to make a Solid object:

.. image:: https://user-images.githubusercontent.com/284644/92301754-b5e83300-ef7f-11ea-953d-9952f64d79bf.png

