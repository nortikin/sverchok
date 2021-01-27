Bend Along Curve Field
======================

Functionality
-------------

This node generates a Vector Field, which bends some part of 3D space along the
provided Curve object.

It is in general not a trivial task to rotate a 3D object along a vector,
because there are always 2 other axes of object and it is not clear where
should they be directed to. So, this node supports 3 different algorithms of
object rotation calculation. In many simple cases, all these algorithms will
give exactly the same result. But in more complex setups, or in some corner
cases, results can be very different. So, just try all algorithms and see which
one fits you better.

* "Frenet" or "Zero-Twist" algorithms give very good results in case when
  extrusion curve has non-zero curvature in all points. If the extrusion curve
  has zero curvature points, or, even worse, it has straight segments, these
  algorithms will either make "flipping" surface, or give an error.
* "Householder", "Tracking" and "Rotation difference" algorithms are
  "curve-agnostic", they work independently of curve by itself, depending only
  on tangent direction. They give "good enough" result (at least, without
  errors or sudden flips) for all extrusion curves, but may make twisted
  surfaces in some special cases.
* "Track normal" algorithm is supposed to give good results without twisting
  for all extrusion curves. It will give better results with higher values of
  "resolution" parameter, but that may be slow.

Inputs
------

This node has the following inputs:

* **Curve**. The curve to bend the space along. This input is mandatory.
* **Src T Min**. The minimum value of the orientation coordinate, where the
  bending should begin. For example, if **Orientation axis** parameter is set
  to Z, this is the minimum value of Z coordinate. The default value is -1.0.
* **Src T Max**. The maximum value of the orientation coordinate, where the
  bending should end. For example, if **Orientation axis** parameter is set to
  Z, this is the maximum value of Z coordinate. The default value is 1.0.
* **Resolution**. The number of samples along the curve, used to calculate
  curve length parameter. This input is only available when **Scale along
  curve** parameter is set to **Curve length**. The higher the value is, the
  more precise is the calculation, but more time it is going to take. The
  default value is 50.

The field bends the part of space which is between **Src T Min** and **Src T
Max**, along the curve. For example, with default settings, the source part of
space is the space between Z = -1 and Z = 1. The behaviour of the field outside
of these bounds is not guaranteed.

Parameters
----------

This node has the following parameters:

* **Orientation**. Which axis of the source space should be elongated along the
  curve. The available values are X, Y and Z. The default value is Z. When the
  **Algorithm** parameter is set to **Zero-Twist** or **Frenet**, the only
  available option is Z.
* **Scale all axis**. If checked, all three axis of the source space will be
  scaled by the same amount as is required to fit the space between **Src T
  Min** and **Src T Max** to the curve length. Otherwise, only orientation axis
  will be scaled. Checked by default.
- **Algorithm**. Rotation calculation algorithm. Available values are:

  * Householder: calculate rotation by using Householder's reflection matrix
    (see Wikipedia_ article).                   
  * Tracking: use the same algorithm as in Blender's "TrackTo" kinematic
    constraint. This algorithm gives you a bit more flexibility comparing to
    other, by allowing to select the Up axis.                                                         
  * Rotation difference: calculate rotation as rotation difference between two
    vectors.                                         
  * Frenet: rotate the space according to curve's Frenet frame.
  * Zero-Twist: rotate the space according to curve's "zero-twist" frame.
  * Track normal: try to maintain constant normal direction by tracking it along the curve.

  Default value is Householder.

* **Up axis**.  Axis of donor object that should point up in result. This
  parameter is available only when Tracking algorithm is selected.  Value of
  this parameter must differ from **Orientation** parameter, otherwise you will
  get an error. Default value is X.
* **Scale along curve**. This defines how the scaling of the space along the
  curve is to be calculated. The available options are:

   * **Curve parameter**. Scale the space proportional to curve's T parameter.
   * **Curve length**. Scale the space proportional to curve's length. This
     usually gives more natural results, but takes more time to compute.

  The default option is **Curve parameter**.

.. _Wikipedia: https://en.wikipedia.org/wiki/QR_decomposition#Using_Householder_reflections

Outputs
-------

This node has the following output:

* **Field**. The generated bending vector field.

Examples of usage
-----------------

Bend a cube along some closed curve:

.. image:: https://user-images.githubusercontent.com/284644/79593221-93e73480-80f4-11ea-8c14-7f1511b1bd7b.png

It is possible to use one field to bend several objects:

.. image:: https://user-images.githubusercontent.com/284644/79593228-95186180-80f4-11ea-930f-59f3f124da63.png

