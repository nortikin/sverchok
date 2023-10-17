Catmull-Rom Spline
==================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/90d6160e-18f2-4d97-a2d5-be0b0f8e0ee5
  :target: https://github.com/nortikin/sverchok/assets/14288520/90d6160e-18f2-4d97-a2d5-be0b0f8e0ee5

Functionality
-------------

This node generates a curve defined as Catmull-Rom spline through the specified
set of points. This is a 3rd degree curve. The curve can be closed or not.

Catmull-Rom splines have the following advantages:

* They are widely used in some areas like game design
* They are quite fast to compute
* They go exactly through specified points (i.e. they are interpolating)
* They can be easily converted to Bezier segments or Nurbs curves.
* In some implementations (see below), they allow to control the "degree of
  smoothness" with additional "tension" parameter.

But Catmull-Rom splines also have some disadvantages:

* They have only C1 continuity, i.e. first derivative is continuous, but second is not.
* As consequence, their curvature can change very fast — they can be "very
  curvy" at one points and "almost straight" in others. But this property can
  be useful in some applications, when you want the spline to go almost by
  straight lines, just rounding the corners a bit.

This node supports two variants of Catmull-Rom spline:

* Non-uniform spline (refer to Wikipedia_). In this implementation, each spline
  segment (between two successive points) is assigned with different span of T
  parameter, which is calculated based on distance between points (several
  metrics are supported). This has the effect of the curve being more "curvy"
  in places where control points are far from one another, and more flat where
  control points are near. This usually gives the feeling of curve being more
  "natural".

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/7d0bb73b-9e8e-4518-be7a-0f7e830a4141
      :target: https://github.com/nortikin/sverchok/assets/14288520/7d0bb73b-9e8e-4518-be7a-0f7e830a4141

    * Generator->Generatots Extended-> :doc:`Spiral </nodes/generators_extended/spiral_mk2>`
    * Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
    * Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`

* Uniform spline. In this implementation, each spline segment is assigned with
  equal span of T parameter. As effect, it is possible that the curve will be
  unexpectedly more "curvy" when successive control points are near one
  another. But this implementation has an option to control the degree of curve
  "smoothness" by additional "tension" parameter. It is also possible to
  specify tension value for each curve segment.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/75f64eec-b2dd-4742-aa06-abac69d27243
      :target: https://github.com/nortikin/sverchok/assets/14288520/75f64eec-b2dd-4742-aa06-abac69d27243

    * Generator->Generatots Extended-> :doc:`Spiral </nodes/generators_extended/spiral_mk2>`
    * Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
    * Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`

.. _Wikipedia: https://en.wikipedia.org/wiki/Centripetal_Catmull%E2%80%93Rom_spline 

Inputs
------

This node has the following inputs:

* **Vertices**. The points through which the curve should go. This input is
  mandatory. At least two points are required to build the spline.
* **Tension**. This input is available only when **Spline Type** parameter is
  set to **Uniform (with tension)**. Specifies the tension value of the spline.
  Lesser values of tension mean that the curve will go segments of straight
  lines between points. It is possible to provide a separate value for each
  segment of the curve (i.e. for each pair of successive points). The default
  value is 1.0.

  .. image:: https://github.com/nortikin/sverchok/assets/14288520/d338ff7b-f65a-46e2-8fb8-5646ab1b98eb
    :target: https://github.com/nortikin/sverchok/assets/14288520/d338ff7b-f65a-46e2-8fb8-5646ab1b98eb

Parameters
----------

This node has the following parameters:

* **Cyclic**. Defines whether the curve should be cyclic (closed). Unchecked by default.
* **Spline Type**. Allows to select one of Catmull-Rom spline implementations
  (see descriptions above). The available options are **Non-uniform** and
  **Uniform (with tension)**. The default option is **Non-uniform**.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/d338ff7b-f65a-46e2-8fb8-5646ab1b98eb
      :target: https://github.com/nortikin/sverchok/assets/14288520/d338ff7b-f65a-46e2-8fb8-5646ab1b98eb

