Naturally Parametrized Curve
============================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/f5cdafd7-aef1-46bb-8912-5a60a8484c24
  :target: https://github.com/nortikin/sverchok/assets/14288520/f5cdafd7-aef1-46bb-8912-5a60a8484c24

Functionality
-------------

It worth reminding that a Curve object is defined as a function from some set
of T values into some points in 3D space; and, since the function is more or
less arbitrary, the change of T parameter is not always proportional to length
of the path along the curve - in fact, it is rarely proportional. For many
curves, small changes of T parameter can move a point a long way along the
curve in one parts of the curve, and very small way in other parts.

This node takes a Curve object and generates another Curve, which has the same
set of points, but another parametrization - specifically, the natural
parametrization. "Natural parametrization" means that the length of part of
curve from the beginning to some point is equal to the value of curve's T
parameter at that point. This means that with equal changes of curve's T
parameter the point on the curve will always travel the equal distances.

This node is similar to "Curve Length Parameter"; the difference is, this node
outputs the Curve object, so that curve can be used in following nodes that
require a Curve as input.

The curve's length is calculated numerically, by subdividing the curve in many
straight segments and summing their lengths. The more segments you subdivide
the curve in, the more precise the length will be, but the more time it will
take to calculate. So the node gives you control on the number of subdivisions.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/0c168562-e894-4b43-bb81-5769fb1f0f05
  :target: https://github.com/nortikin/sverchok/assets/14288520/0c168562-e894-4b43-bb81-5769fb1f0f05

* Generator-> :doc:`Random Vector </nodes/generator/random_vector_mk3>`
* Curves-> :doc:`Cubic Spline </nodes/curve/cubic_spline>`
* Curves-> :doc:`Curve Domain </nodes/curve/curve_range>`
* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`
* Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`

Inputs
------

This node has the following inputs:

* **Curve**. The curve to be re-parametrized. This input is mandatory.
* **Resolution**. The number of segments to subdivide the curve in to calculate
  the length. The bigger the value, the more precise the calculation will be,
  but the more time it will take. The default value is 50.

Parameters
----------

This node has the following parameter:

* **Interpolation mode**. This defines the interpolation method used for
  calculating of points inside the segments in which the curve is split
  according to **Resolution** parameters. The available values are **Cubic**
  and **Linear**. Cubic methods gives more precision, but takes more time for
  calculations. The default value is **Cubic**. This parameter is available in
  the N panel only.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/5f4c2d9c-c1df-4439-ad83-b1432ac67813
  :target: https://github.com/nortikin/sverchok/assets/14288520/5f4c2d9c-c1df-4439-ad83-b1432ac67813

Outputs
-------

This node has the following output:

* **Curve**. The newly generated curve.

Examples of usage
-----------------

Take an Archimedean spiral with a well-known parametrization; in the center,
small changes of T give very small change of the position of the point on the
curve, while farther from the center, the same changes of T give a lot bigger
steps along the curve. This you can see at the left. At the right there is the
same spiral with natural parametrization:

.. image:: https://user-images.githubusercontent.com/284644/79695949-29202f80-8293-11ea-8623-1df67c3a68ef.png
  :target: https://user-images.githubusercontent.com/284644/79695949-29202f80-8293-11ea-8623-1df67c3a68ef.png

* Curves-> :doc:`Curve Formula </nodes/curve/curve_formula>`
* Curves-> :doc:`Evaluate Curve </nodes/curve/eval_curve>`
* Transform-> :doc:`Move </nodes/transforms/move_mk3>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

Similar example with some cubic spline:

.. image:: https://user-images.githubusercontent.com/284644/79693501-75b03e80-8284-11ea-841b-9b5911bf91e7.png
  :target: https://user-images.githubusercontent.com/284644/79693501-75b03e80-8284-11ea-841b-9b5911bf91e7.png

* Curves-> :doc:`Cubic Spline </nodes/curve/cubic_spline>`
* Curves-> :doc:`Evaluate Curve </nodes/curve/eval_curve>`
* Transform-> :doc:`Move </nodes/transforms/move_mk3>`
* Vector-> :doc:`Vector sort </nodes/vector/vertices_sort>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Scene-> :doc:`Objects In Lite </nodes/scene/objects_in_lite>`