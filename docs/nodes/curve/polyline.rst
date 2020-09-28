Polyline
========

Functionality
-------------

This node geneates a polyline (polygonal chain), i.e. a curve consisting of
segments of straight lines between the specified points. The polyline may be
closed or not.

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
* **Concatenate**. If checked, the node will generate one Curve object that
  passes through all provided vertices. Otherwise, the node will generate a
  separate Curve object for each edge. Checked by default.
* **Metric**. This parameter is available in the N panel only. This defines the
  metric used to calculate curve's T parameter values corresponding to
  specified curve points. The available values are:

   * Manhattan
   * Euclidian
   * Points (just number of points from the beginning)
   * Chebyshev.

The default value is Euclidian.

Outputs
-------

This node has the following output:

* **Curve**. The generated curve.

Examples of usage
-----------------

Polyline through some random points:

.. image:: https://user-images.githubusercontent.com/284644/77845220-8bbb6980-71c6-11ea-96f2-5e25bd8c36f1.png

The same with **Cyclic** checked:

.. image:: https://user-images.githubusercontent.com/284644/77845221-8cec9680-71c6-11ea-8f5a-1558b32a2e8b.png

These examples had Metric set to Euclidian (default). Since **Eval Curve** node
generates evenly-distributed values of the T parameter, the number of points at
each segment is proportional to the distance between points. The next example
is with Metric set to Points:

.. image:: https://user-images.githubusercontent.com/284644/77845222-8d852d00-71c6-11ea-986c-0d7bbde0814d.png

In this case, number of points at each segment is the same.

