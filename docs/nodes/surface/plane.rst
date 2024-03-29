Plane (Surface)
===============

.. image:: https://github.com/nortikin/sverchok/assets/14288520/5e68195f-9b2b-4ac5-abb7-3c9a2ba892fe
  :target: https://github.com/nortikin/sverchok/assets/14288520/5e68195f-9b2b-4ac5-abb7-3c9a2ba892fe

Functionality
-------------

This node generate a Surface object, which represents a rectangular segment of plane.

Surface domain: defined by node parameters.

Surface parametrization: Point = P0 + u*V1 + v*V1

.. image:: https://github.com/nortikin/sverchok/assets/14288520/dd23c606-d6c0-4f7e-92e7-84c9f3f09a8b
  :target: https://github.com/nortikin/sverchok/assets/14288520/dd23c606-d6c0-4f7e-92e7-84c9f3f09a8b

* Generator-> :doc:`Segment </nodes/generator/segment>`
* Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`
* Vector-> :doc:`Vector Polar Input </nodes/vector/vector_polar_in>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://github.com/nortikin/sverchok/assets/14288520/2edde6f8-9bfb-4e35-8bc2-d5fc2ef209ad
  :target: https://github.com/nortikin/sverchok/assets/14288520/2edde6f8-9bfb-4e35-8bc2-d5fc2ef209ad

Inputs
------

This node has the following inputs:

* **Point1**. The first point on the plane. This point will correspond to U = 0 and V = 0. The default value is `(0, 0, 0)`.
* **Point2**. The second point on the plane. This point will correspond to U =
  1 and V = 0. This input is only available when **Mode** parameter is set to
  **Three points**. The default value is `(1, 0, 0)`.
* **Point3**. The third point on the plane. This point will correspond to U = 0
  and V = 1. This input is only available when **Mode** parameter is set to
  **Three points**. The default value is `(0, 1, 0)`.
* **Normal**. The normal direction of the plane. This input is only available
  when **Mode** parameter is set to **Point and normal**. The default value is
  `(0, 0, 1)`.
* **U Min**, **U Max**. Minimum and maximum values of surface's U parameter.
  Default values are 0 and 1.
* **V Min**, **V Max**. Minimum and maximum values of surface's V parameter.
  Default values are 0 and 1.

Parameters
----------

This node has the following parameter:

* **Mode**. This determines how the plane is specified. The available options are:

  * **Three points**
  * **Point and normal**

Outputs
-------

This node has the following output:

* **Surface**. The Surface object of the plane.

Examples of usage
-----------------

Default settings:

.. image:: https://user-images.githubusercontent.com/284644/78699409-4b25c380-791d-11ea-8671-2b304e108ed1.png
  :target: https://user-images.githubusercontent.com/284644/78699409-4b25c380-791d-11ea-8671-2b304e108ed1.png

* Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

It is possible to generate a plane with non-rectangular parametrization, if three points provided do not make a right angle:

.. image:: https://user-images.githubusercontent.com/284644/78699412-4bbe5a00-791d-11ea-87c9-78c7bbe4ed78.png
  :target: https://user-images.githubusercontent.com/284644/78699412-4bbe5a00-791d-11ea-87c9-78c7bbe4ed78.png

* Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
