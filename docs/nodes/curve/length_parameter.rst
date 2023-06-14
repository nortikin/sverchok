Curve Length Parameter
======================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/ba10a009-ea67-492b-a493-1693edf148ce
  :target: https://github.com/nortikin/sverchok/assets/14288520/ba10a009-ea67-492b-a493-1693edf148ce

Functionality
-------------

It worth reminding that a Curve object is defined as a function from some set
of T values into some points in 3D space; and, since the function is more or
less arbitrary, the change of T parameter is not always proportional to length
of the path along the curve - in fact, it is rarely proportional. For many
curves, small changes of T parameter can move a point a long way along the
curve in one parts of the curve, and very small way in other parts.

This node calculates the point on the curve by it's "length parameter" (also
called "natural parameter"); i.e., for given number L, it calculates the point
P on the curve such that the length of curve segment from beginning to P equals
to L.

The node can also calculate many such points at once for evenly spaced values
of L. This way, one can use this node to split the curve into evenly-sized
segments.

The curve's length is calculated numerically, by subdividing the curve in many
straight segments and summing their lengths. The more segments you subdivide
the curve in, the more precise the length will be, but the more time it will
take to calculate. So the node gives you control on the number of subdivisions.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/38407639-d579-44cb-9e09-2404e118e14d
  :target: https://github.com/nortikin/sverchok/assets/14288520/38407639-d579-44cb-9e09-2404e118e14d

* Round-N: Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Index+ </nodes/viz/viewer_idx28>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`
* Scene-> :doc:`Bezier Input </nodes/exchange/bezier_in>`

Inputs
------

This node has the following inputs:

* **Curve**. The curve being measured. This input is mandatory.
* **Resolution**. The number of segments to subdivide the curve in to calculate
  the length. The bigger the value, the more precise the calculation will be,
  but the more time it will take. The default value is 50.
* **Length**. The value of length parameter to evaluate the curve at. The
  default value is 0.5. This input is available only if **Mode** parameter is
  set to **Manual**.
* **Samples**. Number of length parameter values to calculate the curve points
  at. The node will calculate evenly spaced values of the length parameter from
  zero to the full length of the curve. The default value is 50. This input is
  only available if **Mode** parameter is set to **By Count**.
* **SegmentLength**. This input is available only when **Mode** parameter is
  set to **By Length**. This allows to specify the length of each segment. Note
  that since the whole length of the curve is not necessarily an integer
  multiple of segment length, there can be some sort of rounding applied - see
  **Rounding** parameter. The default value is 1.0.

Parameters
----------

This node has the following parameters:

* **Mode**. This defines how the values of length parameter will be provided.
  The available options are:

  * **By Count**. Values of length parameters will be calculated as evenly spaced
    values from zero to the full length of the curve. The number of the values
    is controlled by the **Samples** input.
  * **By Length**. Values of length parameters will be calculated as evenly
    spaced values from zero to the full length of the curve (or a bit less, see
    **Rounding** parameter). The length of each segment will be equal to the
    value of **SegmentLength** input (up to rounding); the number of segment
    will be calculated based on full curve length and segment length.
  * **Manual**. Values of length parameter will be provided in the **Length** input.

  The default value is **By Count**.

* **Rounding**. This parameter is available only when **Mode** parameter is set
  to **By Length**. This defines how actual lengths of curve segments will be
  calculated. The available options are:

   * **Longer Segments**. The node will calculate the number of segments by
     dividing full curve length by specified segment length and rounding this
     value down to nearest smaller integer. So, each segment's length will be a
     bit more than the value specified in the **SegmentLength** input.
   * **Shorter Segments**. The node will calculate the number of segments by
     dividing full curve length by specified segment length and rounding this
     value up to nearest greater integer. So, each segments' length will be a
     bit less than the value specified in the **SegmentLength** input.
   * **Precise (Cut)**. The length of each segment will be set exactly to the
     value specified in the **SegmentLength** parameter. But then, near the end
     of curve, the last segment will be shorter than others - it's length will
     be just what left, i.e. it's length will be equal to remainder from
     dividing full curve length by segment length.

  The default option is **Longer Segments**.

* **Interpolation mode**. This defines the interpolation method used for
  calculating of points inside the segments in which the curve is split
  according to **Resolution** parameters. The available values are **Cubic**
  and **Linear**. Cubic methods gives more precision, but takes more time for
  calculations. The default value is **Cubic**. This parameter is available in
  the N panel only.

Outputs
-------

This node has the following outputs:

* **T**. Values of curve's T parameter which correspond to the specified values
  of length parameter.
* **Vertices**. Calculated points on the curve which correspond to the
  specified values of length parameter.

Example of usage
----------------

Two exemplars of Archimedean spiral:

.. image:: https://user-images.githubusercontent.com/284644/77854328-14f09180-7203-11ea-9192-028621be3d95.png
  :target: https://user-images.githubusercontent.com/284644/77854328-14f09180-7203-11ea-9192-028621be3d95.png

* Curves-> :doc:`Curve Formula </nodes/curve/curve_formula>`
* Modifiers->Modifier Make-> :doc:`UV Connection </nodes/modifier_make/uv_connect>`
* Curves-> :doc:`Evaluate Curve </nodes/curve/eval_curve>`
* Transform-> :doc:`Move </nodes/transforms/move_mk3>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

The one on the left is drawn with points according to evenly-spaced values of T
parameter; the one of the right is drawn with points spread with equal length
of the path between them.

Examples of **By Length** mode usage. For the blue curve, **Longer segments**
rounding is used; for green curve, **Shorter segments** rounding is used; and
for orange curve, **Precise (Cut)** rounding option is used.

.. image:: https://user-images.githubusercontent.com/284644/207919660-9e9c364e-cd99-40c0-aca2-dfb47bebdc0c.png
  :target: https://user-images.githubusercontent.com/284644/207919660-9e9c364e-cd99-40c0-aca2-dfb47bebdc0c.png

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Curves-> :doc:`Interpolate NURBS Curve </nodes/curve/interpolate_nurbs_curve>`
* Transform-> :doc:`Randomize </nodes/transforms/randomize>`
* Transform-> :doc:`Move </nodes/transforms/move_mk3>`
* Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
