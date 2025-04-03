Curve Torsion
=============

.. image:: https://github.com/nortikin/sverchok/assets/14288520/2d949b9f-af05-46c8-ab24-36375a98ff33
  :target: https://github.com/nortikin/sverchok/assets/14288520/2d949b9f-af05-46c8-ab24-36375a98ff33

Functionality
-------------

This node calculates the torsion_ value of a curve at the certain value of curve's T parameter.

.. _torsion: https://en.wikipedia.org/wiki/Torsion_of_a_curve

.. image:: https://github.com/nortikin/sverchok/assets/14288520/6d9053f3-d98e-4d4a-985b-3066e1d0748d
  :target: https://github.com/nortikin/sverchok/assets/14288520/6d9053f3-d98e-4d4a-985b-3066e1d0748d

* Number-> :doc:`A Number </nodes/number/numbers>`
* Curves-> :doc:`Evaluate Curve </nodes/curve/eval_curve>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`
* Scene-> :doc:`Bezier Input </nodes/exchange/bezier_in>`

Inputs
------

This node has the following inputs:

* **Curve**. The curve to measure torsion for. This input is mandatory.
* **T**. The value of curve's T parameter to measure torsion at. The default value is 0.5.

Parameters
----------

This node does not have parameters.

Outputs
-------

This node has the following output:

* **Torsion**. The torsion value.

Example of usage
----------------

Calculate torsion value at several points of some random curve:

.. image:: https://user-images.githubusercontent.com/284644/78502538-12e67f80-777b-11ea-8ba6-d4d1d6360ce2.png
  :target: https://user-images.githubusercontent.com/284644/78502538-12e67f80-777b-11ea-8ba6-d4d1d6360ce2.png

* Generator-> :doc:`Random Vector </nodes/generator/random_vector_mk3>`
* Curves-> :doc:`Cubic Spline </nodes/curve/cubic_spline>`
* Curves-> :doc:`Curve Domain </nodes/curve/curve_range>`
* Curves-> :doc:`Evaluate Curve </nodes/curve/eval_curve>`
* Viz-> :doc:`Viewer Index+ </nodes/viz/viewer_idx28>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

Note that calculating torsion at end points of a curve, or at some other
singular points of the curve may give unusable results.

