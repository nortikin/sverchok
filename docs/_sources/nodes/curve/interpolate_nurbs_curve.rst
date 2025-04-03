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

Exact final curve degree can be specified for the built-in Sverchok and Geomdl implementations.

FreeCAD does not offer such parameter since the final curve will always be of degree 3 
(except we interpolate 2 or 3 points without specifying tangents).

FreeCAD implementation offers control with explicit knots and per point tangents.
The final curve can be set as open or smoothly closed.
Continuity of the spline defaults to C2. However, if Cyclic is enabled, or Tangents are supplied, the continuity will drop to C1.

.. _NURBS: https://en.wikipedia.org/wiki/Non-uniform_rational_B-spline

Inputs
------

This node has the following inputs:

* **Vertices**. The points through which the curve should go. This input is mandatory.
* **Degree**. Degree of the curve to be generated. Available only for Sverchok and Geomdl implementations. The default value is 3.
* **Knots**. The knot sequence. Available only for the FreeCAD implementation and if the "Explicit Knots" method is used.
  Must contain unique floats in an ascending order. When not connected, the curve will be
  calculated using "Euclidean" metric. If "Cyclic" is enabled one extra knot must be appended.
* **Tangents**. Custom tangents can be specified per point. Available only for the FreeCAD implementation if "Tangent Constrains" is enabled and "Mode" is set to "All Tangents".
* **TangentsMask**. List of booleans to activate or deactivate the corresponding tangent constraints. Available only for the FreeCAD implementation if "Tangent Constrains" is enabled and "Mode" is set to "All Tangents".
* **InitialTangent**. Set the tangent at the beginning of the curve. Available only for the FreeCAD implementation if "Tangent Constrains" is enabled and "Mode" is set to "Endpoint Tangents".
* **FinalTangent**. Set the tangent at the end of the curve. Available only for the FreeCAD implementation if "Tangent Constrains" is enabled and "Mode" is set to "Endpoint Tangents".
* **Tolerance**. Maximal distance of the built curve from the init "Vertices". Available only for the FreeCAD implementation. Default value is 0.0.

Parameters
----------

This node has the following parameters:

* **Implementation**. Approximation algorithm implementation to be used. The available values are:

  * **Geomdl**. Use the implementation from Geomdl library. This is available only when Geomdl library is installed.
  * **Sverchok**. Use built-in Sverchok implementation.
  * **FreeCAD**. Use the implementation from FreeCAD library. This is available only when FreeCAD library is installed.
  
  In general (with large number of control points), FreeCAD implementation will be the fastest. The built-in implementation
  should be faster than Geomdl, but Geomdl implementation is better tested.
  
  By default, the first available implementation is used.

* **Centripetal**. This parameter is available only when "Implementation"
  parameter is set to "Geomdl". This defines whether the node will use
  centripetal interpolation method. Unchecked by default.
  
* **Cyclic**. This parameter is available only when "Implementation"
  parameter is set to "Sverchok" or "FreeCAD". If checked, then the node will generate
  cyclic (closed) curve. Unchecked by default.
  
* **Method**. Interpolation algorithm to be used for calculating the knots. Available only for the FreeCAD implementation. The available values are:

  * **Parametrization**. Automatic knot sequence generation using certain metric.
  * **Explicit Knots**. Enables custom knot sequence input. The knots list can be also provided with the use of the `Generate Knotvector <https://nortikin.github.io/sverchok/docs/nodes/curve/generate_knotvector.html>`_ node based on the metrics from it. Note that for closed/cyclic curves the knot sequence needs one additional knot value. 
  
* **Metric**. This defines the metric used to calculate curve's T parameter values corresponding to specified curve points.
  Available only when "Implementation" parameter is set to "Sverchok" or "FreeCAD". The available values are:

  * **Manhattan** metric is also known as Taxicab metric or rectilinear distance.
  * **Euclidean** also known as Chord-Length or Distance metric. The parameters of the points are proportionate to the distances between them.
  * **Points** also known as Uniform metric. The parameters of the points are distributed uniformly. Just the number of the points from the beginning.
  * **Chebyshev** metric is also known as Chessboard distance.
  * **Centripetal** The parameters of the points are proportionate to square roots of distances between them.
  * **X, Y, Z axis** Use distance along one of coordinate axis, ignore others.

  The default value is Euclidean.

* **Tangent Constraints**. This enables specifying tangent vectors at the interpolation points.
  Available only when "Implementation" parameter is set to "FreeCAD".

* **Mode**. Constraints mode to be used. Available only when "Implementation" parameter is set to "FreeCAD" and if "Tangent Constraints" is enabled.
  The available values are:

  * **Endpoint Tangents**. Set the tangents at the beginning and the end of the curve.
  * **All Tangents**. Set list of tangent vectors for every single interpolation point.

* **Autoscale Tangents**. Set an automatic scale of all active tangents. Available only when "Implementation" parameter is set to "FreeCAD" and if "Tangent Constraints" is enabled.

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

.. image:: https://user-images.githubusercontent.com/66558924/218280327-2f215c33-7d8f-401a-bc20-ea60d1213f3a.jpg

Example of the FreeCAD implementation generated open curve with constrained start and end tangents.:

.. image:: https://user-images.githubusercontent.com/66558924/218280333-e12de8c8-0abe-4fbd-b66b-1e7d7ca7d2c9.jpg

Example of the FreeCAD implementation generated cyclic curve using full tangent constraints and custom knots.:

.. image:: https://user-images.githubusercontent.com/66558924/218280648-ca635cbf-8d81-4acc-8dd7-e09a4e3ab364.jpg


