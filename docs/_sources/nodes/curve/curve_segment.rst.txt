Curve Segment
=============

.. image:: https://github.com/nortikin/sverchok/assets/14288520/41fa4386-25c7-4282-8ccc-a776b3b19151
  :target: https://github.com/nortikin/sverchok/assets/14288520/41fa4386-25c7-4282-8ccc-a776b3b19151

Functionality
-------------

This node generates a curve which is defined as a subset of the input curve
with a smaller range of allowed T parameter values. In other words, the output
curve is the same as input one, but with restricted range of T values allowed.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/b0ccc491-4211-4c29-ba6f-011dfa02e282
  :target: https://github.com/nortikin/sverchok/assets/14288520/b0ccc491-4211-4c29-ba6f-011dfa02e282

Output curve domain: defined by node inputs.

Output curve parametrization: the same as of input curve.

Inputs
------

This node has the following inputs:

* **Curve**. The curve to be cut. This input is mandatory.
* **TMin**. The value of curve's T parameter, at which the new curve should start. The default value is 0.2.
* **TMax**. The value of curve's T parameter, at which the new curve should end. The default value is 0.8.

Parameters
----------

This node has the following parameters:

* **Join**. If checked, the node will always output single flat list of curves.
* **NURBS if possible**. If checked, for NURBS and NURBS-like curves, the node
  will calculate a new NURBS curve representing the segment of initial curve.
  If not checked, the node will always return a generic Curve object. Checked
  by default. This parameter is available in the N panel only.
* **Rescale to 0..1**. If checked, then the generated curve will have the
  domain (allowed range of T parameter values)  of `[0.0 .. 1.0]`. Otherwise,
  the domain of generated curve will be defined by node's inputs, i.e. `[TMin
  .. TMax]`. Unchecked by default.

Outputs
-------

This node has the following output:

* **Segment**. The resulting curve segment.

Examples of usage
-----------------

Generate some random curve (green) and take a subset from it with T values from 0.2 to 0.8 (red):

.. image:: https://user-images.githubusercontent.com/284644/78508073-99ac5400-779d-11ea-9a01-1d8824934ae4.png
  :target: https://user-images.githubusercontent.com/284644/78508073-99ac5400-779d-11ea-9a01-1d8824934ae4.png

* Generator-> :doc:`Random Vector </nodes/generator/random_vector_mk3>`
* Curves-> :doc:`Cubic Spline </nodes/curve/cubic_spline>`
* Curves-> :doc:`Evaluate Curve </nodes/curve/eval_curve>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

Generate several segments of the same curve with different ranges of T parameter, to generate a dashed line:

.. image:: https://user-images.githubusercontent.com/284644/78508072-987b2700-779d-11ea-9b53-6490db257aed.png
  :target: https://user-images.githubusercontent.com/284644/78508072-987b2700-779d-11ea-9b53-6490db257aed.png

* Generator-> :doc:`Random Vector </nodes/generator/random_vector_mk3>`
* Curves-> :doc:`Cubic Spline </nodes/curve/cubic_spline>`
* Curves-> :doc:`Curve Domain </nodes/curve/curve_range>`
* Curves-> :doc:`Evaluate Curve </nodes/curve/eval_curve>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Add: Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`