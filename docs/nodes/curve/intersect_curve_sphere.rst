Intersect Curve with Sphere
===========================

Dependencies
------------

This node reqiures SciPy_ library to work.

.. _SciPy: https://scipy.org/

Functionality
-------------

This node tries to find all intersections of the specified Curve with the
specified sphere; i.e.it searches for all points on the curve, that lie on
specified distance from the center point.

To find all intersections, the node splits the curve into several segments and
then searches for single intersection in each segment.

Inputs
------

This node has the following inputs:

* **Curve**. The curve to find intersections with. This input is mandatory.
* **Center**. Center point of the sphere. The default value is ``(0, 0, 0)``.
* **Radius**. Radius of the sphere. The default value is 1.0.
* **MaxResults**. This input is available only when the **Set max.results**
  parameter is checked. Defines the maximum number of intersection points this
  node can find. The default value is 1.

Parameters
----------

This node has the following parameters:

* **Use NURBS algorithm**. If checked, the node will use a special version of
  algorithm for NURBS and NURBS-like curves. This algorithm can be about 5x
  faster. But, if you pass a curve which is not NURBS, the node will raise an
  error (become red). If not checked, the node will use a generic algorithm,
  which can work with both NURBS and non-NURBS curve. Checked by default.
* **Init Resolution**. This parameter is only available when **Use NURBS
  algorithm** parameter is not checked. This specifies the initial number of
  segmetns the node will try to split the curve into, to find some
  intersections into each of them. If the node finds it necessary, it can split
  some of these segments further. The default value is 10, which is usually
  enough.
* **Set max. results**. If checked, the node allows to specify how many
  intersections do you wish to find. If not checked, the node will try to find
  all intersections. Unchecked by default.
* **Direction**. The direction on curve in which the node will search for
  intersections. The available options are **Forward by T** and **Backward by
  T**. THe default option is **Forward by T**. The order in which the node
  produces the points is defined by this parameter. For example, if you need
  only the first intersection with the sphere (with smallest value of curve's T
  parameter), you can check **Set max. results**, and set **MaxResults** input
  to 1.
* **Accuracy**. This parameter is available in the N panel only. This defines
  the accuracy level - number of exact digits after decimal point. The default
  value is 4.
* **Max Subdivisions**. Maximum number of recursive segment subdivisions
  allowed in case when both ends of the segment lie on the same side of the
  sphere, but there is a possibility that some part of the segment lies on the
  other side. The default value of 3 is usually enough.

Outputs
-------

This node has the following outputs:

* **Point**. Intersection points.
* **T**. Curve T parameters corresponding to intersection points.

Example of Usage
----------------

.. image:: https://github.com/user-attachments/assets/c507f35c-bbc5-4f4b-b540-5c44fb3afbeb
  :target: https://github.com/user-attachments/assets/c507f35c-bbc5-4f4b-b540-5c44fb3afbeb

