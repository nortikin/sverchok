Implicit Surface Raycast
========================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/c77d08d7-3cf5-40f0-96d9-9a298b180aae
  :target: https://github.com/nortikin/sverchok/assets/14288520/c77d08d7-3cf5-40f0-96d9-9a298b180aae

Dependencies
------------

This node requires SciPy_ library to work.

.. _SciPy: https://scipy.org/

Functionality
-------------

This node implements ray casting_ onto an arbitrary implicit surface; in other words,
given a point in 3D space and ray direction vector, it will find a point where
this ray intersects the given surface first time.

Implicit surface is specified by providing a scalar field and it's value, used to define an iso-surface_.

.. _casting: https://en.wikipedia.org/wiki/Ray_casting
.. _iso-surface: https://en.wikipedia.org/wiki/Level_set

This node uses a numerical method to find the intersection point, so it may be
not very fast. If you happen to know how to find the intersection point for
your specific surface by some formula, that will be faster and more precise.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/81e705a6-0ebd-4b32-836f-e3a0c8fbc3d5
  :target: https://github.com/nortikin/sverchok/assets/14288520/81e705a6-0ebd-4b32-836f-e3a0c8fbc3d5

Inputs
------

This node has the following inputs:

* **Field**. Scalar field, which defines the iso-surface to find the intersection with. This input is mandatory.
* **Vertices**. Source point(s) of the ray(s). The default value is ``(0, 0, 0)``.
* **Direction**. Direction vector of the ray. The default value is ``(0, 0, 1)``.
* **IsoValue**. The value of the scalar field, which defines the iso-surface in question. The default value is 0.

  .. image:: https://github.com/nortikin/sverchok/assets/14288520/792915bc-0726-445d-bf8c-3f6d8e83ba70
    :target: https://github.com/nortikin/sverchok/assets/14288520/792915bc-0726-445d-bf8c-3f6d8e83ba70

Parameters
----------

This node has the following parameters:

* **First solution only**. If checked, the node will output only first
  intersection of the ray with the implicit surface. Otherwise, it will output
  all intersections. Checked by default.
* **N Sections**. To search for intersection, the node subdivides the ray into
  N segments, and checks for intersection in each segment. The number of
  segments defines maximum number of solutions which can be found. The default
  value is 10.
* **On fail**. This parameter is available in the N panel only. This defines what the node should do if the ray does not intersect the surface. The available options are:

  * **Fail**. If any of rays does not intersect surface, the node will fail (become red) and processing will stop.
  * **Skip**. Just do not output anything for such rays.
  * **Return None**. Return None value for such rays.

  The default option is **Fail**.

Outputs
-------

This node has the following outputs:

* **Vertices**. Intersection points in 3D space.
* **Distance**. Distance between ray source point and the intersection point.

Example of usage
----------------

.. image:: https://github.com/nortikin/sverchok/assets/14288520/cf1514ec-f894-4264-8619-64ccc354f7c5
  :target: https://github.com/nortikin/sverchok/assets/14288520/cf1514ec-f894-4264-8619-64ccc354f7c5

* Generator-> :doc:`Segment </nodes/generator/segment>`
* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Fields-> :doc:`Attractor Field </nodes/field/attractor_field_mk2>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Surfaces-> :doc:`Marching Cubes </nodes/surface/marching_cubes>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://github.com/nortikin/sverchok/assets/14288520/dd79a2ff-d011-4d05-89fc-eed0d585eb6e
  :target: https://github.com/nortikin/sverchok/assets/14288520/dd79a2ff-d011-4d05-89fc-eed0d585eb6e

---------

.. image:: https://user-images.githubusercontent.com/284644/87581701-d075fc80-c6f2-11ea-9eb6-ab02ba69ef2a.png
  :target: https://user-images.githubusercontent.com/284644/87581701-d075fc80-c6f2-11ea-9eb6-ab02ba69ef2a.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Curves->Curve Primitives-> :doc:`Ellipse (Curve) </nodes/curve/ellipse_curve>`
* Curves-> :doc:`Evaluate Curve </nodes/curve/eval_curve>`
* Surfaces-> :doc:`Marching Cubes </nodes/surface/marching_cubes>`
* Modifiers->Modifier Make-> :doc:`UV Connection </nodes/modifier_make/uv_connect>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Number-> :doc:`List Input </nodes/number/list_input>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
