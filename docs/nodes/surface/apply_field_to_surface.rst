Apply Field to Surface
======================

Functionality
-------------

This node generates a Surface by applying some vector field to another Surface.
More precisely, it generates the surface, points of which are calculated as `X
+ K * VF(X)`, where X is the point of initial surface, VF is the vector field,
  and K is some coefficient.

Optionally, for NURBS and NURBS-like surfaces, this node can apply a Vector
Fields to control points of NURBS surface, instead of applying to all points of
the surface. If this mode is enabled, then output curve will be always a NURBS curve.

Note that mathematically, for NURBS surfaces, if you apply an affine
transformation (such as translation, scale, rotation - i.e. vector field
defined by a Matrix) to control points of a NURBS surface, you will have a surface
of exactly the same shape, but translated / scaled / rotated according to the
transformation. For any more complex transformation (attractor field, for
example), the resulting surface will have different shape; and also it will be
different from a surface that you would receive if you applied the vector field
to all points of the surface instead.

Surface domain: the same as of initial surface.

Inputs
------

This node has the following inputs:

* **Field**. Vector field to apply. This input is mandatory.
* **Surface**. The surface to apply the vector field to. This input is mandatory.
* **Coefficient**. The "strength" coefficient. Value of 0 will output the
  surface as it was. The default value is 1.0.

Parameters
----------

This node has the following parameter:

* **Use Control Points**. If checked, then the vector field will be applied to
  control points of a NURBS surface, instead of applying it to all points of the
  surface. This node will fail (become red) if this mode is enabled, but input
  surface is not a NURBS and can not be presented as a NURBS. If not checked,
  then the node will apply the vector field to all points of the surface; in
  such a case, it can process any type of surface. Disabled by default.
* **By Normal**. This defines whether the field application will be affected by
  surface's normals. The available options are:

  * **As Is**. Do not consider surface's normals, just apply the field as it
    is. This is the default option.
  * **Along Normal**. Move surface points only along surface's normal vectors;
    i.e., apply only the projection of the field to surface's normals to the
    surface.
  * **Along tangent**. Move surface points only along surface's tangent planes,
    i.e. only perpendicular to the normals.

  This parameter is not available if **Use Control Points** parameter is checked.

Outputs
-------

This node has the following output:

* **Surface**. The generated surface.

Examples of usage
-----------------

Noise field applied to the sphereical surface:

.. image:: https://user-images.githubusercontent.com/284644/79371205-6ae86780-7f6d-11ea-80f7-3bf5ca71c7cf.png

An example with more complex field:

.. image:: https://user-images.githubusercontent.com/284644/79371656-23aea680-7f6e-11ea-97e1-1ac22cb194a1.png

