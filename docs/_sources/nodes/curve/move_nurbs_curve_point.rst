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

* **Vector** / **Point**. This input is available only when **Method** is set
  to **Move one control point**, **Move control points**, or **Insert knot**.
  If **Mode** parameter is set to **Relative**, this input specifies the vector
  for which the curve point at **T** parameter is to be moved. In **Absolute**
  mode, this input specifies the point where curve point is to be moved to. The
  default value is ``(1.0, 0.0, 0.0)``.

Parameters
----------

This node has the following parameters:

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

* **Preserve tangent**. This parameter is available only when **Method** is set
  to **Move control points**. If checked, the node will try to preserve the
  direction of curve tangent at the point being moved. In many cases, this
  gives only a slight difference; but sometimes this will make the result
  smoother. Unchecked by default.
* **Mode**. The available options are **Relative** and **Absolute**. In the
  **Relative** mode, you specify the movement vector; in the **Absolute** mode,
  you specify the target point. The default mode is **Relative**.

Outputs
-------

This node has the following output:

* **Curve**. The adjusted curve.

Examples of Usage
-----------------

An illustration of **Move one control point** method. Here, black is the
original curve; dark blue is it's control polygon; light blue point is the
point at T parameter on the original curve. Green is the resulting curve, and
big green point is the resulting point. In this case, only control point number
7 is moved.

.. image:: https://user-images.githubusercontent.com/284644/186957079-ceee637d-be54-4d26-8474-04dd4543a011.png

An example of **Adjust one weight** method. Here, the blue point is moved
towards the control point number 8. Curve control points are not moved, only
one curve weight is changed.

.. image:: https://user-images.githubusercontent.com/284644/186957074-4f520bad-ff48-48d1-a3b4-ebe2fec1d270.png

An example of **Adjust two weights** method. Here, the blue point is pushed
away from control polygon leg between control points 4 and 5 (note the negative
value of Distance parameter). Again, control points are not moved, only weights
are changed.

.. image:: https://user-images.githubusercontent.com/284644/186957069-2bb35686-1d3b-4abb-94cb-fb0fc03a338d.png

An example of **Move control points** method. Here, the blue point is moved by
specified vector by moving of three control points (6, 7 and 8).

.. image:: https://user-images.githubusercontent.com/284644/186957065-2b465e62-82f7-48ce-a38a-402580dcd7e7.png

An example of **Insert knot** method. The point is moved by inserting a knot,
thus creating additional control points, and moving three control points.

.. image:: https://user-images.githubusercontent.com/284644/186957056-66fb3952-664a-4368-92e3-ab48487d51b6.png

