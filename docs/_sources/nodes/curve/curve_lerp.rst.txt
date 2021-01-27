Curve Lerp
==========

Functionality
-------------

This node generates a linear interpolation ("lerp") between two curves. More
precisely, it generates a curve, each point of which is calculated by linear
interpolation of two corresponding points on two other curves.

If the coefficient value provided is outside `[0 .. 1]` range, then the node
will calculate linear extrapolation instead of interpolation.

Inputs
------

This node has the following inputs:

* **Curve1**. The first curve. This input is mandatory.
* **Curve2**. The second curve. This input is mandatory.
* **Coefficient**. The interpolation coefficient. When it equals to 0, the
  resulting curve will be the same as **Curve1**. When the coefficient is 1.0,
  the resulting curve will be the same as **Curve2**. The default value is 0.5,
  which is something in the middle.

Outputs
-------

This node has the following output:

* **Curve**. The interpolated curve.

Example of usage
----------------

Several curves calculated as linear interpolation between half a circle and a straight line segment:

.. image:: https://user-images.githubusercontent.com/284644/78507545-fdcd1900-7799-11ea-98d4-17bf8109396a.png

