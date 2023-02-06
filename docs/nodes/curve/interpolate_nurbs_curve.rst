Interpolate NURBS Curve
=======================

Dependencies
------------

This node can optionally use Geomdl_ or FreeCAD_ library to work.

.. _Geomdl: https://onurraufbingol.com/NURBS-Python/
.. _FreeCAD: https://www.freecad.org/

Functionality
-------------

This node builds a NURBS_ Curve object, which goes through all specified points.

The generated curve always will be a non-rational curve, which means
that all weights will be equal to 1.

Exact final curve degree can be specified for the built-in Sverchok and Geomdl_ implementations.

FreeCAD_ does not offer such parameter since the final curve will always be of degree 3 
(except we interpolate 2 or 3 points without specifying tangents).

FreeCAD_ implementation offers control with explicit knots and per point tangents.
The final curve can be set as open or smoothly closed.
Continuity of the spline defaults to C2. However, if Cyclic is enabled, or Tangents are supplied, the continuity will drop to C1.

.. _NURBS: https://en.wikipedia.org/wiki/Non-uniform_rational_B-spline

Inputs
------

This node has the following inputs:

* **Vertices**. The points through which the curve should go. This input is mandatory.
* **Degree**. Degree of the curve to be generated. Available only for Sverchok and Geomdl_ implementations. The default value is 3.
* **Knots**. The knot sequence. Available only for the FreeCAD_ implementation and if the "Explicit Knots" method is used.
  Must contain unique floats in an ascending order. When not connected, the curve will be
  calculated using Euclidean metric. If Cyclic is enabled one extra knot must be appended.
* **Tangents**. Custom tangents can be specified per point. Available only for the FreeCAD_ implementation. 
* **Tolerance**. Maximal distance of the built curve from the init Vertices. Available only for the FreeCAD_ implementation. Default value is 0.0.

Parameters
----------

This node has the following parameters:

* **Implementation**. Approximation algorithm implementation to be used. The available values are:

  * **Geomdl**. Use the implementation from Geomdl_ library. This is available only when Geomdl library is installed.
  * **Sverchok**. Use built-in Sverchok implementation.
  * **FreeCAD**. Use the implementation from FreeCAD_ library. This is available only when FreeCAD library is installed.
  
  In general (with large number of control points), FreeCAD implementation will be the fastest. The built-in implementation
  should be faster than Geomdl, but Geomdl implementation is better tested.
  
  By default, the first available implementation is used.

* **Centripetal**. This parameter is available only when **Implementation**
  parameter is set to **Geomdl**. This defines whether the node will use
  centripetal interpolation method. Unchecked by default.
  
* **Cyclic**. This parameter is available only when **Implementation**
  parameter is set to **Sverchok** or **FreeCAD**. If checked, then the node will generate
  cyclic (closed) curve. Unchecked by default.
  
* **Method**. Interpolation algorithm to be used. Available only for the FreeCAD_ implementation. The available values are:

  * **Parametrization**. Automatic knot sequence generation using certain metric.
  * **Explicit Knots**. Enables custom knot sequence input. The knots list can be also provided with the use of the `Generate Knotvector <https://nortikin.github.io/sverchok/docs/nodes/curve/generate_knotvector.html>`_ node based on the metrics from it. Note that for closed/cyclic curves the knot sequence needs one additional knot value. 
  
* **Metric**. This defines the metric used to calculate curve's T parameter values corresponding to specified curve points.
  Available only when **Implementation** parameter is set to **Sverchok** or **FreeCAD**. The available values are:

  * **Manhattan** metric is also known as Taxicab metric or rectilinear distance.
  * **Euclidean** also known as Chord-Length or Distance metric. The parameters of the points are proportionate to the distances between them.
  * **Points** also known as Uniform metric. The parameters of the points are distributed uniformly. Just the number of the points from the beginning.
  * **Chebyshev** metric is also known as Chessboard distance.
  * **Centripetal** The parameters of the points are proportionate to square roots of distances between them.
  * **X, Y, Z axis** Use distance along one of coordinate axis, ignore others.

  The default value is Euclidean.

Outputs
-------

This node has the following outputs:

* **Curve**. The generated NURBS curve object.
* **ControlPoints**. Control points of the generated curve.
* **Knots**. Knot vector of the generated curve.

Example of usage
----------------

.. image:: https://user-images.githubusercontent.com/284644/86528977-4a71de80-bec6-11ea-99bc-9ba8dab027dd.png

Example of the FreeCAD implementation generated cyclic curve with Euclidean parametrization:

.. image:: https://user-images.githubusercontent.com/66558924/216847760-b45134c9-f0df-431a-ba4b-2cf4a37e5a26.jpg

Example of the FreeCAD implementation generated cyclic curve with custom knots and per point tangents.:

.. image:: https://user-images.githubusercontent.com/66558924/217056287-5f073809-f246-4a6a-aa95-7fab809ae971.jpg

