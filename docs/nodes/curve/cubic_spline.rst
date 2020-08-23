Cubic Spline
============

Functionality
-------------

This node generates a cubic spline interpolating curve, i.e. a 3rd degree curve
which goes through the specified vertices. The curve can be closed or not.

Curve domain / parameterization specifics: depends on **Metrics** parameter.
Curve domain will be equal to sum of distanes between the control points (in
the order they are provided) in the specified metric. For example, if
**Metric** is set to **Points**, then curve domain will be from 0 to number of
points.

Inputs
------

This node has the following input:

* **Vertices**. The points through which it is required to plot the curve. This input is mandatory.

Parameters
----------

This node has the following parameters:

* **Cyclic**. If checked, the node will generate a cyclic (closed) curve. Unchecked by default.
* **Metric**. This parameter is available in the N panel only. This defines the
  metric used to calculate curve's T parameter values corresponding to
  specified curve points. The available values are:

   * Manhattan
   * Euclidian
   * Points (just number of points from the beginning)
   * Chebyshev
   * Centripetal (square root of Euclidian distance).

The default value is Euclidian.

Outputs
-------

This node has the following output:

* **Curve**. The generated curve.

Examples of usage
-----------------

Smooth curve through some random points:

.. image:: https://user-images.githubusercontent.com/284644/77845087-6f6afd00-71c5-11ea-9062-77c195a512ce.png

The same with **Cyclic** checked:

.. image:: https://user-images.githubusercontent.com/284644/77845088-709c2a00-71c5-11ea-85a9-c090776c6c96.png

These examples had Metric set to Euclidian (default). Since **Eval Curve** node
generates evenly-distributed values of the T parameter, the number of points at
each segment is proportional to the distance between points. The next example
is with Metric set to Points:

.. image:: https://user-images.githubusercontent.com/284644/77845090-7134c080-71c5-11ea-8c6b-10d04a95cf87.png

In this case, number of points at each segment is the same.

