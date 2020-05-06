Adaptive Plot Curve
===================

Functionality
-------------

Given a Curve object, this node generates a mesh representing the curve. This
way, it is similar to "Evaluate Curve" node with "Auto" mode. But, this node
tries to generate less points for more "straight" parts of the curve, and more
points for the most interesting parts of the curve. This way, the node is
similar to "Adaptive Tessellate Surface" node.

The following algorithm is used:

* The whole domain of curve's T parameters is subdivided into even parts.
* Then some points are added into "most interesting" intervals. "Interesting" can be defined as:

   * Having greater length;
   * Having bigger curvature value.

   Number of points to be added into each subdivision is calcluated proportionally to this "subdivision factor".
   These additional points can be distributed either evenly, or randomly.

* Then all resulting points are connected to make a curve-like mesh object.

Inputs
------

This node has the following inputs:

* **Curve**. The curve to be plotted. This input is mandatory.
* **Samples**. Number of initial subdivisions. The default value is 25.
* **Min per segment**. Minimal number of additional points, which is to be
  added into intervals which have the least value of subdivision factor (length
  and/or curvature). The default value is 0 - do not add points to such
  intervals.
* **Max per segment**. Maximum number of additional points, which is to be
  added into intervals which have the greatest value of subdivision factor
  (length and/or curvature). The default value is 5.
* **Seed**. Random seed value. This input is only available when the **Random**
  parameter is enabled. The default value is 0.

Parameters
----------

This node has the following parameters:

* **By Curvature**. Use curve curvature value to distribute additional points
  on the curve: places with greater curvature value will receive more points.
  Checked by default.
* ** By Length**. Use segment lengths to distribute additional points on the
  curve: segments with greater length will receive more points. Unchecked by
  default.
* **Random**. If checked, then additional points will be distributed randomly.
  Otherwise, additional points will be distributed evenly inside each segment
  of initial subdivision. Unchecked by default.
* **Curvature Clip**. This parameter is available only in the N panel of the
  node, only when the **By Curvature** parameter is enabled. The calculated
  values of curve curvature will be restricted to do not exceed this number.
  This is used to ignore places on the curve where it has too high values of
  curvature (sharp points) - otherwise the algorithm would be placing all the
  additional points to such places. The default value is 100. Usually you do
  not have to change this value. Set the parameter to 0 (zero) to disable this
  part of the algorithm.

Outputs
-------

This node has the following outputs:

* **Vertices**. The vertices of the generated mesh.
* **Edges**. The edges of the generated mesh.
* **T**. Values of curve's T parameter for all generated points on the curve.

