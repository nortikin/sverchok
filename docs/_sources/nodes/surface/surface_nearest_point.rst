Nearest Point on Surface
========================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/aeb96cdd-91d3-4ade-aaef-d0b76e61ae46
  :target: https://github.com/nortikin/sverchok/assets/14288520/aeb96cdd-91d3-4ade-aaef-d0b76e61ae46

Dependencies
------------

This node requires SciPy_ library to work.

.. _SciPy: https://scipy.org/

Functionality
-------------

This node searches for the point on the surface, which is the nearest (the
closest) to the given point.

Note that the search is implemented with a numeric algorithm, so it may be not
very fast. In case you know how to solve this task analytically (with formula)
for your particular surface, that will be much faster. This node, on the other
hand, is usable in cases when you do not know formulas for your surface - for
example, it was received by some approximation.

At the first step of it's algorithm, this node evaluates the surface in points
of a cartesian grid, and selects the closest of them. This point is then used
as an initial guess for the more precise algorithm.

In case there are several points on the surface with equal distance to the
original point, the node will return one of them (it is not guaranteed which
one).

.. image:: https://github.com/nortikin/sverchok/assets/14288520/668eebba-dcbb-456b-9bdd-f825bd686af3
  :target: https://github.com/nortikin/sverchok/assets/14288520/668eebba-dcbb-456b-9bdd-f825bd686af3

Inputs
------

This node has the following inputs:

* **Surface**. The surface to find the nearest point on. This input is mandatory.
* **Point**. The point to search the nearest for. The default value is ``(0, 0, 0)``.

Parameters
----------

This node has the following parameters:

* **Init Resolution**. Number of samples to evaluate the surface in, for the
  initial guess. The higher this value is, the more precise the initial guess
  will be, so the less work for the numeric algorithm. The default value is 10.
  In many simple cases you do not have to change this value.
* **Precise**. If checked, then a numeric algorithm will be used to find exact
  location of the nearest point. Otherwise, the node will return the initial
  guess. So if this parameter is not checked, the **Init Resolution** parameter
  will define the precision of the node. Checked by default.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/010a3bea-e988-4a69-9aee-567e07bd2a7a
      :target: https://github.com/nortikin/sverchok/assets/14288520/010a3bea-e988-4a69-9aee-567e07bd2a7a

* **Method**. This parameter is available in the N panel only. The algorithm
  used to find the nearest point. The available algorithms are:

   * L-BFGS-B
   * Conjugate Gradient
   * Truncated Newton
   * SLSQP -  Sequential Least SQuares Programming algorithm.

   The default option is L-BFGS-B. In simple cases, you do not have to change
   this parameter. In more complex cases, you will have to try all algorithms
   and select the one which fits you the best.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/3c69245a-9e78-405f-a0b6-0784f690c99f
      :target: https://github.com/nortikin/sverchok/assets/14288520/3c69245a-9e78-405f-a0b6-0784f690c99f

* **Sequential**. This parameter is available in the N panel only, and only
  when **Precise** parameter is checked. When checked, the node will use result
  of finding the nearest point from one source point as an initial guess for
  finding the nearest point for the next source point. This approach can give
  better results or better performance in case you are, for example, finding
  nearest points for a series of points generated from one curve. Unchecked by
  default.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/8de6fe38-943e-4d3d-a503-6ac86d852a4b
      :target: https://github.com/nortikin/sverchok/assets/14288520/8de6fe38-943e-4d3d-a503-6ac86d852a4b

Outputs
-------

This node has the following outputs:

* **Point**. The nearest point on the surface, in 3D space.
* **UVPoint**. The point in surface's U/V space, which corresponds to the
  nearest point. Z coordinate of this output is always zero, X and Y correspond
  to U and V.

Example of usage
----------------

.. image:: https://github.com/nortikin/sverchok/assets/14288520/377c8839-91d0-4348-863e-0338310618d4
  :target: https://github.com/nortikin/sverchok/assets/14288520/377c8839-91d0-4348-863e-0338310618d4

* Generator-> :doc:`Segment </nodes/generator/segment>`
* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Surfaces-> :doc:`Minimal Surface </nodes/surface/minimal_surface>`
* Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`
* Transform-> :doc:`Randomize </nodes/transforms/randomize>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://github.com/nortikin/sverchok/assets/14288520/e5e6c83f-7c34-4bff-b2fa-97dcaed59e57
  :target: https://github.com/nortikin/sverchok/assets/14288520/e5e6c83f-7c34-4bff-b2fa-97dcaed59e57

---------

.. image:: https://user-images.githubusercontent.com/284644/87247996-782fc800-c470-11ea-8ccc-e15021b59591.png
  :target: https://user-images.githubusercontent.com/284644/87247996-782fc800-c470-11ea-8ccc-e15021b59591.png

* Curves-> :doc:`Cubic Spline </nodes/curve/cubic_spline>`
* Surfaces-> :doc:`Minimal Surface </nodes/surface/minimal_surface>`
* Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`
* Modifiers->Modifier Make-> :doc:`UV Connection </nodes/modifier_make/uv_connect>`
* Vector-> :doc:`Vector sort </nodes/vector/vertices_sort>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Scene-> :doc:`Objects In Lite </nodes/scene/objects_in_lite>`
