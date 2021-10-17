Adaptive Plot NURBS Curve
=========================

Functionality
-------------

Given a Curve object, this node generates a mesh representation of the curve in
such a way, that each edge declines from corresponding curve segment for a
distance less than specified tolerance. Thus, in some parts of curve, vertices
can be far from one another, while in "most interesting" parts of curve,
vertices will be very dense.

This node can work with NURBS and NURBS-like curves only. For arbitrary curves,
consider use of "Adaptive Plot Curve" node.

The following algorithm is used:

* The whole domain of curve's T parameters is divided into N even parts. Number
  N is usually very small, such as 2 or 3.
* For each subdomain, it is checked if the segment of the curve is close enough
  to straight line segment. If yes, then algorithm is done for this segment. If
  not, then this segment is subdivided again into N even parts.
* All generated points are connected to make a curve-like mesh object.

Inputs
------

This node has the following inputs:

* **Curve**. The curve to be plotted. This input is mandatory.
* **InitCuts**. The number of subdivisions to be used at each recursive step.
  The default value is 2. Bigger values not necessarily give larger number of
  vertices generated.
* **Tolerance**. Maximum allowable distance between mesh's edge and
  corresponding curve segment. The default value is 0.0001.

Parameters
----------

This node has the following parameter:

* **Join**. If checked, then the node will output one single list of objects
  for all provided curves - for example, data in **Verties** output will have
  nesting level 3 even if data in **Curve** input had nesting level 2.
  Otherwise, the node will output separate list of object for each list of
  curves in the input - i.e., **Verties** output will have nesting level 4 if
  **Curve** input had nesting level 2. Checked by default.

Outputs
-------

This node has the following outputs:

* **Vertices**. The vertices of the generated mesh.
* **Edges**. The edges of the generated mesh.
* **T**. Values of curve's T parameter for all generated points on the curve.

Examples of Usage
-----------------

Example 1:

.. image:: https://user-images.githubusercontent.com/284644/137624189-60f75834-b119-4340-a40a-fbb2f3e7f3fb.png

Example 2:

.. image:: https://user-images.githubusercontent.com/284644/137624185-964ea9bf-463c-418c-a674-1f88fab24c4d.png

