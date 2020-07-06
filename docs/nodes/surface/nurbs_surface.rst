NURBS surface
=============

.. image:: /docs/assets/nodes/surface/node_build_nurbs_surface.png

Functionality
-------------

This node generates a nurbs surface.

https://en.wikipedia.org/wiki/Non-uniform_rational_B-spline

Inputs
------

This node has the following input:

* **Control Ploints**. The control points determine the shape of the curve.
  Typically, each point of the curve is computed by taking a weighted sum of a number of control points.

* **Weights**. TODO
* **Degree U**. TODO
* **Degree V**. TODO
* **U Size**. TODO


Parameters
----------

This node has the following parameters:

* **Surface modes**. Values: NURBS, BSpline
* **Knot modes**. Values: Autro, Explicit
* **Normalize knots**. Values: Normalize knots
* **Is cyclic U**. Values: True, False
* **Is cyclic V**. Values: True, False
* **Make grid**. Values: Tessellate


Outputs
-------

This node has the following output:

* **Surface**. The generated surface.

Examples of usage
-----------------


.. image:: /docs/assets/nodes/surface/nurbs_surface_01.png

These example use a plan as control points
