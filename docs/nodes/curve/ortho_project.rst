Ortho Project on Curve
======================

Dependencies
------------

This node requires SciPy_ library to work.

.. _SciPy: https://scipy.org/

Functionality
-------------

This node finds an orthogonal projection of a point onto a curve, i.e. a point
on a curve, such that the vector connecting the provided point and the point on
curve is perpendicular to the curve.

If there are several such points on a curve, the node will return the nearest
of them. If there are several nearest points, the node will return any of them
(not guaranteed which one).

The node uses a numerical method to find such point, so it may be not very
fast. If you happen to know how to find such point for your specific curve by
formulas, that way will be faster and more precise.

Inputs
------

This node has the following inputs:

* **Curve**. The curve to find an orthogonal projection at. This input is mandatory.
* **Point**. The point to find an orthogonal projection for. The default value is ``(0, 0, 0)``.

Parameters
----------

This node has the following parameter:

* **Init resolution**. This parameter is available only in the N panel. At the
  first stage of the algorithm, the node subdivides the curve in N segments,
  and then searches for orthogonal projection at each of them by a numerical
  method. The more segments you take, the less work will be for numerical
  method, by the more time will it spend at this first step.  The default value
  is 5. In most simple cases, you do not have to change this value.

Outputs
-------

This node has the following outputs:

* **Point**. The point on a curve in 3D space.
* **T**. The value of curve's T parameter corresponding to that point.

Example of usage
----------------

Take points on a straight line and project them to some curve:

.. image:: https://user-images.githubusercontent.com/284644/87218335-1fc2d280-c36b-11ea-979b-9858a0dd2f10.png

