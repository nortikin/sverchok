Optimal Bezier Spline
=====================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/TODO-optimal-bezier-spline
  :target: https://github.com/nortikin/sverchok/assets/14288520/TODO-optimal-bezier-spline

Functionality
-------------

This node generates a C2-continuous cubic Bezier spline through the specified
set of interpolation points. The spline is built as a sequence of cubic Bezier
segments with continuous first and second derivatives at all joints.

Unlike Catmull-Rom splines (which have only C1 continuity), this spline
guarantees C2 continuity — the curvature changes smoothly along the entire
curve. This makes it ideal for applications where smooth motion paths, tool
paths, or organic shapes are required.

The node implements the algorithm from V.V. Borisenko,
"Construction of Optimal Bezier Spline" (2017), which provides three
parameterization strategies:

* **Points (uniform)**. Each spline segment receives equal time span. This is
  the fastest option and works well when distances between consecutive points
  are approximately equal. The resulting spline may exhibit unexpected
  oscillations when point spacing varies significantly.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/TODO-uniform-parameterization
      :target: https://github.com/nortikin/sverchok/assets/14288520/TODO-uniform-parameterization

    * Generator->Generators Extended-> :doc:`Spiral </nodes/generators_extended/spiral_mk2>`
    * Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`

* **Distance (chord-length)**. Segment time spans are proportional to Euclidean
  distances between consecutive points. This produces smoother curves than
  uniform parameterization when node spacing varies. The curve spends more
  "time" traversing longer segments, which gives a more natural appearance.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/TODO-chord-parameterization
      :target: https://github.com/nortikin/sverchok/assets/14288520/TODO-chord-parameterization

    * Generator->Generators Extended-> :doc:`Spiral </nodes/generators_extended/spiral_mk2>`
    * Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`

