Blend Curves
============

Functionality
-------------

This node takes two or more Curve objects, and connects them by adding new
curve(s) in the middle, to generate a smooth blending. For example, the end of
the first curve is connected to the beginning of the second curve. Generated
blending curves are Bezier curves. It is possible to define how smooth the
connection between initial curves and blending curve(s) should be.  

Inputs
------

This node has the following inputs:

* **Curve1**. First curve to be blended. This input is available and mandatory
  only if **Blend** parameter is set to **Two curves**.
* **Curve2**. Second curve to be blended. This input is available and mandatory
  only if **Blend** parameter is set to **Two curves**.
* **Curves**. List of curves to be blended. This input is available and
  mandatory only if **Blend** paramter is set to **List of curves**.
* **Factor1**. This input is available and mandatory only if **Blend**
  parameter is set to **Two curves**, and **Continuity** parameter is set to
  **Tangency**. This defines the strength with which the tangent vector of the
  first curve at it's end point will affect the generated blending curve. The
  default value is 1.0.
* **Factor2**. This input is available and mandatory only if **Blend**
  parameter is set to **Two curves**, and **Continuity** parameter is set to
  **Tangency**. This defines the strength with which the tangent vector of the
  second curve at it's starting point will affect the generated blending curve.
  The default value is 1.0.
* **Parameter**. This input is available only if **Continuity** parameter is
  set to **BiArc**. This defines the value of P parameter of the family of
  biarc_ curves, that are generated as blending curves. The default value is 1.0.

.. _biarc: https://en.wikipedia.org/wiki/Biarc

Parameters
----------

This node has the following parameters:

* **Continuity**. This defines how smooth the connection between initial curves
  and generated blending curves should be. The available options are:

  * **0 - Position**. Blending curve starts at the end of first curve and ends
    at the beginning of the second curve, but no attempts are made to make
    these connections smooth. As a result, the blending curve is always a
    segment of a straight line.
  * **1 - Tangency**. The blending curves are generated so that the tangent
    vectors of the curves are equal at their meeting points. The generated
    curves are cubic Bezier curves.
  * **1 - Bi Arc**. The blending curves are generated as biarc_ curves, i.e.
    pairs of circular arcs; they are generated so that the tanent vectors of
    the curves are equal at their meeting points.
  * **2 - Normals**. The blending curves are generated so that 1) tangent
    vectors of the curves are equal at the meeting points; 2) second
    derivatives of the curves are also equal at the meeting points. Thus,
    normal and binormal vectors of the curves are equal at their meeting
    points. The generated curves are Bezier curves of fifth order.
  * **3 - Curvature**. The blending curves are generated so that 1) tangent
    vectors of the curves are equal at the meeting points; 2) second and third
    derivatives of the curves are also equal at the meeting points. Thus,
    normal and binormal vectors of the curves, as well as curvatures of the
    curves, are equal at their meeting points. The generated curves are Bezier
    curves of order 7.

  The default value is **1 - Tangency**.

* **Blend**. These defines how the curves to be joined are provided. The available options are:

  * **Two curves**. The node will blend two curves, which are provided in
    inputs **Curve1** and **Curve2**, correspondingly.
  * **List of curves**. The node will blend arbitrary number of curves, which
    are provided in the **Curves** input.

  The default value is **Two curves**.

* **Concatenate**. If checked, then the node will output all initial curves
  together with generated blending curves, concatenated into one curve.
  Otherwise, original curves (optionally) and generated curves will be output
  as separate Curve objects. Checked by default.
* **Cyclic**. This paramter is available only when the **Blend** parameter is set
  to **List of curves**. If checked, then the node will connect the end of last
  curve to the beginning of the first curve. Unchecked by default.
* **Output source curves**. This parameter is available only when the **Blend**
  parameter is set to **List of curves**, and **Concatenate** parameter is not
  checked. If **Output source curves** is enabled, then the node will output
  original curves in single list with generated blending curves - for example,
  ``[Original curve 1; Blending curve 1; Original curve 2; Blending curve 2;
  Original curve 3]``. Otherwise, the node will output generated blending
  curves only. Checked by default.

Outputs
-------

This node has the following outputs:

* **Curve**. The generated curve (or list of curves).
* **ControlPoints**. Control points of all generated blending curves.

Example of usage
----------------

Generate two cubic curves from mesh objects (one of them is white - selected,
another is black - unselected); and blend them together with a smooth curve:

.. image:: https://user-images.githubusercontent.com/284644/82763139-eb2ca300-9e1e-11ea-9e21-a11232adc29c.png

