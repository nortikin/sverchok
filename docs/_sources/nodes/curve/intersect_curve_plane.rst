Intersect Curve with Plane
==========================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/cd2a24f5-52d5-450a-bcc4-a90f8ff98125
  :target: https://github.com/nortikin/sverchok/assets/14288520/cd2a24f5-52d5-450a-bcc4-a90f8ff98125

Dependencies
------------

This node requires SciPy_ library to work.

.. _SciPy: https://scipy.org/

Functionality
-------------

This node tries to find all intersections of the specified Curve with a
specified (infinite) plane. The plane is specified by providing a normal vector
and a point on the plane.

To find all intersections, the node splits the curve into several segments and
then searches for single intersection in each segment.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/b231613e-fd3a-46c4-9fd3-cdd0b586f092
  :target: https://github.com/nortikin/sverchok/assets/14288520/b231613e-fd3a-46c4-9fd3-cdd0b586f092

* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Matrix-> :doc:`Matrix Normal </nodes/matrix/matrix_normal>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`
* Scene-> :doc:`Bezier Input </nodes/exchange/bezier_in>`

Inputs
------

This node has the following inputs:

* **Curve**. The curve to find intersections with. This input is mandatory.
* **Point**. The point on the plane. The default value is ``(0, 0, 0)``.
* **Normal**. The normal vector of the plane. The default value is ``(0, 0,
  1)``. Thus, by default the plane is XOY coordinate plane.

Parameters
----------

This node has the following parameters:

* **NURBS**. If checked, the node will apply NURBS-specific algorithm for NURBS
  and NURBS-like curves. This algorithm can be about 50% faster comparing to
  generic algorithm. Unchecked by default.
* **Init resolution**. Number of segments to subdivide the curve in. This
  defines the maximum number of intersection this node can potentially find.
  For example, if you set this to 1, but actually the curve intersects the
  plane in two places, then the node will actually find only one of
  intersections. The default value is 10.
* **Accuracy**. This parameter is available in the N panel only. This defines
  the accuracy level - number of exact digits after decimal point. The default
  value is 4.

Outputs
-------

This node has the following outputs:

* **Point**. Intersection points.
* **T**. Curve's T parameter values corresponding to the intersection points.

Example of usage
----------------

Find intersections of some NURBS curve with XOY plane:

.. image:: https://user-images.githubusercontent.com/284644/86529252-b2292900-bec8-11ea-9b85-61d200e8b93d.png
  :target: https://user-images.githubusercontent.com/284644/86529252-b2292900-bec8-11ea-9b85-61d200e8b93d.png

* Vector-> :doc:`Vector sort </nodes/vector/vertices_sort>`
* Curves-> :doc:`Interpolate NURBS Curve </nodes/curve/interpolate_nurbs_curve>`
* Curves-> :doc:`Evaluate Curve </nodes/curve/eval_curve>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Scene-> :doc:`Objects In Lite </nodes/scene/objects_in_lite>`