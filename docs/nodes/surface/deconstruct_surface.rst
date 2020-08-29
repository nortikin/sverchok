Deconstruct Surface
===================

Functionality
-------------

This node deconstructs any NURBS or NURBS-like surface into it's main
components: control points, weights, and so on.

For types of surfaces that are considered as not having NURBS components (control
points, for example), outputs will be empty.

Inputs
------

This node has the following input:

* **Surface**. The surface to be decomposed. This input is mandatory.

Parameters
----------

This node has the following parameter:

* **Split by row**. If checked, then data in **ControlPoints** and **Weights**
  output will be grouped by row of control points: for example, ControlPoints
  will contain one list of points for each row of control points of the
  surface. Otherwise, these outputs will contain one joined lists of control
  points and weights, correspondingly. Unchecked by default.

Outputs
-------

This node has the following outputs:

* **DegreeU**, **DegreeV**. Surface degree along U and V parameter,
  correspondingly. If the surface is not NURBS-like, these outputs will contain
  ``None``.
* **KnotVectorU**, **KnotVectorV**. Surface knot vectors along U and V
  parameters, correspondingly. If the surface is not NURBS-like, these outputs
  will contain an empty list.
* **ControlPoints**. Surface control points. If the surface is not NURBS-like,
  this output will contain an empty list.
* **Edges**. Edges that connect surface's control points. Together with
  **ControlPoints** output this form so-called "control net" of the surface.
  If the surface is not NURBS-like, this output will contain an empty list.
* **Weights**. Weights of surface's control points. If the surface is not
  NURBS-like, this output will contain an empty list.

Examples of usage
-----------------

Generate some random points (green), build an interpolating surface from them
(blue), and visualize it's control net (red and orange):

.. image:: https://user-images.githubusercontent.com/284644/91633596-2e407880-ea03-11ea-826c-3fe194fd264f.png

