Approximate NURBS Curve
=======================

Dependencies
------------

This node requires either Geomdl_ or SciPy_ library to work.

.. _Geomdl: https://onurraufbingol.com/NURBS-Python/
.. _SciPy: https://scipy.org/

Functionality
-------------

This node builds a NURBS_ Curve object, which approximates the given set of
points, i.e. goes as close to them as possible while remaining a smooth curve.

In fact, the generated curve always will be a non-rational curve, which means
that all weights will be equal to 1.

This node supports two implementations of curve approximation algorithm.
Different implementation give you different ways of controlling them:

* Geomdl_ implementation can either define the number of control points of
  generated curve automatically, or you can provide it with desired number of
  control points. This implementation supports only two metrics - euclidean and
  centripetal. This implementation can not generate cyclic (closed) curves.
* SciPy_ implementation allows you to define "smoothing" parameter, to define
  how smooth you want the curve to be. By default, it selects the smoothing
  factor automatically. If you explicitly set the smoothing factor to zero, the
  curve will go exactly through all provided points, i.e. the node will perform
  interpolation instead of approximation. This implementation supports wider
  selection of metrics. This implementation can make cyclic (closed) curves.
  Additionally, when smoothing factor is not zero, you can provide different
  weights for different points.

.. _NURBS: https://en.wikipedia.org/wiki/Non-uniform_rational_B-spline

Inputs
------

This node has the following inputs:

* **Vertices**. The points to be approximated. This input is mandatory.
* **Weights**. This input is available only when **Implementation** parameter
  is set to **SciPy**. Weights of points to be approximated. Bigger values of
  weight mean that the curve will pass through corresponding point at the
  smaller distance. This does not have sense if **Smoothing** input is set to
  zero. Optional input. If not connected, the node will consider weights of all
  points as equal.
* **Degree**. Degree of the curve to be built. Default value is 3. Most useful values are 3, 5 and 7.
* **PointsCnt**. Number of curve's control points. This input is available only
  when **Implementation** parameter is set to **Geomdl**, and **Specify points
  count** parameter is checked. Default value is 5.
* **Smoothing**. This input is available only when **Implementation** parameter
  is set to **SciPy**, and **Scpecify smoothing** parameter is checked.
  Smoothing factor. Bigger values will make more smooth curves. Value of 0
  (zero) mean that the curve will exactly pass through all points. The default
  value is 0.1.

Parameters
----------

This node has the following parameters:

* **Implementation**. Approximation algorithm implementation to be used. The available values are:

  * **Geomdl**. Use the implementation from Geomdl_ library. This is available only when Geomdl library is installed.
  * **SciPy**. Use the implementation from SciPy_ library. This is available only when SciPy library is installed.

  By default, the first available implementation is used.

* **Centripetal**. This parameter is available only when **Implementation**
  parameter is set to **Geomdl**. This defines whether the node will use
  centripetal metric. If not checked, the node will use euclidean metric.
  Unchecked by default.
* **Specify points count**. This parameter is available only when
  **Implementation** parameter is set to **Geomdl**. If checked, then it will
  be possible to specify the number of curve's control points in **PointsCnt**
  input. Otherwise, the node will determine required number of control points
  by itself (this number can be too big for many applications).
* **Cyclic**. This parameter is available only when **Implementation**
  parameter is set to **SciPy**. Defines whether the generated curve will be
  cyclic (closed). Unchecked by default.
* **Auto**. This parameter is available only when **Implementation** parameter
  is set to **SciPy**, and **Cyclic** parameter is enabled. If checked, the
  node will automatically decide if the curve should be cyclic (closed), based
  on the distance between the first and last points being approximated: if the
  points are close enough, the curve will be closed. If not checked, the curve
  will be closed regardless of distance between points, just because **Cyclic**
  parameter is checked. Unchecked by default.
* **Cyclic threshold**. This parameter is available only when
  **Implementation** parameter is set to **SciPy**, **Cyclic** parameter is
  enabled, and **Auto** parameter is enabled as well. This defines maximum
  distance between the first and the last points being approximated, for which
  the node will make the curve cyclic. Default value is 0.0, i.e. the points
  must exactly coincide in order for curve to be closed.
* **Metric**. This parameter is available only when **Implementation**
  parameter is set to **SciPy**.Metric to be used for interpolation. The
  available values are:

   * Manhattan
   * Euclidean
   * Points (just number of points from the beginning)
   * Chebyshev
   * Centripetal (square root of Euclidean distance)
   * X, Y, Z axis - use distance along one of coordinate axis, ignore others.

   The default value is Euclidean.

* **Specify smoothing**. This parameter is available only when
  **Implementation** parameter is set to **SciPy**. If checked, the node will
  allow you to specify smoothing factor via **Smoothing** input. If not
  checked, the node will select the smoothing factor automatically. Unchecked
  by default.

Outputs
-------

This node has the following outputs:

* **Curve**. The generated NURBS curve object.
* **ControlPoints**. Control points of the generated curve.
* **Knots**. Knot vector of the generated curve.

Example of usage
----------------

Take points from Greasepencil drawing and approximate them with a smooth curve:

.. image:: https://user-images.githubusercontent.com/284644/74363000-7becef00-4deb-11ea-9963-e864dc3a3599.png

Use SciPy implementation to make a closed curve:

.. image:: https://user-images.githubusercontent.com/284644/101246890-d61ebe00-3737-11eb-942d-c31e02bf3c3d.png

