Monotone Spline
===============

Dependencies
------------

This node requires SciPy library to function.

Functionality
-------------

A monotone spline is a smooth curve, which interpolates input set of X and Y
values, with additional property: interpolated values of Y are strictly
increasing when X is increasing.

As a consequence, Y values of whole curve lie within the span between the first
and last values of Y provided.

One of possible applications of monotone splines is reparametrization of
curves. In original curve, you have some dependency of the point on the curve
from curve T parameter; when T is increasing, the point on the curve goes in
one direction along the curve. When you do reparametrization, you change this
dependency in such a way that the speed at which the point travels along the
curve when T is changing, becomes different from original curve. But you still
want the point to travel always in one direction.

This node takes two sets of numbers, for X (independent variable) and Y
(dependent variable). Both sets are sorted. The node builds a monotone spline,
which is a curve third degree. First derivative is continuous, but the second
derivative can have discontinuities. This curve is "NURBS-like", i.e. can be
automatically converted to NURBS by nodes which work with NURBS curves.

Curve parametrization: according to provided set of X values.

Inputs
------

This node has the following inputs:

* **X**. Set of independent variable values. This input is mandatory.
* **Y**. Set of dependent variable values. This input is mandatory.

The inputs are automatically renamed according to selected value of the **Plane** parameter.

Parameters
----------

This node has the following parameter:

* **Plane**. The coordinate plane in which the spline will be drawn. The available options are:

  * **XY**. It is assumed that Y depends on X.
  * **XZ**. It is assumed that Z depends on X.
  * **YZ**. It is assumed that Z depends on Y.

  The default option is **XY**.

Outputs
-------

This node has the following output:

* **Curve**. The generated monotone spline curve.

Examples of Usage
-----------------

In the following example, green line is a cubic spline, and you can see that
for these points the cubic spline is decreasing in the beginning and in the end
of curve; and it also goes outside of the range between first and last Y
values.

.. image:: https://github.com/user-attachments/assets/7c1afb23-e24c-4498-a676-e47e50b9137c
  :target: https://github.com/user-attachments/assets/7c1afb23-e24c-4498-a676-e47e50b9137c

