Deconstruct Curve
=================

Functionality
-------------

This node deconstructs any NURBS or NURBS-like curve into it's main components:
control points, weights and so on.

At the moment, this node can effectively work with the following types of curves:

* NURBS curves
* Bezier curves
* Cubic splines
* Polylines
* Circular arcs
* Line segments

Some nodes, that output complex curves composed from simple curves (for
example, "Rounded rectangle"), have **NURBS output** parameter; when it is
checked, such nodes output NURBS curves, so "Deconstruct curve" can work with
them.

Other types of curves are considered as not having NURBS components (control
points, for example), so outputs will be empty.

Inputs
------

This node has the following input:

* **Curve**. The curve to be decomposed. This input is mandatory.

Outputs
-------

This node has the following outputs:

* **Degree**. Curve degree. If the curve is not NURBS-like, this output will
  contain ``None``.
* **KnotVector**. Curve knot vector. If the curve is not NURBS-like, this
  output will contain an empty list.
* **ControlPoints**. Curve control points. If the curve is not NURBS-like, this
  output will contain an empty list.
* **Edges**. Edges that connect curve's control points. Together with
  **ControlPoints** output this form so-called "control polygon" of the curve.
  If the curve is not NURBS-like, this output will contain an empty list.
* **Weights**. Weights of curve's control points. If the curve is not
  NURBS-like, this output will contain an empty list.

Examples of usage
-----------------

NURBS components of interpolating cubic spline:

.. image:: https://user-images.githubusercontent.com/284644/90808602-b8b91600-e339-11ea-9a1c-ff7b15009c00.png

Circular arc can also be represented as a NURBS curve:

.. image:: https://user-images.githubusercontent.com/284644/90808604-b9ea4300-e339-11ea-93fa-57d944b3b036.png

