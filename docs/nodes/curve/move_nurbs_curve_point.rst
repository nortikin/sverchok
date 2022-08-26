Move NURBS Curve Point
======================

Functionality
-------------

This node suggests several ways of adjusting a NURBS curve so that it would go
through another point at specified position, while keeping most of the curve
more or less in place.

Different methods of curve adjustment allow different degrees of freedom in
specifying what do you want to move and where to.

Inputs
------

This node has the following inputs:

* **Curve**. The NURBS Curve object to be adjusted. This input is mandatory.
* **T**. The value of curve parameter, point at which is to be moved. The default value is 0.5.
* **Index**. This input has different meaning for different curve adjustment methods being used:
  
   * For **Move one control point** method, this is the index of curve control point to be moved.
   * For **Adjust one weight** method, this is the index of curve weight to be adjusted.
   * For **Adjust two weights** method, this is the index of first of two curve
     weights to be adjusted. The second weight adjusted will be the following one.
   * For other methods, this input is not available.

   The default value is 1.

* **Distance**. The distance for which curve point at **T** parameter is to be moved.

  * For **Adjust one weight** method, positive values mean move the point
    toward corresponding control point (index of which is defined in **Index**
    input). Negative values mean movement in the oppposite direction.
  * For **Adjust two weight** method, positive values mean move the span of
    curve towards the corresponding curve control polygon leg (the one between
    control points **Index** and **Index+1**). Negative values mean movement in
    the opposite direction.
  * For other methods, this input is not available.

  The default value is 1.0.

* **Vector**. The vector for which the curve point at **T** parameter is to be
  moved. This input is available only when **Method** is set to **Move one
  control point**, **Move control points**, or **Insert knot**. The default
  value is ``(1.0, 0.0, 0.0)``.

Parameters
----------

This node has the following parameter:

* **Method**. The method to be used to adjust the curve. The following methods are available:

  * **Move one control point**. The node will move exactly one control point of
    the curve, to move curve point at **T** parameter by **Vector**. The index
    of control point being moved is specified in the **Index** input. Note that
    it is not always possible to move arbitrary curve point by arbitrary vector
    by moving specified control point. In intuitive terms, the point to be
    moved has to be near control point being moved.
  * **Adjust one weight**. The node will adjust one weight of the curve, to
    move curve point at **T** parameter directly towards corresponding control
    point, or in the opposite direction. The index of the weight being adjusted
    (and the index of corresponding control point) is specified in the
    **Index** input. Movement distance is specified in the **Distance** input.
    Note that it is not always possible to move arbitrary curve point by
    adjusting the specified curve weight. Also, if you try to move the point
    too far with this method, you will probably get unexpected curve shapes.
  * **Adjust two weights**. The node will adjust two weights of the curve, to
    move curve point at **T** parameter, together with neighbouring curve span,
    towards the corresponding control polygon leg, or in the opposite
    direction. The index of the first weight to be adjusted (and corresponding
    control point index) is specified in the **Index** input. Note that it is
    not always possible to move an arbitrary curve point by adjusting the
    specified weights. Also, if you try to move the point too far with this
    method, you will probably get unexpected curve shapes.
  * **Move control points**. The node will move several control points of the
    curve (approximately ``p`` of them, where ``p`` is the degree of the
    curve), to move curve point at **T** parameter by the specified vector. The
    node will automatically figure out which control points have to be moved.
    This algorithms gives most smooth results, but it requires more
    computations, so it is probably less performant.
  * **Insert knot**. The node will insert additional knot into curve's
    knotvector, and then move three control points, in order to move curve
    point at **T** parameter by specified vector. The node will automatically
    figure out which control points have to be moved.

  The default option is **Move one control point**.

Outputs
-------

This node has the following output:

* **Curve**. The adjusted curve.

Examples of Usage
-----------------

