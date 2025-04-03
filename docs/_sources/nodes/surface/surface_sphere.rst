Sphere (Surface)
================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/42b9eb53-0b91-4d62-9ac4-be044b74a717
  :target: https://github.com/nortikin/sverchok/assets/14288520/42b9eb53-0b91-4d62-9ac4-be044b74a717

Functionality
-------------

This node generates a spherical Surface object. Several parametrizations are available:

* Default - corresponding to spherical coordinates formula
* Equirectangular
* Lambert
* Gall Stereographic
* NURBS Sphere

.. image:: https://github.com/nortikin/sverchok/assets/14288520/9bf84f33-7961-4ba1-9249-3254896f1505
  :target: https://github.com/nortikin/sverchok/assets/14288520/9bf84f33-7961-4ba1-9249-3254896f1505

For formulas, please refer to Wikipedia: https://en.wikipedia.org/wiki/List_of_map_projections

Inputs
------

This node has the following inputs:

* **Center**. The center of the sphere. The default value is `(0, 0, 0)` (origin).
* **Radius**. Sphere radius. The default value is 1.0.
* **Theta1**. Theta1 parameter of the Equirectangular projection. This input is only available when the **Projection** parameter is set to **Equirectangular**. The default value is pi/4.

Parameters
----------

This node has the following parameter:

* **Projection**. This defines the parametrization to be used.

Outputs
-------

This node has the following output:

* **Surface**. The generated spherical surface.

Example of usage
----------------

The default parametrization:

.. image:: https://user-images.githubusercontent.com/284644/79351826-93169d00-7f52-11ea-99ad-bb904f62ce6c.png
  :target: https://user-images.githubusercontent.com/284644/79351826-93169d00-7f52-11ea-99ad-bb904f62ce6c.png

* Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`