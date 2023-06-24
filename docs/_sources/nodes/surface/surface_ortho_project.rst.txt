Orthogonal Project on Surface
=============================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/83c1004d-c510-4195-bdf2-898c77e2804d
  :target: https://github.com/nortikin/sverchok/assets/14288520/83c1004d-c510-4195-bdf2-898c77e2804d

Dependencies
------------

This node requires SciPy_ library to work.

.. _SciPy: https://scipy.org/

Functionality
-------------

This node finds an orthogonal projection of a point onto a surface, i.e. a
point on a surface such that the vector connecting to the provided point and
the point on surface is perpendicular to the surface.

If there are several such points on a surface, the node will return the nearest
of them. If there are several nearest points, the node will return any of them
(not guaranteed which one).

The node uses a numerical method to find such point, so it may be not very
fast. If you happen to know how to find such point for your specific surface by
formulas, that way will be faster and more precise.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/b1d205cf-9adf-4d3a-b8b9-166744c8ae13
  :target: https://github.com/nortikin/sverchok/assets/14288520/b1d205cf-9adf-4d3a-b8b9-166744c8ae13

Inputs
------

This node has the following inputs:

* **Surface**. The surface to find orthogonal projection onto. This input is
  mandatory.
* **Point**. The point to find the orthogonal projection from. The default
  value is ``(0, 0, 0)``.

Parameters
----------

This node has the following parameter:

* **Init Resolution**. This defines the number of samples to use at the first
  stage of algorithm, to find the initial guess. The higher the value is, the
  more precise the initial guess will be, so less work for the numerical
  algorithm; but the more time will this initial step take. In most cases, you
  do not have to change this parameter. The default value is 5.

Outputs
-------

This node has the following outputs:

* **Point**. The orthogonal projection point on a surface, in 3D space.
* **UVPoint**. The point in surface's U/V space, which corresponds to the found
  orthogonal projection point. Z coordinate of this output is always zero. X
  and Y correspond to U and V.

Examples
--------

.. image:: https://github.com/nortikin/sverchok/assets/14288520/1bb7f46d-9577-40ad-9607-b605156c492b
  :target: https://github.com/nortikin/sverchok/assets/14288520/1bb7f46d-9577-40ad-9607-b605156c492b

* Generator-> :doc:`Segment </nodes/generator/segment>`
* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Surfaces-> :doc:`Minimal Surface </nodes/surface/minimal_surface>`
* Surfaces-> :doc:`Surface Frame </nodes/surface/normals>`
* Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`
* Transform-> :doc:`Noise Displace </nodes/transforms/noise_displace>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Matrix Multiply: Matrix-> :doc:`Matrix Math </nodes/matrix/matrix_math>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://github.com/nortikin/sverchok/assets/14288520/aeab6797-b6ba-4ce4-be12-3ab23370f3cd
  :target: https://github.com/nortikin/sverchok/assets/14288520/aeab6797-b6ba-4ce4-be12-3ab23370f3cd