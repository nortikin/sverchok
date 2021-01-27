Revolve Face (Solid)
====================

Functionality
-------------

This node takes a Solid Face object (i.e. a Surface trimmed by some edges), and
makes a Solid object of revolution from it, by rotating it around the specified
axis. The axis is specified by providing a point on it and a directing vector.

Solid Face object can be created with nodes from "Make Face" submenu (such as
"Face from Curve"); also any NURBS or NURBS-like surface can be used as a Solid
Face.

Inputs
------

This node has the following inputs:

* **SolidFace**. Solid Face object to be used for Solid generation (a section
  of the body of revolution). This input is mandatory.
* **Point**. A point lying on the rotation axis. The default value is ``(0, 0,
  0)`` (global origin).
* **Direction**. Directing vector of the rotation axis. The default value is
  ``(0, 0, 1)`` (Z axis).
* **Angle**. Rotation angle, in degrees. The default value is 360 (full circle).

Outputs
-------

This node has the following output:

* **Solid**. The generated Solid object.

Example of Usage
----------------

.. image:: https://user-images.githubusercontent.com/284644/92300247-dc53a180-ef72-11ea-9abf-1bc3f5e3b662.png

