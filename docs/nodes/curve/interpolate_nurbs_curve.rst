Interpolate NURBS Curve
=======================

Dependencies
------------

This node requires Geomdl_ library to work.

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

This node has the following parameter:

* **Centripetal**. This defines whether the node will use centripetal interpolation method. Unchecked by default.

Outputs
-------

This node has the following outputs:

* **Curve**. The generated NURBS curve object.
* **ControlPoints**. Control points of the generated curve.
* **Knots**. Knot vector of the generated curve.

Example of usage
----------------

.. image:: https://user-images.githubusercontent.com/284644/86528977-4a71de80-bec6-11ea-99bc-9ba8dab027dd.png