* **Metric**. This parameter is available only if **Spline Type** is set to
  **Non-uniform**. Defines the metric used to assign T parameter spans to each
  segment of the curve. The available values are:

   * Manhattan
   * Euclidean
   * Points (just number of points from the beginning)
   * Chebyshev
   * Centripetal (square root of Euclidean distance)
   * X, Y, Z axis - use distance along one of coordinate axis, ignore others.

   Most used options are Euclidean (in this case the spline is called chordal
   Catmull-Rom spline), Centripetal (centripetal Catmull-Rom spline), and
   Points (this makes a uniform spline with tension set to 1). The default
   option is Euclidean.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/06f36f4f-31e8-4c70-8de6-29839e869edd
      :target: https://github.com/nortikin/sverchok/assets/14288520/06f36f4f-31e8-4c70-8de6-29839e869edd

Outputs
-------

This node has the following output:

* **Curve**. The generated curve object.

Examples of Usage
-----------------

Simplest example:

.. image:: https://user-images.githubusercontent.com/284644/210108720-cb3ef5df-1745-4c19-8625-73f74a445c3d.png
  :target: https://user-images.githubusercontent.com/284644/210108720-cb3ef5df-1745-4c19-8625-73f74a445c3d.png

* Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`
* Scene-> :doc:`Get Objects Data </nodes/scene/get_objects_data>`

Uniform (yellow) vs non-uniform (green) spline:

.. image:: https://user-images.githubusercontent.com/284644/210095223-04cb8658-522e-4458-8668-280a810d5b56.png
  :target: https://user-images.githubusercontent.com/284644/210095223-04cb8658-522e-4458-8668-280a810d5b56.png

* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`
* Scene-> :doc:`Get Objects Data </nodes/scene/get_objects_data>`

Non-uniform splines with Euclidean metric (yellow) and with centripetal metric (green):

.. image:: https://user-images.githubusercontent.com/284644/210095289-11843fed-a915-4030-8391-b81735f1375b.png
  :target: https://user-images.githubusercontent.com/284644/210095289-11843fed-a915-4030-8391-b81735f1375b.png

* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`
* Scene-> :doc:`Get Objects Data </nodes/scene/get_objects_data>`

Non-uniform (Euclidean) Catmull-Rom spline (yellow) vs Cubic spline (blue):

.. image:: https://user-images.githubusercontent.com/284644/210095458-840ee62f-36bc-41ec-8f25-728392fdaedf.png
  :target: https://user-images.githubusercontent.com/284644/210095458-840ee62f-36bc-41ec-8f25-728392fdaedf.png

* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`
* Scene-> :doc:`Get Objects Data </nodes/scene/get_objects_data>`

Uniform splines with different tension values: from 0.2 (almost black lines) to 2.0 (white line):

.. image:: https://user-images.githubusercontent.com/284644/210087921-a8cebbca-2235-4d82-9e11-f08794d8227c.png
  :target: https://user-images.githubusercontent.com/284644/210087921-a8cebbca-2235-4d82-9e11-f08794d8227c.png

* Number-> :doc:`Number Range </nodes/number/number_range>`
* Number-> :doc:`Map Range </nodes/number/range_map>`
* Curves-> :doc:`Evaluate Curve </nodes/curve/eval_curve>`
* List->List Struct-> :doc:`List Levels </nodes/list_struct/levels>`
* Color-> :doc:`Color In </nodes/color/color_in_mk1>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Scene-> :doc:`Get Objects Data </nodes/scene/get_objects_data>`

Here the curvature comb is used to illustrate that the curvature of Catmull-Rom
splines can change very fast and sudden:

.. image:: https://user-images.githubusercontent.com/284644/210087923-fc329968-375a-440e-b661-ee107a85e326.png
  :target: https://user-images.githubusercontent.com/284644/210087923-fc329968-375a-440e-b661-ee107a85e326.png

* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`
* Scene-> :doc:`Get Objects Data </nodes/scene/get_objects_data>`

