Curve Curvature
===============

.. image:: https://github.com/nortikin/sverchok/assets/14288520/50a1d9b3-0c0a-4b23-b890-a18c0bd1872e
  :target: https://github.com/nortikin/sverchok/assets/14288520/50a1d9b3-0c0a-4b23-b890-a18c0bd1872e

Functionality
-------------

This node calculates curve's curvature_ at certain value of the curve's T
parameter. It can also calculate curve's curvature radius and the center of
osculating circle.

.. _curvature: https://en.wikipedia.org/wiki/Curvature#Space_curves

.. image:: https://github.com/nortikin/sverchok/assets/14288520/157422c9-d794-4a63-82c9-77dd6d954071
  :target: https://github.com/nortikin/sverchok/assets/14288520/157422c9-d794-4a63-82c9-77dd6d954071

* Generator-> :doc:`Segment </nodes/generator/segment>`
* Curves-> :doc:`Evaluate Curve </nodes/curve/eval_curve>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* List->List Struct-> :doc:`List Levels </nodes/list_struct/levels>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Scene-> :doc:`Bezier Input </nodes/exchange/bezier_in>`

Inputs
------

This node has the following inputs:

* **Curve**. The curve to measure curvature for. This input is mandatory.
* **T**. The value of curve's T parameter to measure curvature at. The default value is 0.5.

Parameters
----------

This node does not have parameters.

Outputs
-------

This node has the following outputs:

* **Curvature**. Curvature value.
* **Radius**. Curvature radius value.
* **Center**. This contains the center of osculating circle as well as circle's orientation.

Example of usage
----------------

Calculate and display curvature at several points of some random curve:

.. image:: https://user-images.githubusercontent.com/284644/78502370-470d7080-777a-11ea-9ee7-648946c89ab5.png
  :target: https://user-images.githubusercontent.com/284644/78502370-470d7080-777a-11ea-9ee7-648946c89ab5.png

* Generator-> :doc:`Random Vector </nodes/generator/random_vector_mk3>`
* Curves-> :doc:`Cubic Spline </nodes/curve/cubic_spline>`
* Curves-> :doc:`Curve Domain </nodes/curve/curve_range>`
* Curves-> :doc:`Evaluate Curve </nodes/curve/eval_curve>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Viz-> :doc:`Viewer Index+ </nodes/viz/viewer_idx28>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`