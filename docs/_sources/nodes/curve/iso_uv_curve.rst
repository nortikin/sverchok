Iso U/V Curve
=============

.. image:: https://github.com/nortikin/sverchok/assets/14288520/92c4575f-f2bd-4632-8843-576f62485bfa
  :target: https://github.com/nortikin/sverchok/assets/14288520/92c4575f-f2bd-4632-8843-576f62485bfa

Functionality
-------------

This node generates a curve on the surface, which is defined by setting either
U or V surface parameter to some fixed value and letting the other parameter
slide along it's domain.

If input surface is a NURBS surface, then the node will try to output NURBS curves.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/f97c1527-e99c-49e1-a2c8-e1c7d0fde3c7
  :target: https://github.com/nortikin/sverchok/assets/14288520/f97c1527-e99c-49e1-a2c8-e1c7d0fde3c7

* Surfaces-> :doc:`Sphere (Surface) </nodes/surface/surface_sphere>`
* Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`


Inputs
------

This node has the following inputs:

* **Surface**. The surface to generate curves on. This input is mandatory.
* **Value**. The value of U or V surface parameter to generate curve at. The default value is 0.5.

Parameters
----------

This node has the following parameter:

* **Join**. If checked, the node will output a single flat list of Curve
  objects for all sets of input parameters. Otherwise, it will output a
  separate list of Curve objects for each set of input parameters. Checked by
  default.

Outputs
-------

This node has the following outputs:

* **UCurve**. The curve obtained by setting the U parameter of the surface to
  **Value** and letting V slide along it's domain. So, this curve is elongated
  along surface's V direction.
* **VCurve**. The curve obtained by setting the V parameter of the surface to
  **Value** and letting U slide along it's domain. So, this curve is elongated
  along surface's U direction.

Example of usage
----------------

Generate some surface and then draw curves along it's V direction:

.. image:: https://user-images.githubusercontent.com/284644/78507210-3a981080-7798-11ea-84b8-d4e6e7d66803.png
  :target: https://user-images.githubusercontent.com/284644/78507210-3a981080-7798-11ea-84b8-d4e6e7d66803.png

* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Generator-> :doc:`Segment </nodes/generator/segment>`
* Curves->Curve Primitives-> :doc:`Polyline </nodes/curve/polyline>`
* Curves-> :doc:`Evaluate Curve </nodes/curve/eval_curve>`
* Surfaces-> :doc:`Surface from Curves </nodes/surface/interpolating_surface>`
* Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`
* Transform-> :doc:`Rotate </nodes/transforms/rotate_mk3>`
* Transform-> :doc:`Matrix Apply (verts) </nodes/transforms/apply>`
* Number-> :doc:`Random Num Gen </nodes/number/random_num_gen>`
* List->List Struct-> :doc:`List Split </nodes/list_struct/split>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`