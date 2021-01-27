Bi Arc
======

Functionality
-------------

This node generates a BiArc_ - i.e. a Curve, which is composed of two circular
arcs. Two arcs are joined so that their tangent vectors have the same direction
at the meeting point. A family of biarc curves is defined by start and end points
and tangent vectors at these points. Specific curve from such family is
selected by specifying the P parameter. Default value of P = 1.0 ensures
minimum change of curvature at the junction point of two arcs. See
illustrations in the Wikipedia article for better explanation of this
parameter.

This node can generate only planar curves. If specified points and tangent
vectors do not lie in the same plane, the node will raise an exception (become
red), and processing will stop.

.. _BiArc: https://en.wikipedia.org/wiki/Biarc

Inputs
------

This node has the following inputs:

* **Point1**. Start point of the curve. The default value is ``(0, 0, 0)``
  (global origin).
* **Point2**. End point of the curve. The default value is ``(4, 0, 0)``.
* **Tangent1**. Tangent vector at the start point of the curve. Length of this
  vector is not used, only direction. The default value is ``(0, 1, 0)``.
* **Tangent2**. Tangent vector at the end point of the curve. Length of this
  vector is not used, only diretion. The default value is ``(0, 1, 0)``.
* **Parameter**. The value of P parameter for selecting a biarc curve from a
  family. The default value is 1.0.

Parameters
----------

This node has the following parameters:

* **Show Details**. If checked, several outputs of the node with detailed
  information about generated arcs will be shown. Unchecked by default.
* **Join**. If checked, the node will generate one flat list of curves for all
  lists of input parameters. Otherwise, the node will generate a separate list
  of curves for each list of input parameters. Checked by default.
* **Planar Accuracy**. This parameter is available in the N panel only.
  Tolerance value for checking if provided points and tangent vectors lie in
  the same plane. The bigger the value is, the more precisely this condition
  must be respected. If points and vectors do not lie precisely in the same
  plane, the generated curve can be not passing exactly through the provided
  points and provided tangent vectors. The default value is 6.

Outputs
-------

This node has the following outputs:

* **Curve**. The generated biarc curve.
* **Arc1**. The first arc of the generated biarc.
* **Arc2**. The second arc of the generated biarc.
* **Center1**. This output is available only if **Show Details** parameter is
  checked. The center of the first arc.
* **Center2**. This output is available only if **Show Details** parameter is
  checked. The center of the second arc.
* **Radius1**.  This output is available only if **Show Details** parameter is
  checked. The radius of the first arc.
* **Radius2**.  This output is available only if **Show Details** parameter is
  checked. The radius of the second arc.
* **Angle1**.  This output is available only if **Show Details** parameter is
  checked. The angle of the first arc.
* **Angle2**.  This output is available only if **Show Details** parameter is
  checked. The angle of the second arc.
* **Junction**. This output is available only if **Show Details** parameter is
  checked. The junction point of two arcs.

Examples of Usage
-----------------

A simple example:

.. image:: https://user-images.githubusercontent.com/284644/94367821-63bbad00-00fa-11eb-8ccf-7b9c2ed6d345.png

A reproduction from Wikipedia illustration: a family of biarc curves with fixed
start and end points and tangent vectors, but with P parameter ranging from -4
to 4:

.. image:: https://user-images.githubusercontent.com/284644/94367816-61f1e980-00fa-11eb-971a-5b9808b36082.png

