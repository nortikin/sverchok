Implicit Surface Raycast
========================

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

Inputs
------

This node has the following inputs:

* **Field**. Scalar field, which defines the iso-surface to find the intersection with. This input is mandatory.
* **Vertices**. Source point(s) of the ray(s). The default value is ``(0, 0, 0)``.
* **Direction**. Direction vector of the ray. The default value is ``(0, 0, 1)``.
* **IsoValue**. The value of the scalar field, which defines the iso-surface in question. The default value is 0.

Outputs
-------

This node has the following outputs:

* **Vertices**. Intersection points in 3D space.
* **Distance**. Distance between ray source point and the intersection point.

Example of usage
----------------

.. image:: https://user-images.githubusercontent.com/284644/87581701-d075fc80-c6f2-11ea-9eb6-ab02ba69ef2a.png

