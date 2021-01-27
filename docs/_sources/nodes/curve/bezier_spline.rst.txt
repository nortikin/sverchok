Bezier Spline (Curve)
=====================

Functionality
-------------

This node generates a Bezier_ Curve object. It is possible to generate curves
of second order (quadratic), third order (cubic), or arbitrary order (generic).
For cubic curves, there are several ways to define the control points.

.. _Bezier: https://en.wikipedia.org/wiki/B%C3%A9zier_curve

Curve parametrization: from 0 to 1.

Inputs
------

This node has the following inputs:

* **Start**. Starting point of the curve. This node is not available if
  **Mode** parameter is set to **Generic**.
* **Control1** / **Tangent1**. Exact meaning of this input depends on **Mode** parameter:

   * When mode is **Cubic 2pts + 2 controls**, then this is the first control point.
   * When mode is **Cubic 2pts + 2 tangents**, then this is a tangent vector at the starting point.
   * When mode is **Cubic 4pts**, then this is the second point on the curve, used for interpolation.
   * When mode is **Quadratic**, then this is a middle control point of the curve.
   * This input is not available when mode is **Generic**.

* **Control2** / **Tangent2**. Exact meaning of this input depends on **Mode** parameter:

  * When mode is **Cubic 2pts + 2 controls**, then this is the second control point.
  * When mode is **Cubic 2pts + 2 tangents**, then this is a tangent vector at the end point of the curve.
  * When mode is **Cubic 4pts**, then this is the third point on the curve, used for interpolation.
  * This input is not available in other modes.

* **End**. Ending point of the curve. This node is not available if
  **Mode** parameter is set to **Generic**.
* **ControlPoints**. Control points of the curve. This input is only available
  when the **Mode** paramter is set to **Generic**. Note that Bezier curve
  begins at it's first control point and ends at it's last control point, but
  it in general does not pass through all other control points.

Parameters
----------

This node has the following parameters:

* **Mode**. This defines how the control points will be provided, as well as
  order of the curve. The available options are:

  * **Cubic 2pts + 2 controls**. Generate a cubic spline (with four control
    points). **Start** and **End** inputs define start and end points;
    **Control1** and **Control2** points define two additional control points.
  * **Cubic 2pts + 2 tangents**. Generate a cubic spline. **Start** and **End**
    inputs define start and end points. **Tangent1** input defines the tangent
    vector at the starting point; **Tangent2** input defines the tangent vector
    at the end point. This mode of defining a Bezier curve is also known as
    Hermite spline.
  * **Cubic 4pts**. Generate a cubic spline, which goes through four provided
    control points (interpolating spline). Four control points are defined by
    **Start**, **Control1**, **Control2**, **End** inputs.
  * **Quadratic**. Generate a quadratic spline (with three control points).
    **Start** and **End** inputs define start and end points; **Control1**
    input defines an additional control point for the middle of the curve.
  * **Generic**. Generate a Bezier spline of arbitrary order, which is defined
    by number of provided control points. Control points are provided in the
    **ControlPoints** input. At least two control points must be provided.

   The default value is **Cubic 2pts + 2 controls**.

* **Cyclic**. This parameter is only available when **Mode** parameter is set
  to **Generic**. If checked, then the node will generate a closed curve, by
  adding the first control point in the end of list of control points. Note
  that in general, closed Bezier curve will not be smooth at that closing
  point.

Outputs
-------

This node has the following outputs:

* **Curve**. Generated Bezier curve.
* **ControlPoints**. List of all control points of generated curve(s).

Examples of usage
-----------------

Cubic Bezier curve by four control points:

.. image:: https://user-images.githubusercontent.com/284644/82762154-dd741f00-9e18-11ea-875b-ed3a59c3b76c.png

Cubic Bezier curve by two points and two tangents (Hermite spline):

.. image:: https://user-images.githubusercontent.com/284644/82762156-df3de280-9e18-11ea-96a9-695476bf6fdc.png

Cubic Bezier curve interpolated through four points:

.. image:: https://user-images.githubusercontent.com/284644/82762157-df3de280-9e18-11ea-987a-15eeb02c8bac.png

Quadratic Bezier curve by three points:

.. image:: https://user-images.githubusercontent.com/284644/82762158-dfd67900-9e18-11ea-9f52-98374c7605df.png

Generic Bezier curve (of fifth order, in this case):

.. image:: https://user-images.githubusercontent.com/284644/82756588-7d6b8180-9df4-11ea-925e-1628a4413bf9.png

