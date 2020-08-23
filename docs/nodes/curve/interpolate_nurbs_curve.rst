Interpolate NURBS Curve
=======================

Dependencies
------------

This node can optionally use Geomdl_ library.

.. _Geomdl: https://onurraufbingol.com/NURBS-Python/

Functionality
-------------

This node builds a NURBS_ Curve object, which goes through all specified points.

In fact, the generated curve always will be a non-rational curve, which means
that all weights will be equal to 1.

.. _NURBS: https://en.wikipedia.org/wiki/Non-uniform_rational_B-spline

Inputs
------

This node has the following inputs:

* **Vertices**. The points through which the curve should go. This input is mandatory.
* **Degree**. Degree of the curve to be generated. The default value is 3.

Parameters
----------

This node has the following parameters:

* **Implementation**. This parameter is available only if **Interpolation
  mode** parameter is set to **BSpline**. This defines the implementation of
  NURBS mathematics to be used. The available options are:

  * **Geomdl**. Use Geomdl_ library. This option is available only when Geomdl
    package is installed.
  * **Sverchok**. Use built-in Sverchok implementation.
  
  In general (with large nuber of control points), built-in implementation
  should be faster; but Geomdl implementation is better tested.
  The default option is **Geomdl**, when it is available; otherwise, built-in
  implementation is used.

* **Centripetal**. This parameter is available only when **Implementation**
  parameter is set to **Geomdl**. This defines whether the node will use
  centripetal interpolation method. Unchecked by default.
* **Metric**. This parameter is available only when **Implementation**
  parameter is set to **Sverchok**. This defines the metric used to calculate
  curve's T parameter values corresponding to specified curve points. The
  available values are:

   * Manhattan
   * Euclidian
   * Points (just number of points from the beginning)
   * Chebyshev
   * Centripetal (square root of Euclidian distance).

The default value is Euclidian.

Outputs
-------

This node has the following outputs:

* **Curve**. The generated NURBS curve object.
* **ControlPoints**. Control points of the generated curve.
* **Knots**. Knot vector of the generated curve.

Example of usage
----------------

.. image:: https://user-images.githubusercontent.com/284644/86528977-4a71de80-bec6-11ea-99bc-9ba8dab027dd.png

