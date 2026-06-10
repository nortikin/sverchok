Optimal Bezier Spline
=====================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/TODO-optimal-bezier-spline
  :target: https://github.com/nortikin/sverchok/assets/14288520/TODO-optimal-bezier-spline

Functionality
-------------

This node generates a **C2-continuous cubic Bezier spline** through the
specified set of interpolation points. The spline is built as a sequence of
cubic Bezier segments with continuous first and second derivatives at all
joints, meaning the curvature changes smoothly along the entire curve without
sudden jumps.

The node implements the algorithm from V.V. Borisenko,
*"Construction of Optimal Bezier Spline"* (2017)_. The core idea is to compute
Bezier control points by solving a linear system, then optimize the
parameterization (segment time allocation) to minimize the **bending energy**
integral ∫|B''(t)|² — a standard measure of curve smoothness.

.. _2017: https://www.mathnet.ru/php/getFT.phtml?jrnid=kvant&paperid=4965&what=fullt&option=1

Properties of the optimal spline
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The optimal Bezier spline has the following properties:

* **C2 continuity** — both first and second derivatives are continuous at every
  interpolation node. This means the curvature function is continuous — the
  curve has no "kinks" in its bending behavior. This is a stronger guarantee
  than C1 continuity (where only the first derivative is continuous).

* **Interpolating** — the curve passes exactly through all input points.

* **Energy-minimized** — in the optimal mode, the spline minimizes the integral
  of the squared second derivative ∫|B''(t)|² over all possible parameterizations
  with Σ t_i = 1, t_i > 0. This is the standard "bending energy" functional from
  spline theory. Minimizing it produces the smoothest possible curve for the
  given set of points.

* **Native Bezier representation** — the output is a standard cubic Bezier curve
  (or a concatenation of Bezier segments), which can be used directly with any
  Bezier-aware tool or converted to NURBS.

* **Three parameterization strategies** — the node supports uniform, chord-length,
  and optimal (energy-minimized) parameterization, allowing a trade-off between
  computation speed and visual quality.

Comparison with Catmull-Rom spline
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :doc:`Catmull-Rom spline </nodes/curve/catmull_rom>` is another popular
interpolating spline. Here is how the optimal Bezier spline compares:

* **Continuity**: Catmull-Rom splines have only **C1 continuity** — the first
  derivative is continuous, but the second derivative (and thus curvature) can
  have discontinuities at the interpolation nodes. The optimal Bezier spline has
  **C2 continuity**, meaning curvature changes smoothly everywhere. This makes
  the optimal Bezier spline visually smoother, especially near sharp turns.

* **Curvature behavior**: Because Catmull-Rom splines lack C2 continuity, their
  curvature can change very rapidly — the curve can be "very curvy" at some
  points and "almost straight" at others, with sudden transitions. The optimal
  Bezier spline avoids such abrupt curvature changes.

* **Control**: Catmull-Rom splines (in uniform mode) support a **tension**
  parameter that allows controlling how closely the curve follows the polyline.
  The optimal Bezier spline does not have a tension parameter; instead, it offers
  different parameterization strategies. The chord-length mode provides a similar
  effect to moderate tension.

* **Performance**: Catmull-Rom splines are faster to compute (each segment is
  independent). The optimal Bezier spline requires solving a linear system and,
  in optimal mode, running an optimization loop. However, for typical point
  counts (up to ~100 points), the computation is still fast (under 2 seconds).

* **Use cases**: Catmull-Rom splines are widely used in game design and animation
  where C1 continuity is sufficient and speed matters. The optimal Bezier spline
  is better suited for applications requiring high visual quality: organic shapes,
  tool paths, motion paths, and any scenario where smooth curvature is important.

Comparison with Hobby spline
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :doc:`Hobby spline </nodes/curve/hobby_spline>` is based on John Hobby's
algorithm from MetaPost, designed for producing visually smooth curves in
technical illustrations. Here is how the optimal Bezier spline compares:

* **Continuity**: Hobby splines have **G1 continuity** (tangent direction is
  continuous at every knot). The optimal Bezier spline has **C2 continuity**,
  which is a strictly stronger condition — it guarantees not just smooth tangent
  direction, but also smooth curvature.

* **Algorithmic approach**: Hobby splines use a **mock curvature** heuristic —
  a clever approximation that produces visually pleasing curves without requiring
  full C2 continuity. The optimal Bezier spline minimizes the **actual bending
  energy** integral ∫|B''(t)|², providing a mathematically rigorous optimality
  criterion.

* **Parameters**: Hobby splines support **tension** and **curl** parameters for
  fine control over the curve shape, especially at endpoints. The optimal Bezier
  spline does not have endpoint curl control, but offers three parameterization
  strategies (uniform, chord-length, optimal) that affect the overall shape.

