Tangents Curve
==============

Functionality
-------------

This node generates a Curve object, defined by series of points, through which
the curve must pass, and tangent vectors of the curve at those points.

The curve is generated as a series of cubic Bezier curves. Control points of
Bezier curves are defined as follows:

* For each segment defined by a pair of input points, one Bezier curve is
  generated - for example, one curve for first and second point, one curve for
  second and third point, and so on.
* For each segment, the first point is the starting point of Bezier curve, and
  the second point is the end point of Bezier curve.
* Provided tangent vectors are placed so that the middle point of each vector
  is at corresponding input point - middle of the first tangent vector at the
  first input point, and so on. Then end points of these vectors will define
  additional control points for Bezier curves.

Generated curves may be optionally concatenated into one Curve object.

Inputs
------

This node has the following inputs:

* **Points**. List of points, through which the generated curve should pass.
  This input is mandatory, and must contain at least two points.
* **Tangents**. List of vectors, which are tangent vectors at corresponding
  points in the **Points** input. This input is mandatory.

Parameters
----------

This node has the following parameters:

* **Cyclic**. If checked, then the node will generate additional Bezier curve
  segment to connect the last point with the first one. Unchecked by default.
* **Concatenate**. If checked, then the node will concatenate all generated
  Bezier curve segments into one Curve object. Otherwise, it will output each
  segment as a separate Curve object. Checked by default.

Outputs
-------

This node has the following outputs:

* **Curve**. Generated curve (or list of curves).
* **ControlPoints**. Control points of all generated Bezier curves. This output
  contains a separate list of points for each generated curve segment.

Examples of usage
-----------------

Simple example, with points and curves defined manually:

.. image:: https://user-images.githubusercontent.com/284644/82763513-c423a080-9e21-11ea-9e25-38847a6fa464.png

More complex example: draw a smooth curve so that it would touch three circles in specific points:

.. image:: https://user-images.githubusercontent.com/284644/82763926-8411ed00-9e24-11ea-9a5b-171c580155b0.png