* **Optimal (energy-minimized)**. Uses hill-descent optimization to minimize
  the bending energy integral ∫|B''(t)|² over all possible parameterizations
  with Σ t_i = 1, t_i > 0. This typically reduces bending energy by 5-15%
  compared to chord-length parameterization. The optimization converges in
  roughly 65-85 iterations for most inputs.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/TODO-optimal-parameterization
      :target: https://github.com/nortikin/sverchok/assets/14288520/TODO-optimal-parameterization

    * Generator->Generators Extended-> :doc:`Spiral </nodes/generators_extended/spiral_mk2>`
    * Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`

The node also supports **cyclic (closed) splines**, where the last segment
wraps from the final point back to the first, with full C2 continuity at the
wrap-around joint.

Advantages of C2 Bezier splines:

* **C2 continuity** — both first and second derivatives are continuous,
  meaning curvature changes smoothly without sudden jumps.
* **Interpolating** — the curve passes exactly through all specified points.
* **Optimal parameterization** — the energy-minimized mode produces the
  smoothest possible spline for the given set of points.
* **Native Bezier representation** — the output is a standard Bezier curve
  that can be used with any Bezier-aware tool or converted to NURBS.

Disadvantages:

* **Slower computation** — especially for the optimal mode, which requires
  iterative optimization. For 100 points, expect 1-2 seconds of computation.
* **Minimum points** — at least 2 points are required for open splines,
  at least 3 for closed splines.

Inputs
------

This node has the following inputs:

* **Vertices**. The points through which the curve should pass. This input is
  mandatory. At least two points are required for open splines, at least three
  for closed splines. Supports multi-level nesting for generating multiple
  curves from a single node.

* **Epsilon**. Convergence tolerance for the hill-descent optimization.
  Available only when **Metric** is set to **Optimal** and **Advanced**
  settings are shown. Smaller values produce more accurate results but require
  more iterations. Default value is 1e-8.

* **Max Iterations**. Maximum number of hill-descent iterations. Available
  only when **Metric** is set to **Optimal** and **Advanced** settings are
  shown. The optimization typically converges well before this limit. Default
  value is 1000.

* **Delta**. Initial step parameter for hill-descent. Available only when
  **Metric** is set to **Optimal** and **Advanced** settings are shown.
  Controls the initial search step size. Default value is 0.01.

* **Acceleration**. Step-size acceleration factor for hill-descent. Available
  only when **Metric** is set to **Optimal** and **Advanced** settings are
  shown. Larger values speed up convergence but may overshoot the optimum.
  Default value is 1.2.

Parameters
----------

This node has the following parameters:

* **Metric**. Defines the parameterization strategy used to assign time spans
  to each spline segment. The available options are:

   * **Points (uniform)** — all segments receive equal time.
   * **Distance (chord-length)** — segment times proportional to point distances.
   * **Optimal (energy-minimized)** — hill-descent minimization of bending energy.

   The default option is **Optimal (energy-minimized)**.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/TODO-metric-selection
      :target: https://github.com/nortikin/sverchok/assets/14288520/TODO-metric-selection

* **Cyclic**. Defines whether the curve should be cyclic (closed). When
  checked, the last segment connects the final point back to the first point,
  with full C2 continuity at the join. Unchecked by default.

* **Optimization** (expandable section). Shows advanced parameters for the
  hill-descent optimizer when **Metric** is set to **Optimal**. Contains:

   * **Epsilon** — convergence tolerance (default 1e-8)
   * **Max Iter** — maximum iterations (default 1000)
   * **Delta** — initial step parameter (default 0.01)
   * **Accel** — acceleration factor (default 1.2)

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/TODO-advanced-settings
      :target: https://github.com/nortikin/sverchok/assets/14288520/TODO-advanced-settings

Outputs
-------

This node has the following outputs:

* **Curve**. The generated C2-continuous Bezier spline curve object.

* **ControlPoints**. The control points of the Bezier spline segments.
  Useful for visualization, analysis, or further processing. The output is
  structured as a list of control point arrays, one per curve.

* **Segments**. The number of Bezier segments in the spline. For open splines,
  this equals N-1 where N is the number of input vertices. For closed splines,
  this equals N.

Examples of Usage
-----------------

Simplest example — open spline through scattered points with optimal parameterization:

.. image:: https://user-images.githubusercontent.com/TODO/optimal-bezier-simple
  :target: https://user-images.githubusercontent.com/TODO/optimal-bezier-simple

* Generator->Generators Extended-> :doc:`Spiral </nodes/generators_extended/spiral_mk2>`
* Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`

Comparing three parameterization modes on the same set of points:

.. image:: https://user-images.githubusercontent.com/TODO/optimal-bezier-metrics-comparison
  :target: https://user-images.githubusercontent.com/TODO/optimal-bezier-metrics-comparison

* Points (uniform) — yellow curve
* Distance (chord-length) — green curve
* Optimal (energy-minimized) — blue curve

* Generator->Generators Extended-> :doc:`Spiral </nodes/generators_extended/spiral_mk2>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`

Closed (cyclic) spline through points on a circle:

.. image:: https://user-images.githubusercontent.com/TODO/optimal-bezier-closed
  :target: https://user-images.githubusercontent.com/TODO/optimal-bezier-closed

* Generator->Generators Extended-> :doc:`Spiral </nodes/generators_extended/spiral_mk2>`
* Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`

Multiple splines with different metrics from nested vertex data:

.. image:: https://user-images.githubusercontent.com/TODO/optimal-bezier-multiple
  :target: https://user-images.githubusercontent.com/TODO/optimal-bezier-multiple

* List->List Struct-> :doc:`List Levels </nodes/list_struct/levels>`
* Generator->Generators Extended-> :doc:`Spiral </nodes/generators_extended/spiral_mk2>`
* Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`

Using control points output for visualization:

.. image:: https://user-images.githubusercontent.com/TODO/optimal-bezier-control-points
  :target: https://user-images.githubusercontent.com/TODO/optimal-bezier-control-points

* Curves-> :doc:`Optimal Bezier Spline </nodes/curve/optimal_bezier>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`