* **3D support**: Hobby splines handle 3D by treating each triple of consecutive
  points as defining a local plane. The optimal Bezier spline works natively in
  3D space through its linear system formulation.

* **Use cases**: Hobby splines are the standard in technical illustration tools
  (MetaPost, TikZ, Asymptote) where visual quality matters and fine control over
  endpoints is needed. The optimal Bezier spline is better when mathematical
  smoothness (C2 continuity) is required, such as in CNC tool paths, animation
  paths, or organic modeling.

Parameterization strategies
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The shape of the spline depends critically on how the parameter ``t`` is
distributed among segments. The node offers three strategies:

* **Points (uniform)**. Each spline segment receives equal time span (all
  ``t_i`` are equal). This is the fastest option and works well when distances
  between consecutive points are approximately equal. When point spacing varies
  significantly, the resulting spline may exhibit unexpected oscillations —
  sharp turns near closely-spaced points and overly stretched curves between
  distant points.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/TODO-uniform-parameterization
      :target: https://github.com/nortikin/sverchok/assets/14288520/TODO-uniform-parameterization

* **Distance (chord-length)**. Segment time spans are proportional to Euclidean
  distances between consecutive points. Longer segments get more "time", which
  produces a more natural appearance. The curve bends more on long segments and
  turns more gently near closely-spaced points. This is the standard approach
  used in many spline implementations.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/TODO-chord-parameterization
      :target: https://github.com/nortikin/sverchok/assets/14288520/TODO-chord-parameterization

* **Optimal (energy-minimized)**. Uses numerical optimization to find the
  parameterization that minimizes the bending energy integral ∫|B''(t)|².
  Starting from chord-length parameterization, the optimizer searches over the
  simplex Σ t_i = 1, t_i > 0 to find the global minimum. This typically reduces
  bending energy by 5-15% compared to chord-length parameterization. The
  optimization converges in roughly 65-85 iterations for most inputs, independent
  of the number of points.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/TODO-optimal-parameterization
      :target: https://github.com/nortikin/sverchok/assets/14288520/TODO-optimal-parameterization

    * Generator->Generators Extended-> :doc:`Spiral </nodes/generators_extended/spiral_mk2>`
    * Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`

Closed (cyclic) splines
~~~~~~~~~~~~~~~~~~~~~~~

The node supports **cyclic (closed) splines**, where the last segment wraps from
the final point back to the first, with full C2 continuity at the wrap-around
joint. For closed splines, no boundary conditions are needed — continuity
equations apply at every node, including the join.

Advantages and disadvantages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Advantages of C2 Bezier splines:

* **C2 continuity** — curvature changes smoothly without sudden jumps.
* **Interpolating** — the curve passes exactly through all specified points.
* **Optimal parameterization** — the energy-minimized mode produces the
  smoothest possible spline for the given set of points.
* **Native Bezier representation** — standard Bezier curves compatible with
  any Bezier-aware tool.

Disadvantages:

* **Slower computation** — especially for the optimal mode, which requires
  iterative optimization. For 100 points, expect 1-2 seconds of computation.
* **Minimum points** — at least 2 points are required for open splines,
  at least 3 for closed splines.
* **No tension control** — unlike Catmull-Rom or Hobby splines, there is no
  tension parameter. Use chord-length parameterization for a similar effect.

Inputs
------

This node has the following inputs:

* **Vertices**. The points through which the curve should pass. This input is
  mandatory. At least two points are required for open splines, at least three
  for closed splines. Supports multi-level nesting for generating multiple
  curves from a single node.

* **Epsilon**. Convergence tolerance for the optimization. Available only when
  **Metric** is set to **Optimal** and **Advanced** settings are shown. Smaller
  values produce more accurate results but require more iterations. Default
  value is 1e-8.

* **Max Iterations**. Maximum number of optimization iterations. Available only
  when **Metric** is set to **Optimal** and **Advanced** settings are shown.
  The optimization typically converges well before this limit (usually 65-85
  iterations). Default value is 1000.

* **Delta**. Initial step parameter for the optimization search. Available only
  when **Metric** is set to **Optimal** and **Advanced** settings are shown.
  Controls the initial search step size. Default value is 0.01.

* **Acceleration**. Step-size acceleration factor for the optimization. Available
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
   * **Optimal (energy-minimized)** — numerical minimization of bending energy.

   The default option is **Optimal (energy-minimized)**.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/TODO-metric-selection
      :target: https://github.com/nortikin/sverchok/assets/14288520/TODO-metric-selection

* **Cyclic**. Defines whether the curve should be cyclic (closed). When
  checked, the last segment connects the final point back to the first point,
  with full C2 continuity at the join. Unchecked by default.

* **Optimization** (expandable section). Shows advanced parameters for the
  optimizer when **Metric** is set to **Optimal**. Contains:

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
