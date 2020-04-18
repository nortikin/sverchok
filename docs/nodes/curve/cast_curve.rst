Cast Curve
==========

Functionality
-------------

This node generates a Curve object by casting (projecting) another Curve onto one of predefined shapes.

Curve domain: the same as the curve being projected.

Inputs
------

This node has the following inputs:

* **Curve**. Curve to be projected. This input is mandatory.
* **Center**. The meaning of this input depends on **Target form** parameter:

   * for **Plane**, this is a point on the plane;
   * for **Shpere**, this is the center of the sphere;
   * for **Cylinder**, this is a point on cylinder's axis line.

* **Direction**. This parameter is available only when **Target form** parameter is set to **Plane** or **Cylinder**. It's meaning depends on target form:

  * for **Plane**, this is the normal direction of the plane;
  * for **Cyinder**, this is the directing vector of cylinder's axis line.

* **Radius**. This parameter is available only when **Target form** parameter is set to **Sphere** or **Cylinder. It's meaning depends on target form:

  * for **Sphere**, this is the radius of the sphere;
  * for **Cylinder**, this is the radius of the cylinder.

* **Coefficient**. Casting effect coefficient. 0 means no effect, 1.0 means
  output the curve on the target form. Use other values for linear
  interpolation or linear extrapolation. The default value is 1.0.

Parameters
----------

This node has the following parameter:

* **Target form**. The available forms are:

  * **Plane** is defined by **Center** (a point on the plane) and **Direction** (plane normal vector direction).
  * **Sphere** is defined by **Center** of the sphere and **Radius**.
  * **Cylinder** is defined by **Center** (a point on cylinder's axis),
    **Direction** (directing vector of the cylinder's axis) and **Radius** of
    the cylinder.

Outputs
-------

This node has the following output:

* **Curve**. The casted curve.

Example of usage
----------------

A line and the same line casted onto the unit sphere:

.. image:: https://user-images.githubusercontent.com/284644/77565225-ba46f500-6ee5-11ea-95ea-1baa8555d024.png

