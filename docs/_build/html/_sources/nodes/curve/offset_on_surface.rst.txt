Offset Curve on Surface
=======================

Functionality
-------------

This node does the following:

* Takes a Surface and a Curve, which is supposed to be in UV space of the surface;
* Draws a curve which is a result of mapping the provided curve into 3D space
  by the surface (similar to "Curve on Surface" node works);
* Then offsets that curve by specified amount, while remaining within the surface.

In some simple cases, it is possible to perform similar offset operation by
offsetting the original curve in surface's UV space, and then mapping the
result into 3D space. But as surface may stretch or compress it's UV space in
different proportions in different places, in any non-trivial case the result
would be very imprecise. This node, on the other hand, guarantees that the
distance between the original curve and it's offset will be equal to specified
amount with good precision.

Curve domain and parametrization: the same as of original curve.

Inputs
------

This node has the following inputs:

* **Curve**. The curve (in surface's UV space) to be offseted. The curve is
  supposed to lie in XOY, XOZ or YOZ coordinate plane, depending on **Curve
  Plane** parameter. This input is mandatory.
* **Surface**. The surface, in which the offset is to be performed. This input is mandatory.
* **Offset**. Offset amount (offset distance in 3D space). The default value is
  0.1. This input is available only when **Offset type** parameter is set to
  **Constant**.
* **OffsetCurve**. The curve defining the offset amount for each point of
  original curve. The curve is supposed to lie in XOY coordinate plane. The
  node uses this curve's mapping of T parameter to Y coordinate. For parameter
  of this offset curve, the node will use either parameter of the original
  curve, or it's length share, depending on **Offset curve type** parameter.
  This input is available and mandatory only if **Offset type** parameter is
  set to **Variable**.

Parameters
----------

This node has the following parameters:

* **Curve plane**. The coordinate plane where original curve is supposed to
  lie. The available values are **XY**, **YZ** and **XZ**. The default value is
  **XY**, which means that the original curve should lie in XOY coordinate
  plane, X coordinates of it's points will be used as surface's U parameter,
  and Y coordinates of curve's points will be used as surface's V parameter
  values.
* **Offset type**. This defines how the offset amount is specified. The available values are:

   * **Constant**. The offset amount is constant and it is specified in the **Offset** input.
   * **Variable**. The offset amount is changing along the curve; the offset
     amount at each point of the original curve is defined by another curve,
     which is provided in **OffsetCurve** input.

   The default value is **Constant**.

* **Offset curve use**. This parameter is available only when **Offset type**
  parameter is set to **Variable**. This defines what will be used as T
  parameter when calculating offset amount for each point of original curve.
  The available values are:

  * **Curve parameter**. T parameter of the original curve will be used. Note
    that in some cases this will distort the "offset curve" (compress it in one
    places and stretch in other places), as curve length is not required to be
    proportional to it's parameter.
  * **Curve length**. Length of corresponding segment of original curve will be
    used. This allows more precise control over where the offset amount should
    change. But this option is slower.

  The default option is **Curve parameter**.

* **Length resolution**. This parameter is available only when **Offset type**
  parameter is set to **Variable**, and **Offset curve use** parameter is set
  to **Curve length**. This defines the resolution for curve length
  calculation. The bigger the value, the more precise the calculation will be,
  but the slower. The default value is 50.

Outputs
-------

This node has the following outputs:

* **Curve**. The offseted curve (in 3D space).
* **UVCurve**. The offseted curve in surface's UV space; it will lie in XOY,
  YOZ or XOZ coordinate plane, depending on **Curve plane** parameter.

Examples of usage
-----------------

Constant offset of a curve on a surface:

.. image:: https://user-images.githubusercontent.com/284644/85555664-922f7500-b63f-11ea-8479-9ee8db89ee11.png

Similar setup, but with variable offset amount, controlled by a curve from "Curve mapper" node:

.. image:: https://user-images.githubusercontent.com/284644/85555750-a8d5cc00-b63f-11ea-8f28-3565e3a8d1e4.png

