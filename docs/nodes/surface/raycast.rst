Raycast on Surface
==================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/fa62c6eb-b7a2-49ef-bbb4-48c6b890ca29
  :target: https://github.com/nortikin/sverchok/assets/14288520/fa62c6eb-b7a2-49ef-bbb4-48c6b890ca29

Dependencies
------------

This node requires SciPy_ library to work.

.. _SciPy: https://scipy.org/

Functionality
-------------

This node implements ray casting_ onto an arbitrary surface; in other words,
given a point in 3D space and ray direction vector, it will find a point where
this ray intersects the given surface first time.

.. _casting: https://en.wikipedia.org/wiki/Ray_casting

This node uses a numerical method to find the intersection point, so it may be
not very fast. If you happen to know how to find the intersection point for
your specific surface by some formula, that will be faster and more precise.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/d586f26e-d0d2-4811-965a-8c0f329bfd61
  :target: https://github.com/nortikin/sverchok/assets/14288520/d586f26e-d0d2-4811-965a-8c0f329bfd61

Inputs
------

This node has the following inputs:

* **Surface**. The surface to find intersection with. This input is mandatory.
* **Source**. Source point of the ray. The default value is ``(0, 0, 1)``.
* **Point**. The second point through which the ray goes. This input is
  available only when **Project** parameter is set to **From Source**.
* **Direction**. Ray direction. The default value is ``(0, 0, -1)``. This input
  is available only when **Project** parameter is set to **Along Direction**.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/7c958109-abca-4570-a8ac-be9ee9445892
      :target: https://github.com/nortikin/sverchok/assets/14288520/7c958109-abca-4570-a8ac-be9ee9445892

Parameters
----------

This node has the following parameters:

* **Project**. This defines how the direction of the ray is specified. The available options are:

  * **Along Direction**. Ray is specified by defining it's source point in
    **Source** input, and it's direction vector in **Direction** input.

      .. image:: https://github.com/nortikin/sverchok/assets/14288520/04c75833-06f6-497a-9e99-9de8ca5416ac
        :target: https://github.com/nortikin/sverchok/assets/14288520/04c75833-06f6-497a-9e99-9de8ca5416ac

  * **From Source**. Ray is specified by defining it's source point in
    **Source** input, and a second point on the same ray in **Point** input.

      .. image:: https://github.com/nortikin/sverchok/assets/14288520/97719a38-f5c9-4979-b87d-ec579d1471b7
        :target: https://github.com/nortikin/sverchok/assets/14288520/97719a38-f5c9-4979-b87d-ec579d1471b7

  The default option is **Along Direction**.

* **Precise**. If checked, then the node will calculate precise intersection
  point with a numerical algorithm. Otherwise, it will return "initial guess"
  point, calculated by use of Blender's "BVH raycasting" method. In this case,
  **Samples** parameter defines the precision of calculation. Checked by
  default.
* **Samples**. This parameter is available in the N panel only, if **Precise**
  parameter is checked. To find the "initial guess" point for numerical method,
  this node evaluates the surface in points of cartesian grid, and uses
  Blender's "BVH raycast" method. This input defines the number of samples for
  this first step. The higher this number is, the more precise the initial
  guess is, so the less work for numeric method; but the more time will this
  first step take. In most cases, you do not have to change this parameter. The
  default value is 10.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/7f1f5ee9-2390-43a8-a061-e364b1f86cf4
      :target: https://github.com/nortikin/sverchok/assets/14288520/7f1f5ee9-2390-43a8-a061-e364b1f86cf4

* **Method**. This parameter is available in the N panel only. Type of numeric
  method to be used. The available options are:

   * **Hybrd & Hybrj**. Use MINPACK’s hybrd and hybrj routines (modified Powell method).
   * **Levenberg-Marquardt**. Levenberg-Marquardt algorithm.
   * **Krylov**. Krylov algorithm.
   * **Broyden 1**. Broyden1 algorithm.
   * **Broyden 2**. Broyden2 algorithm.
   * **Anderson**. Anderson algorithm.
   * **DF-SANE**. DF-SANE method.

   The default option is **Hybrd & Hybrj**. In simple cases, you do not
   have to change this parameter. In more complex cases, you will have to try
   all of them and decide which one fits you better.

Outputs
-------

This node has the following outputs:

* **Point**. The intersection point in 3D space.
* **UVPoint**. The point in surface's U/V space, corresponding to the intersection point.

Example of usage
----------------

Along Direction (Parallel):

.. image:: https://github.com/nortikin/sverchok/assets/14288520/a5223515-5df5-449f-8d72-62e30cb340f5
  :target: https://github.com/nortikin/sverchok/assets/14288520/a5223515-5df5-449f-8d72-62e30cb340f5

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Generator-> :doc:`Segment </nodes/generator/segment>`
* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Surfaces-> :doc:`Minimal Surface </nodes/surface/minimal_surface>`
* Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`
* Transform-> :doc:`Noise Displace </nodes/transforms/noise_displace>`
* Vector-> :doc:`Vector Polar Input </nodes/vector/vector_polar_in>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://github.com/nortikin/sverchok/assets/14288520/9be76fe3-d9a0-4b1f-ae42-0b73b0a67174
  :target: https://github.com/nortikin/sverchok/assets/14288520/9be76fe3-d9a0-4b1f-ae42-0b73b0a67174

--------

From Source (Conic):

.. image:: https://github.com/nortikin/sverchok/assets/14288520/c22f6d04-501a-4bd8-a5c5-32677826fa43
  :target: https://github.com/nortikin/sverchok/assets/14288520/c22f6d04-501a-4bd8-a5c5-32677826fa43

* Generator-> :doc:`Segment </nodes/generator/segment>`
* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Surfaces-> :doc:`Minimal Surface </nodes/surface/minimal_surface>`
* Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`
* Transform-> :doc:`Noise Displace </nodes/transforms/noise_displace>`
* Vector-> :doc:`Vector Polar Input </nodes/vector/vector_polar_in>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://github.com/nortikin/sverchok/assets/14288520/67cf4338-8a9a-4853-9a81-8b1bec1b77df
  :target: https://github.com/nortikin/sverchok/assets/14288520/67cf4338-8a9a-4853-9a81-8b1bec1b77df

--------

.. image:: https://user-images.githubusercontent.com/284644/87579479-69a31400-c6ef-11ea-9996-2675af3f6106.png
  :target: https://user-images.githubusercontent.com/284644/87579479-69a31400-c6ef-11ea-9996-2675af3f6106.png

* Curves-> :doc:`Rounded Rectangle </nodes/curve/rounded_rectangle>`
* Curves->Curve Primitives-> :doc:`Ellipse (Curve) </nodes/curve/ellipse_curve>`
* Curves-> :doc:`Evaluate Curve </nodes/curve/eval_curve>`
* Surfaces-> :doc:`Extrude Curve Along Vector </nodes/surface/extrude_vector>`
* Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`
* Modifiers->Modifier Make-> :doc:`UV Connection </nodes/modifier_make/uv_connect>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

Note that in this case we set **Method** parameter to **Krylov**.

