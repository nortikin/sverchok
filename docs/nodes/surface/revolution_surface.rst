Revolution Surface
==================

Functionality
-------------

Given a curve, this node generates a surface which is made by revolving
(rotating) this curve along some axis vector. Many surfaces of revolution, such
as spheres, cylinders, cones may be made with this node.

Note that the profile curve does not have to be planar (flat).

Surface domain: in U direction - the same as profile curve; in V direction - defined by node inputs.
Zero (0) value of V corresponds to initial position of the profile curve.

Inputs
------

This node has the following inputs:

* **Profile**. The profile curve, i.e. the curve which is going to be rotated
  to make a surface. This input is mandatory.
* **Point**. A point on the rotation axis. The default value is `(0, 0, 0)`.
* **Direction**. The direction of the rotation axis. The default value is `(0, 0, 1)` (Z axis).
* **AngleFrom**. The minimal value of rotation angle to rotate the curve from;
  i.e. the surface's V parameter minimal value. The default value is 0.0.
* **AngleTo**. The maximum value of rotation angle to rotate the curve to; i.e.
  the surface's V parameter maximum value. The default value is 2*pi (full
  circle).

Parameters
----------

This node has the following parameter:

* **Origin**. This defines where the origin of the generated surface will be,
  i.e. how the surface will be located in space. This does not affect the shape
  of the surface, only it's location. The following options are available:

  * **Global origin**. Origin of the surface will be placed at global origin
    `(0,0,0)`, so the surface will look like it was revolved around an axis
    which goes through the global origin (but actually revolution will be done
    around the specified axis, only the whole surface will be moved to global
    origin).
  * **Revolution axis**. Origin of the surface will be at the origin of
    revolution axis, i.e. at the point which is provided in the **Point**
    input.

  The default value is **Revolution axis**.

Outputs
-------

This node has the following output:

* **Surface**. The generated surface of revolution.

Examples of usage
-----------------

Rotate a line segment around Z axis to make a conical surface:

.. image:: https://user-images.githubusercontent.com/284644/78705373-cdff4c00-7926-11ea-943a-42eaa6ba8241.png

Rotate some cubic spline around X axis:

.. image:: https://user-images.githubusercontent.com/284644/78705377-cf307900-7926-11ea-8d30-9fd707c42ab6.png

