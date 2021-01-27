Offset Curve
============

Functionality
-------------

This node generates a Curve, calculated as offset of another Curve by some
amount. It takes all points of original curve and moves them in direction
perpendicular to curve's tangent. In other words, this "offsetting" operation
can be described as extruding one single point along the curve.

When we say "offset all points of curve in direction perpendicular to curve's
tangent", there is a good question: where exactly? There are several algorithms
how to define a reference frame associated with curve's point and curve's
tangent direction. In simplest cases, all of them will give very similar
results. In more complex cases, results will be very different. Different
algorithms give best results in different cases:

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
* "Specified plane" algorithm selects offset direction vector so that it
  satisfies two conditions: 1) it is perpendicular to curve's tangent vector,
  and 2) it lies in so-called "offset operation plane", which is specified by
  user by providing the normal vector of such plane (in other words, offset
  direction vector is perpendicular to normal vector provided by user). This
  algorithm is supposed to give good results for planar or almost planar
  curves. The resulting curve may have twists in places where original curve's
  tangent vector is parallel to offset operation plane's normal (i.e. tangent
  is perpendicular to offset operation plane). Hint: you may use "Linear
  approximation" node to automatically calculate normal vector of offset
  operation plane.

For all algorithms, reference frame's Z axis is always pointing along curve's
tangent direction. Two other axes are always perpendicular to tangent
direction, but where exactly they are pointing - depends on the algorithm. For
Frenet algorithm, X axis is pointing along curve's normal and Y axis is
pointing along curve's binormal.

Curve domain and parametrization: the same as of original curve.

Inputs
------

This node has the following inputs:

* **Curve**. The curve to be offseted. This input is mandatory.
* **Offset**. Offset amount. This input is available only if **Algorithm**
  parameter is set to **Specified plane**, or the **Direction** parameter is
  set to **X (Normal)** or **Y (Binormal)**. The input is not available when
  **Offset type** parameter is set to **Variable**. The default value is 0.1.
* **OffsetCurve**. The curve defining the offset amount for each point of
  original curve. The curve is supposed to lie in XOY coordinate plane. The
  node uses this curve's mapping of T parameter to Y coordinate. For parameter
  of this offset curve, the node will use either parameter of the original
  curve, or it's length share, depending on **Offset curve type** parameter.
  This input is available and mandatory only if **Offset type** parameter is
  set to **Variable**.
* **Vector**. Offset direction vector. This input is available only if
  **Algorithm** parameter is set to **Specified plane**, or the **Direction**
  parameter is set to **Custom (N/B/T)**.

  * For **Specified plane** algorithm, this input defines the normal vector of
    offset operation plane (offset direction vector will be always
    perpendicular to it).
  * For other algorithms, Components of the vector are used within curve frame,
    calculated according to **Algorithm** parameter. For Frenet algorithm, X
    component of the vector represents offset along curve's normal, Y component
    of the vector represents offset along curve's binormal, and Z component of
    the vector represents offset along curve's tangent.
    
  The default value is ``(0.1, 0, 0)``.

* **Resolution**. Number of samples for **Zero-Twist** or **Track normal**
  rotation algorithm calculation. It is also used for curve length calculation,
  when **Offset type** parameter is set to **Variable**, and **Offset curve
  use** parameter is set to **Curve length**. The more the number is, the more
  precise the calculation is, but the slower. The default value is 50. This
  input is only available when **Algorithm** parameter is set to **Zero-Twist**
  or **Track normal**, or when **Offset type** parameter is set to **Variable**
  and **Offset curve use** parameter is set to **Curve length**.

Parameters
----------

This node has the following parameters:

* **Algorithm**. Curve frame calculation algorithm. The available options are:

  * **Frenet**. Rotate the profile curve according to Frenet frame of the
    extrusion curve.
  * **Zero-Twist**. Rotate the profile curve according to "zero-twist" frame of
    the extrusion curve.
  * **Householder**: calculate rotation by using Householder's reflection matrix
    (see Wikipedia_ article).                   
  * **Tracking**: use the same algorithm as in Blender's "TrackTo" kinematic
    constraint. This node currently always uses X as the Up axis.
  * **Rotation difference**: calculate rotation as rotation difference between two
    vectors.                                         
  * **Track normal**: try to maintain constant normal direction by tracking it
    along the curve.
  * **Specified plane**: offset direction vector will be always lying in a
    plane which is defined by normal vector provided in **Vector** input.

  The default option is **Householder**.

* **Direction**. This defines offset direction. This input is not available
  when **Algorithm** parameter is set to **Specified plane**. The available
  options are:

   * **X (Normal)**. Offset along curve reference frame's X axis (for Frenet
     frame - curve normal).
   * **Y (Binormal)**. Offset along curve reference frame's Y axis (for Frenet
     frame - curve binormal).
   * **Custom (N/B/T)**. Offset along user-provided vector.

   The default option is **X (Normal)**.

.. _Wikipedia: https://en.wikipedia.org/wiki/QR_decomposition#Using_Householder_reflections

Outputs
-------

This node has the following output:

* **Curve**. The offseted curve.

Examples of usage
-----------------

Offset one curve with several different offset amounts:

.. image:: https://user-images.githubusercontent.com/284644/84906631-a4536580-b0cb-11ea-83b7-5a9920757554.png

Example of **Custom (N/B/T)** mode usage:

.. image:: https://user-images.githubusercontent.com/284644/84906638-a5849280-b0cb-11ea-98a7-aad8803bfb9d.png

Example of **Specified plane** mode usage. Here **Linear approximation** node
is used to automatically detect the plane where the curve is lying (mostly); it
outputs a normal vector, which is nearly OY axis, so the offset operation plane
will be nearly XOZ. Note that the offsetted curve has a twist in a place where
the tangent of original curve is perpendicular to offset operation plane.

.. image:: https://user-images.githubusercontent.com/284644/85607132-3da2ee80-b66d-11ea-9c8b-2e730dd97751.png

Example of **Variable** offset mode usage:

.. image:: https://user-images.githubusercontent.com/284644/85608724-c79f8700-b66e-11ea-97f8-5b54e9d90401.png

