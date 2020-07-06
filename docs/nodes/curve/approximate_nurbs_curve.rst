Approximate NURBS Curve
=======================

Dependencies
------------

This node requires Geomdl_ library to work.

.. _Geomdl: https://onurraufbingol.com/NURBS-Python/

Functionality
-------------

This node builds a NURBS_ Curve object, which approximates the given set of
points, i.e. goes as close to them as possible while remaining a smooth curve.

In fact, the generated curve always will be a non-rational curve, which means
that all weights will be equal to 1.

.. _NURBS: https://en.wikipedia.org/wiki/Non-uniform_rational_B-spline

Inputs
------

This node has the following inputs:

* **Vertices**. The points to be approximated. This input is mandatory.
* **Degree**. Degree of the curve to be built. Default value is 3. Most useful values are 3, 5 and 7.
* **PointsCnt**. Number of curve's control points. This input is available only
  when **Specify points count** parameter is checked. Default value is 5.

Parameters
----------

This node has the following parameters:

* **Centripetal**. This defines whether the node will use centripetal
  approximation method. Unchecked by default.
* **Specify points count**. If checked, then it will be possible to specify the
  number of curve's control points in **PointsCnt** input. Otherwise, the node
  will determine required number of control points by itself (this number can
  be too big for many applications).

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

