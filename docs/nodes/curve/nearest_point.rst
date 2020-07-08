Nearest Point on Curve
======================

Dependencies
------------

This node requires SciPy_ library to work.

.. _SciPy: https://scipy.org/

Functionality
-------------

This node searches for the point on the curve, which is the nearest (the
closest) to the given point.

Note that the search is implemented with a numeric algorithm, so it may be not
very fast. In case you know how to solve this task analytically (with formula)
for your particular curve, that will be much faster. This node, on the other
hand, is usable in cases when you do not know formulas for your curve - for
example, it was received by some approximation.

At the first step of it's algorithm, this node generates several sample points
on the curve with even intervals of T parameter. The nearest of them is
selected. This point are then used as initial guess points for the more precise
algorithm. 

In case there are several points on the curve with equal distance to the
original point, the node will return one of them (it is not guaranteed which
one).

Inputs
------

This node has the following inputs:

* **Curve**. The curve to search the point on. This input is mandatory.
* **Point**. The point to search the neares for. The default value is global origin ``(0, 0, 0)``.

Parameters
----------

This node has the following parameters:

* **Init Resolution**. Initial number of segments to subdivide curve in, for
  the first step of algorithm. The higher values will lead to more precise
  initial guess, so the precise algorithm will be faster; but that can require
  more evaluations at the first stage. The default value is 50. In many cases,
  you do not have to change this value.
* **Precise**. If not checked, then the precise calculation step will not be
  executed, and the node will just output the nearest point out of points
  generated at the first step - so it will be "roughly nearest point". So, if
  this parameter is not checked, higher values of **Init resolution** parameter
  will lead to more precise output. Checked by default.

Outputs
-------

This node has the following outputs:

* **Point**. The nearest point in 3D space.
* **T**. The value of curve's T parameter corresponding to the nearest point.

