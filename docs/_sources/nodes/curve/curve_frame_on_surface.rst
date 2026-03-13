Curve Frame on Surface
======================

.. image:: https://user-images.githubusercontent.com/14288520/210639554-d0a9be1f-e0ef-4c9f-b165-2f17dad71e20.png
  :target: https://user-images.githubusercontent.com/14288520/210639554-d0a9be1f-e0ef-4c9f-b165-2f17dad71e20.png

Functionality
-------------

Given a surface and a curve in the surface's U/V space, this node calculates a reference frame of a curve for the given value of curve's T parameter. The frame is calculated so that:

* it's X axis is pointing along surface's normal;
* it's Z axis is pointing along curve's tangent (in 3D space);
* it's Y axis is perpendicular to both X and Z.

This node allows one to place some object at the curve on the surface, while
aligning it both with curve's tangent and surface's normal.

.. image:: https://user-images.githubusercontent.com/14288520/210656324-3e8fdb9f-8654-491b-b305-cf512293a717.png
  :target: https://user-images.githubusercontent.com/14288520/210656324-3e8fdb9f-8654-491b-b305-cf512293a717.png

Inputs
------

This node has the following inputs:

* **Surface**. The surface to put the curve into. This input is mandatory.
* **UVCurve**. The curve to calculate frame for. The curve is supposed to lie
  in XOY plane; X coordinate means U parameter of the surface, and Y coordinate
  means V parameter. This input is mandatory.
* **T**. The value of curve's T parameter. The default value is 0.5.

.. image:: https://user-images.githubusercontent.com/14288520/210652754-f1802ae1-4cab-4761-80fc-eab7a03965b2.png
  :target: https://user-images.githubusercontent.com/14288520/210652754-f1802ae1-4cab-4761-80fc-eab7a03965b2.png

Parameters
----------

This node has the following parameter:

* **Join**. If checked, then the node will output single (concatenated) list of
  matrices for all input curves. Otherwise, it will output separate list of
  matrices per each input curve. Checked by default.

.. image:: https://user-images.githubusercontent.com/14288520/210657860-01c05782-4475-4d65-b6d0-3a22d2fe1bf3.png
  :target: https://user-images.githubusercontent.com/14288520/210657860-01c05782-4475-4d65-b6d0-3a22d2fe1bf3.png

Outputs
-------

This node has the following outputs:

* **Matrix**. The matrix defining the frame for the curve at the specified
  value of T parameter. The location component of the matrix is the point of
  the curve.
* **Tangent**. The direction of curve's tangent vector at the specified value of T parameter.
* **Normal**. The direction of curve's main normal at the specified value of T parameter.
* **Binormal**. The direction of curve's binormal at the specified value of T parameter.

.. image:: https://user-images.githubusercontent.com/14288520/210658893-6fb8a1e6-4913-4d04-8a3d-0d49ea85aa60.png
  :target: https://user-images.githubusercontent.com/14288520/210658893-6fb8a1e6-4913-4d04-8a3d-0d49ea85aa60.png

Examples of usage
-----------------

Let's generate an ellipse by generating a sine wave in U/V space of cylindrical
curve. Then we use "Curve Frame" node to place cubes along that ellipse:

.. image:: https://user-images.githubusercontent.com/284644/89296471-d28d0480-d67b-11ea-9ac0-d6104821ea94.png
  :target: https://user-images.githubusercontent.com/284644/89296471-d28d0480-d67b-11ea-9ac0-d6104821ea94.png

As you can see, the cubes are aligned with a plane where the ellipse lies, but
they are not aligned with the cylinder surface. Now let's use "Curve frame on surface" node instead:

.. image:: https://user-images.githubusercontent.com/284644/89296479-d456c800-d67b-11ea-9409-2f83e9db415b.png
  :target: https://user-images.githubusercontent.com/284644/89296479-d456c800-d67b-11ea-9409-2f83e9db415b.png

**Replay with new nodes**:

https://gist.github.com/c119546943b4ce703d0f55be00cbedbd

.. image:: https://user-images.githubusercontent.com/14288520/210871891-c0228c13-2dc8-472d-ab3d-f806be82aed3.png
  :target: https://user-images.githubusercontent.com/14288520/210871891-c0228c13-2dc8-472d-ab3d-f806be82aed3.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Curves-> :doc:`Circle (Curve) </nodes/curve/curve_circle>`
* Curves-> :doc:`Curve on Surface </nodes/curve/curve_on_surface>`
* Curves-> :doc:`Evaluate Curve </nodes/curve/eval_curve>`
* Curves-> :doc:`Curve Domain </nodes/curve/curve_range>`
* Curves-> :doc:`Curve Frame </nodes/curve/curve_frame>`
* Surfaces-> :doc:`Curve Formula </nodes/curve/curve_formula>`
* Surfaces-> :doc:`Extrude Curve Along Vector </nodes/surface/extrude_vector>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Script-> :doc:`Formula </nodes/script/formula_mk5>`

.. image:: https://user-images.githubusercontent.com/14288520/210870497-8c9108bb-0bfa-41d2-b1b8-fdfad1fc59c3.gif
  :target: https://user-images.githubusercontent.com/14288520/210870497-8c9108bb-0bfa-41d2-b1b8-fdfad1fc59c3.gif

---------

https://gist.github.com/5fdc5d5e6169a86f9356ff461be321d3

.. image:: https://user-images.githubusercontent.com/14288520/210880364-869888dd-9ede-4131-8bc5-473f5624e5b0.png
  :target: https://user-images.githubusercontent.com/14288520/210880364-869888dd-9ede-4131-8bc5-473f5624e5b0.png

* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Curves-> :doc:`Cubic Spline </nodes/curve/cubic_spline>`
* Curves-> :doc:`Evaluate Curve </nodes/curve/eval_curve>`
* Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`
* Surfaces-> :doc:`Surface from Curves </nodes/surface/interpolating_surface>`
* Transform-> :doc:`Move </nodes/transforms/move_mk3>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Mutrix Multiply: Matrix-> :doc:`Matrix Math </nodes/matrix/matrix_math>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Scene-> :doc:`Bezier Input </nodes/exchange/bezier_in>`