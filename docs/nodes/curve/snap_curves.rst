Snap Curves
===========

Functionality
-------------

This node takes two or more NURBS curve objects, and modifies them in such a
way that they become connected: end point of first curve coincides with start
point of the second curve, and so on. It is possible to define, which curve
must become "main" , and which curve should be adjusted in order to match the
"main" curve.

Optionally, this node can also adjust directions of curves at their start and
end points.

For this node, direction and order of curves are important. If you have several
curves with arbitrary directions, you may want to use "Sort Curves" node first,
to ensure that the end of each curve is near the beginning of the next curve.

This node can work with NURBS and NURBS-like curves only. It adjusts curves by
moving their control points, while trying to move all points as less as
possible. This means that curve structure is important for this node. For
example,

* If the curve has a lot of control points, the node will have to move only one
  or two of it's control points near the end, so that most of the curve will be
  left unchanged.
* If the curve has only a few of control points, for example 3 or 4, then
  movement of 1 or 2 control points can move almost whole curve.
* For curves with higher degree, each control point controls wider span of the
  curve. So when adjusting curves with higher degree, wider span of the curve
  will be moved.

Inputs
------

This node has the following inputs:

* **Curve1**. First curve to process. This input is available and mandatory
  only if **Input Mode** parameter is set to **Two Curves**.
* **Curve2**. Second curve to process. This input is available and mandatory
  only if **Input Mode** parameter is set to **Two Curves**.
* **Curves**. List of curves to be processed. This input is available and mandatory
  only if **Input Mode** parameter is set to **List of Curves**.

Parameters
----------

This node has the following parameters:

* **Input Mode**. The available options are **Two Curves** and **List of
  Curves**. The default option is **Two Curves**.
* **Bias**. This defines where two curves should meet. The available options are:
  
  * **Middle**. The meeting point will be defined as middle between end of
    first curve and start of second curve.
  * **Curve 1**. First curve will be considered "main", so it's end point will
    not be moved; start point of the second curve will be moved to end point of
    the first curve.
  * **Curve 2**. Second curve will be considered "main", so it's start point
    will not be moved; end point fo the first curve will be moved to start
    point of the second curve.

  The default option is **Middle**.
* **Tangents**. This defines whether the node should adjust directions of
  curves at their ends, and how exactly. The available options are:

  * **No matter**. The node will not bother about curve directions, and try to
    move curve ends properly while moving control points as less as possible.
  * **Preserve**. The node will try to preserve directions of the curves at their ends.
  * **Medium**. The node will adjust the directions of curves at their ends in
    such a way, that their tangent vectors will be equal to average between
    tangent vector of the first curve at it's end and tangent vector of the
    second curve at it's beginning.
  * **Curve 1**. The node will preserve the direction of the first curve at
    it's end, and adjust the direction of the second curve at it's beginning to
    match the first curve.
  * **Curve 2**. The node will preserve the direction of the second curve at
    it's beginning, and adjust the direction of the first curve at it's end to
    match the second curve.
  
  The default option is **No matter**.

* **Cyclic**. If checked, the node will also try to connect the end point of
  last curve to the start point of the first curve, in order to create a closed
  loop. Unchecked by default.

Outputs
-------

This node has the following output:

* **Curves**. The resulting curves.

Example of Usage
----------------

.. image:: ../../../docs/assets/nodes/curve/snap_curves.gif
   :target: ../../../docs/assets/nodes/curve/snap_curves.gif

