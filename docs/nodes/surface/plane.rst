Plane (Surface)
===============

Functionality
-------------

This node generate a Surface object, which represents a rectangular segment of plane.

Surface domain: defined by node parameters.

Surface parametrization: Point = P0 + u*V1 + v*V1

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

It is possible to generate a plane with non-rectangular parametrization, if three points provided do not make a right angle:

.. image:: https://user-images.githubusercontent.com/284644/78699412-4bbe5a00-791d-11ea-87c9-78c7bbe4ed78.png

