Bi Arc
======

.. image:: https://user-images.githubusercontent.com/14288520/205462176-6c609aad-9fd8-4796-8b9c-37118a63a52c.png
  :target: https://user-images.githubusercontent.com/14288520/205462176-6c609aad-9fd8-4796-8b9c-37118a63a52c.png

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

.. image:: https://user-images.githubusercontent.com/14288520/205462337-25f75811-864d-4307-9ad2-ce4972b36ac6.png
  :target: https://user-images.githubusercontent.com/14288520/205462337-25f75811-864d-4307-9ad2-ce4972b36ac6.png

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

.. image:: https://user-images.githubusercontent.com/14288520/205463037-041107d2-47cf-4aa7-8cde-863c0a8bd7bf.png
  :target: https://user-images.githubusercontent.com/14288520/205463037-041107d2-47cf-4aa7-8cde-863c0a8bd7bf.png

Parameters
----------

This node has the following parameters:

* **Show Details**. If checked, several outputs of the node with detailed
  information about generated arcs will be shown. Unchecked by default.

.. image:: https://user-images.githubusercontent.com/14288520/205464077-b7407453-378c-4654-bfd2-1c6413a69ca6.png
  :target: https://user-images.githubusercontent.com/14288520/205464077-b7407453-378c-4654-bfd2-1c6413a69ca6.png

* **Join**. If checked, the node will generate one flat list of curves for all
  lists of input parameters. Otherwise, the node will generate a separate list
  of curves for each list of input parameters. Checked by default.

.. image:: https://user-images.githubusercontent.com/14288520/205464318-bcd70012-c52b-4c8d-b5fb-73263ccb88c3.png
  :target: https://user-images.githubusercontent.com/14288520/205464318-bcd70012-c52b-4c8d-b5fb-73263ccb88c3.png

* **Planar Accuracy**. This parameter is available in the N panel only.
  Tolerance value for checking if provided points and tangent vectors lie in
  the same plane. The bigger the value is, the more precisely this condition
  must be respected. If points and vectors do not lie precisely in the same
  plane, the generated curve can be not passing exactly through the provided
  points and provided tangent vectors. The default value is 6.

.. image:: https://user-images.githubusercontent.com/14288520/205464361-a921a950-2907-44b2-b283-8d326bf6ff3f.png
  :target: https://user-images.githubusercontent.com/14288520/205464361-a921a950-2907-44b2-b283-8d326bf6ff3f.png

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

.. image:: https://user-images.githubusercontent.com/14288520/205464670-18bafcd1-29d2-4cdc-b506-471df36b0787.png
  :target: https://user-images.githubusercontent.com/14288520/205464670-18bafcd1-29d2-4cdc-b506-471df36b0787.png

Examples of Usage
-----------------

A simple example:

.. image:: https://user-images.githubusercontent.com/14288520/205464786-a97e435d-2a3a-4412-a0e5-ced1e4e8d8c2.png
  :target: https://user-images.githubusercontent.com/14288520/205464786-a97e435d-2a3a-4412-a0e5-ced1e4e8d8c2.png

* Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`

---------

A reproduction from Wikipedia illustration: a family of biarc curves with fixed
start and end points and tangent vectors, but with P parameter ranging from -4
to 4:

.. image:: https://user-images.githubusercontent.com/14288520/205464989-ae2ee45e-e16f-4236-bebf-8cee19c5af41.png
  :target: https://user-images.githubusercontent.com/14288520/205464989-ae2ee45e-e16f-4236-bebf-8cee19c5af41.png

* Number-> :doc:`Number Range </nodes/number/number_range>`
* Vector-> :doc:`Vector Polar Input </nodes/vector/vector_polar_in>`
* Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`