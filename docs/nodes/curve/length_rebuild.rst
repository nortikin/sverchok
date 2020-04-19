Naturally Parametrized Curve
============================

Functionality
-------------

It worth reminding that a Curve object is defined as a function from some set
of T values into some points in 3D space; and, since the function is more or
less arbitrary, the change of T parameter is not always proportional to length
of the path along the curve - in fact, it is rarely proportional. For many
curves, small changes of T parameter can move a point a long way along the
curve in one parts of the curve, and very small way in other parts.

This node takes a Curve object and generates another Curve, which has the same
set of points, but another parametrization - specifically, the natural
parametrization. "Natural parametrization" means that the length of part of
curve from the beginning to some point is equal to the value of curve's T
parameter at that point. This means that with equal changes of curve's T
parameter the point on the curve will always travel the equal distances.

This node is similar to "Curve Length Parameter"; the difference is, this node
outputs the Curve object, so that curve can be used in following nodes that
require a Curve as input.

The curve's length is calculated numerically, by subdividing the curve in many
straight segments and summing their lengths. The more segments you subdivide
the curve in, the more precise the length will be, but the more time it will
take to calculate. So the node gives you control on the number of subdivisions.

Inputs
------

This node has the following inputs:

* **Curve**. The curve to be re-parametrized. This input is mandatory.
* **Resolution**. The number of segments to subdivide the curve in to calculate
  the length. The bigger the value, the more precise the calculation will be,
  but the more time it will take. The default value is 50.

Parameters
----------

This node has the following parameter:

* **Interpolation mode**. This defines the interpolation method used for
  calculating of points inside the segments in which the curve is split
  according to **Resolution** parameters. The available values are **Cubic**
  and **Linear**. Cubic methods gives more precision, but takes more time for
  calculations. The default value is **Cubic**. This parameter is available in
  the N panel only.

Outputs
-------

This node has the following output:

* **Curve**. The newly generated curve.

Examples of usage
-----------------

Take an Archimedian spiral with a well-known parametrization; in the center,
small changes of T give very small change of the position of the point on the
curve, while farther from the center, the same changes of T give a lot bigger
steps along the curve. This you can see at the left. At the right there is the
same spiral with natural parametrization:

.. image:: https://user-images.githubusercontent.com/284644/79695949-29202f80-8293-11ea-8623-1df67c3a68ef.png

Similar example with some cubic spline:

.. image:: https://user-images.githubusercontent.com/284644/79693501-75b03e80-8284-11ea-841b-9b5911bf91e7.png

