Remove Excessive Knots (NURBS Curve)
====================================

Functionality
-------------

This node performs "knot removal" procedure for a NURBS curve, trying to remove
as many knots, and as many times, as it is possible, without changing the shape
of the curve too much. Allowed change of shape is controlled by "tolerance"
parameter.

This node can work only with NURBS and NURBS-like curves.

Inputs
------

This node has the following input:

* **Curve**. The curve to work on. This input is mandatory.

Parameters
----------

This node has the following parameter:

* **Tolerance**. This defines how much is it allowed to change the shape of the
  curve by knot removal procedure. The default value is ``10^-6``.

Outputs
-------

This node has the following output:

* **Curve**. The resulting curve.

