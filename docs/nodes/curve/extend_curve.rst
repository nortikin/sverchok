Extend Curve
============

Functionality
-------------

This node generates a continuation of given Curve beyond it's end points in a
smooth manner. It can be used if you for some reason have just a segment of a
curve, and want to continue it, for example, until it meets some plane or
surface.

Inputs
------

This node has the following inputs:

* **Curve**. The curve to be extended. This input is mandatory.
* **StartExt**. This defines how far the curve should be extended beyond it's
  starting point. Depending on **Extend by** parameter, this is measured either
  in terms of curve's T parameter, or in terms of curve length. Default value
  is 1.0. If this input is set to 0.0, then no continuation will be generated
  beyond curve's starting point.
* **EndExt**. This defines how far the curve should be extended beyond it's
  ending point. Depending on **Extend by** parameter, this is measured either
  in terms of curve's T parameter, or in terms of curve length. Default value
  is 1.0. If this input is set to 0.0, then no continuation will be generated
  beyond curve's ending point.

Parameters
----------

This node has the following parameters:

* **Type**. Extending curves type. The available options are:

  * **1 - Line**. Extend the curve with straight line segments. The direction of
    lines is calculated accordingly to curve's tangent directions at starting
    and ending point. Thus, it is guaranteed that the resulting curve will have
    continuous first derivative at the point where original curve is glued with
    it's extension.
  * **1 - Arc**. Extend the curve with circular arcs. Extension direction and arc
    radius is calculated from curve's tangents. The plane where the arc will
    lie is calculated based on curve's second derivatives at ending points.
    Thus, it is guaranteed that the resulting curve will have continuous first
    derivative at the point where original curve is glued with it's extension.
  * **2 - Smooth - Normal**. Extend the curve with segments of second order
    (quadratic) curves. The coefficients of curves are calculated based on
    original curve's tangent and second derivatives directions at the ending
    points. Thus, it is guaraneed that the resulting curve will have continuous
    first and second derivatives at the point where original curve is glued
    with it's extension.
  * **3 - Smooth - Curvature**. Extend the curve with segments of third order
    (cubic) curves. The coefficients of curves are calculated based on
    original curve's tangent, second and third derivatives directions at the ending
    points. Thus, it is guaraneed that the resulting curve will have continuous
    first, second and third derivatives at the point where original curve is glued
    with it's extension.

  The default option is **1 - Line**.

* **Extend by**. This defines the units in which values of **StartExt**,
  **EndExt** inputs is measured. The available options are:

  * **Curve parameter**. Inputs define the range of curve's T parameter. Since
    coefficients of the generated extension curves are calculated
    automatically, the length of extension curves can be hard to predict from
    the input values. On the other hand, this option is the faster one.
  * **Curve length**. Inputs define the length of extension curves. Required
    ranges of curve's T parameter is calculated numerically, so this option is
    slower.

  The default option is **Curve parameter**.

* **Length resolution**. This parameter is available in the N panel only, and
  only when **Extend by** parameter is set to **Curve length**. Defines the
  resolution value for curve length calculation. The higher the value is, the
  more precisely extension curves length will be equal to the specified inputs,
  but the slower the computation will be. The default value is 50.

Outputs
-------

This node has the following outputs:

* **ExtendedCurve**. The original curve extended by one extension curve at the
  beginning and another curve at the end.
* **StartExtent**. Extension curve generated at the beginning of the original curve.
* **EndExtent**. Extension curve generated at the end of the original curve.

Example of usage
----------------

Build part of curve from points, and then extend it to additional lenght of 1
at the beginning and to additional length of 2 at the end:

.. image:: https://user-images.githubusercontent.com/284644/84564568-07679400-ad7c-11ea-8370-c4a8008a8c74.png

