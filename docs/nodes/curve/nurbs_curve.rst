Build NURBS Curve
=================

Dependencies
------------

This node requires Geomdl_ library to work.

.. _Geomdl: https://onurraufbingol.com/NURBS-Python/

Functionality
-------------

This node generates a NURBS_ Curve object, given all it's details: control points, weights and knot vector.

.. _NURBS: https://en.wikipedia.org/wiki/Non-uniform_rational_B-spline

Inputs
------

This node has the following inputs:

* **ControlPoints**. NURBS curve control points. This input is mandatory.
* **Weights**. NURBS curve control point weights. If this input is not linked,
  it will be assumed that all control points have weight of 1. This input is
  not available when **Curve mode** parameter is set to **BSpline**.
* **Knots**. NURBS curve knot vector. This input is not available if
  **Knots** parameter is set to **Auto**.
* **Degree**. NURBS curve degree. The default value is 3.

Parameters
----------

This node has the following parameters:

* **Curve mode**. This defines the type of curve to be built:

  * NURBS: rational B-Spline curve (with ability to have different weights of control points)
  * BSpline: non-rational B-Spline curve (all control points have equal weight)

  The default option is NURBS.

* **Knots**. This defines how the knot vector is specified:

  * **Auto**: Knot vector is generated automatically (the curve will be clamped and periodic).
  * **Explicit**: Knot vector is explicitly defined in the **Knots** input of the node.
   
  The default option is Auto.

* **Normalize knots**. If checked, all knotvector values will be rescaled to
  ``[0 .. 1]`` range; so, the curve domain will always be from 0 to 1. If not
  checked, the curve domain will be defined by knotvector.
* **Cyclic**. Whether the curve should be cyclic (closed). This option is
  available only when the **Knots** parameter is set to **Auto**. Unchecked by
  default.

Outputs
-------

This node has the following outputs:

* **Curve**. The generated NURBS curve object.
* **Knots**. NURBS curve knotvector.

Example of usage
----------------

.. image:: https://user-images.githubusercontent.com/284644/86948496-a6f32900-c166-11ea-850f-5977d5a0fea8.png

