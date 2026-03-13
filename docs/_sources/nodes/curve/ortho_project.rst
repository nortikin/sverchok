Ortho Project on Curve
======================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/f1089726-6f12-4343-b350-2a105af2dd07
  :target: https://github.com/nortikin/sverchok/assets/14288520/f1089726-6f12-4343-b350-2a105af2dd07

Dependencies
------------

This node requires SciPy_ library to work.

.. _SciPy: https://scipy.org/

Functionality
-------------

This node finds an orthogonal projection of a point onto a curve, i.e. a point
on a curve, such that the vector connecting the provided point and the point on
curve is perpendicular to the curve.

The node uses a numerical method to find such point, so it may be not very
fast. If you happen to know how to find such point for your specific curve by
formulas, that way will be faster and more precise.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/bb607a8e-ccab-4d15-80e4-94de87d954c9
  :target: https://github.com/nortikin/sverchok/assets/14288520/bb607a8e-ccab-4d15-80e4-94de87d954c9

Inputs
------

This node has the following inputs:

* **Curve**. The curve to find an orthogonal projection at. This input is mandatory.
* **Point**. The point to find an orthogonal projection for. The default value is ``(0, 0, 0)``.

Parameters
----------

This node has the following parameters:

* **Nearest**. If checked, then the node will search for the nearest of
  orthogonal projections if there are several of them. If there are several
  nearest points, the node will return any of them (not guaranteed which one).
  Otherwise, the node will return all orthogonal projections. Checked by default.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/288eb91c-84a1-4d3a-bc31-7fa0134eb356
  :target: https://github.com/nortikin/sverchok/assets/14288520/288eb91c-84a1-4d3a-bc31-7fa0134eb356

* **Init resolution**. This parameter is available only in the N panel. At the
  first stage of the algorithm, the node subdivides the curve in N segments,
  and then searches for orthogonal projection at each of them by a numerical
  method. The more segments you take, the less work will be for numerical
  method, by the more time will it spend at this first step.  The default value
  is 5. In most simple cases, you do not have to change this value.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/15544fc0-0837-4328-8622-6dbc1935b4ae
  :target: https://github.com/nortikin/sverchok/assets/14288520/15544fc0-0837-4328-8622-6dbc1935b4ae

Outputs
-------

This node has the following outputs:

* **Point**. The point on a curve in 3D space.
* **T**. The value of curve's T parameter corresponding to that point.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/c5633d2a-8c7d-47e3-b67e-ce587ddcf795
  :target: https://github.com/nortikin/sverchok/assets/14288520/c5633d2a-8c7d-47e3-b67e-ce587ddcf795

Example of usage
----------------

Take points on a straight line and project them to some curve:

.. image:: https://user-images.githubusercontent.com/284644/87218335-1fc2d280-c36b-11ea-979b-9858a0dd2f10.png
  :target: https://user-images.githubusercontent.com/284644/87218335-1fc2d280-c36b-11ea-979b-9858a0dd2f10.png

* Generator-> :doc:`Segment </nodes/generator/segment>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Vector-> :doc:`Vector sort </nodes/vector/vertices_sort>`
* Curves-> :doc:`RBF Curve </nodes/curve/rbf_curve>`
* Curves-> :doc:`Evaluate Curve </nodes/curve/eval_curve>`
* Modifiers->Modifier Make-> :doc:`UV Connection </nodes/modifier_make/uv_connect>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Scene-> :doc:`Objects In Lite </nodes/scene/objects_in_lite>`


.. image:: https://github.com/nortikin/sverchok/assets/14288520/41b8196e-5a5f-4268-ad5e-e8b142053dfa
  :target: https://github.com/nortikin/sverchok/assets/14288520/41b8196e-5a5f-4268-ad5e-e8b142053dfa

* Generator-> :doc:`Segment </nodes/generator/segment>`
* Transform-> :doc:`Matrix Apply (verts) </nodes/transforms/apply>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Scene-> :doc:`Bezier Input </nodes/exchange/bezier_in>`
* Scene-> :doc:`Get Objects Data </nodes/scene/get_objects_data>`