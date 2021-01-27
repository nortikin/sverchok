Raycast on Surface
==================

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

Inputs
------

This node has the following inputs:

* **Surface**. The surface to find intersection with. This input is mandatory.
* **Source**. Source point of the ray. The default value is ``(0, 0, 1)``.
* **Point**. The second point through which the ray goes. This input is
  available only when **Project** parameter is set to **From Source**.
* **Direction**. Ray direction. The default value is ``(0, 0, -1)``. This input
  is available only when **Project** parameter is set to **Along Direction**.

Parameters
----------

This node has the following parameters:

* **Project**. This defines how the direction of the ray is specified. The available options are:

  * **Along Direction**. Ray is specified by defining it's source point in
    **Source** input, and it's direction vector in **Direction** input.
  * **From Source**. Ray is specified by defining it's source point in
    **Source** input, and a second point on the same ray in **Point** input.

  The default option is **Along Direction**.

* **Precise**. If checked, then the node will calculate precise intersection
  point with a numerical algorithm. Otherwise, it will return "initial guess"
  point, calculated by use of Blender's "BVH raycasting" method. In this case,
  **Samples** parameter defines the precision of calculation. Checked by
  default.
* **Samples**. This parameter is available in the N panel only, if **Precise**
  parameter is checked. To find the "initial guess" point for numerical method,
  this node evaluates the surface in points of carthesian grid, and uses
  Blender's "BVH raycast" method. This input defines the number of samples for
  this first step. The higher this number is, the more precise the initial
  guess is, so the less work for numeric method; but the more time will this
  first step take. In most cases, you do not have to change this parameter. The
  default value is 10.
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

.. image:: https://user-images.githubusercontent.com/284644/87579479-69a31400-c6ef-11ea-9996-2675af3f6106.png

Note that in this case we set **Method** paramter to **Krylov**.

