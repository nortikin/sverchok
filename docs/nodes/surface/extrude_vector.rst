Extrude Curve Along Vector
==========================

Functionality
-------------

This node generates a Surface by extruding a Curve (called "profile") along some vector.

Surface domain: along U direction - the same as of profile curve; along V
direction - from 0 to 1. V = 0 corresponds to the initial position of profile
curve.

Inputs
------

This node has the following inputs:

* **Profile**. The curve to be extruded. This input is mandatory.
* **Vector**. The vector along which the curve must be extruded. The default value is `(0, 0, 1)`.

Outputs
-------

This node has the following output:

* **Surface**. The generated surface.

Example of usage
----------------

Extrude some cubic spline along a vector:

.. image:: https://user-images.githubusercontent.com/284644/79358827-2ce24800-7f5b-11ea-91ec-a5df4762e610.png

