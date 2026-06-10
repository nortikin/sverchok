Hobby Spline
============

.. image:: https://github.com/user-attachments/assets/250895c9-0c0e-443c-9241-ae03804fbd3b
  :target: https://github.com/user-attachments/assets/250895c9-0c0e-443c-9241-ae03804fbd3b

Functionality
-------------

This node generates a smooth curve defined as a **Hobby spline** through the
specified set of points. Hobby splines are based on John Hobby's algorithm
from MetaPost_ — a system for drawing high-quality technical illustrations
and vector graphics.

Hobby splines are **cubic Bezier curves** that interpolate through all given
points with **G1 (tangent) continuity** at every knot. This means:

* The curve passes exactly through all input points
* The tangent direction is continuous at every point — there are no sharp
  corners or discontinuities
* The curvature changes smoothly, giving a natural, flowing appearance

This is different from Catmull-Rom splines, which have C1 continuity (both
first and second derivatives are continuous). Hobby splines use a concept
called **mock curvature** — a heuristic that produces visually smooth curves
without requiring full C2 continuity. The result is a curve that looks natural
even with sharp turns between control points.

Hobby splines have the following advantages:

* They are widely used in technical illustration and vector graphics (MetaPost,
  TikZ, Asymptote)
* They produce visually smooth curves with natural-looking curvature
* They work correctly in 3D space — each triple of consecutive points defines
  a local plane, and the curve follows the 3D shape
* They can be easily converted to Bezier segments or NURBS curves
* They support tension and curl parameters for fine control over the shape

The Hobby algorithm works by computing the tangent angles at each point
(Hobby angles θ) that satisfy a tridiagonal system of equations. The solution
is found using the Thomas algorithm (for open curves) or direct linear
algebra (for cyclic curves).

.. _MetaPost: https://www.tug.org/metapost/

Tension
~~~~~~~

The **Tension** parameter controls how closely the curve follows the polyline
formed by the input points. It is analogous to the tension parameter in uniform
Catmull-Rom splines.

* **Tension = 1.0** (default): natural curvature, balanced between the polyline
  and a smooth curve
* **Tension → 0.75** (minimum): the curve becomes more "relaxed", bulging
  further away from the polyline between points
* **Tension → ∞**: the curve approaches the polyline itself — the control
  points move closer to the line segments, and the curve becomes more
  "tight" around the input points

Higher tension values make the curve stay closer to the straight lines between
points, while lower values make it more "floppy". The minimum supported value
is 0.75, which corresponds to the softest possible curve.

Curl Start / Curl End
~~~~~~~~~~~~~~~~~~~~~

The **Curl Start** and **Curl End** parameters control the behavior of the
curve at its endpoints. They determine the curvature at the start and end of
the spline.

* **Curl = 1.0** (default): the endpoint has a circular-arc-like curvature,
  meaning the curve departs from (or arrives at) the endpoint with a smooth,
  rounded turn
* **Curl = 0.0**: the endpoint has zero curvature — the curve departs from
  (or arrives at) the endpoint in a straight line, with no initial turn
* **Curl > 1.0**: the endpoint curves more sharply, creating a "hook" or
  "curl" effect at the endpoint

These parameters are especially useful when:

* You want the curve to start or end horizontally/vertically (set curl to
  achieve the desired direction)
* You are creating a closed shape and want smooth transitions at the join
  (use curl = 1.0 for both ends)
* You want the curve to approach a tangent line at the endpoint (use curl = 0.0)

For cyclic (closed) curves, the curl parameters are ignored — the curve is
automatically closed with smooth G1 continuity at the join.

Inputs
------

This node has the following inputs:

* **Vertices**. The points through which the curve should go. This input is
  mandatory. At least two points are required to build an open spline, and at
  least three points for a cyclic (closed) spline.
* **Tension**. Specifies the tension value of the spline. The default value is
  1.0. Values below 0.75 are not supported. It is possible to provide a
  separate tension value for each curve.
* **Curl Start**. Specifies the curl at the start endpoint. The default value
  is 1.0. Values range from 0.0 (zero curvature) to any positive value.
* **Curl End**. Specifies the curl at the end endpoint. The default value is
  1.0. Values range from 0.0 (zero curvature) to any positive value.

Parameters
----------

This node has the following parameters:

* **Cyclic**. Defines whether the curve should be cyclic (closed). When
  enabled, the last point connects back to the first, forming a closed loop.
  Unchecked by default.
* **Concatenate**. If enabled (default), the output is a single concatenated
  NURBS curve. If disabled, the output is a list of individual Bezier segments
  (one per curve segment between consecutive points).

Outputs
-------

This node has the following output:

* **Curve**. The generated curve object.

Examples of Usage
-----------------

Compare several spline types:

.. image:: https://github.com/user-attachments/assets/318d88c0-7c03-4455-98be-8588ca585c80
  :target: https://github.com/user-attachments/assets/318d88c0-7c03-4455-98be-8588ca585c80

* Green line - Cubic spline
* Brown line - Catmull-Rom spline
* Blue line - interpolated NURBS curve
* Violet line - Hobby spline.

A couple of other examples:

.. image:: https://github.com/user-attachments/assets/04984148-19bc-4325-82c9-599fc8055567
  :target: https://github.com/user-attachments/assets/04984148-19bc-4325-82c9-599fc8055567

.. image:: https://github.com/user-attachments/assets/5accd098-428a-4610-8000-6405d23976d2
  :target: https://github.com/user-attachments/assets/5accd098-428a-4610-8000-6405d23976d2

3D Spiral example:

.. image:: https://github.com/user-attachments/assets/e0f56ff5-fd85-4f8b-8949-0b04b088247f
  :target: https://github.com/user-attachments/assets/e0f56ff5-fd85-4f8b-8949-0b04b088247f

