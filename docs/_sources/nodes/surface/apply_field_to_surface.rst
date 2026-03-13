Apply Field to Surface
======================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/8019b545-7cdd-4c92-b7be-ae4eb3ac3d4d
  :target: https://github.com/nortikin/sverchok/assets/14288520/8019b545-7cdd-4c92-b7be-ae4eb3ac3d4d

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

.. image:: https://github.com/nortikin/sverchok/assets/14288520/2b6fcc1e-9085-4e9a-a3c0-4eaf1de22bcf
  :target: https://github.com/nortikin/sverchok/assets/14288520/2b6fcc1e-9085-4e9a-a3c0-4eaf1de22bcf

Inputs
------

This node has the following inputs:

* **Field**. Vector field to apply. This input is mandatory.
* **Surface**. The surface to apply the vector field to. This input is mandatory.
* **Coefficient**. The "strength" coefficient. Value of 0 will output the
  surface as it was. The default value is 1.0.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/07dabcee-a13d-4079-abb9-ab2bb0b79387
      :target: https://github.com/nortikin/sverchok/assets/14288520/07dabcee-a13d-4079-abb9-ab2bb0b79387

Parameters
----------

This node has the following parameter:

* **Use Control Points**. If checked, then the vector field will be applied to
  control points of a NURBS surface, instead of applying it to all points of the
  surface. This node will fail (become red) if this mode is enabled, but input
  surface is not a NURBS and can not be presented as a NURBS. If not checked,
  then the node will apply the vector field to all points of the surface; in
  such a case, it can process any type of surface. Disabled by default.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/df590aa6-8533-417d-a019-7ba24899a89e
      :target: https://github.com/nortikin/sverchok/assets/14288520/df590aa6-8533-417d-a019-7ba24899a89e

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

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/164463e2-f002-4451-9639-3ed375993948
      :target: https://github.com/nortikin/sverchok/assets/14288520/164463e2-f002-4451-9639-3ed375993948

Outputs
-------

This node has the following output:

* **Surface**. The generated surface.

Examples of usage
-----------------


Noise field applied to the torus surface:

.. image:: https://github.com/nortikin/sverchok/assets/14288520/096f4723-705e-4401-87fd-77d7d3e5dd86
  :target: https://github.com/nortikin/sverchok/assets/14288520/096f4723-705e-4401-87fd-77d7d3e5dd86

* Surfaces-> :doc:`Surface Formula </nodes/surface/surface_formula>`
* Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`
* Fields-> :doc:`Noise Vector Field </nodes/field/noise_vfield>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

Noise field applied to the sphereical surface:

.. image:: https://user-images.githubusercontent.com/284644/79371205-6ae86780-7f6d-11ea-80f7-3bf5ca71c7cf.png
  :target: https://user-images.githubusercontent.com/284644/79371205-6ae86780-7f6d-11ea-80f7-3bf5ca71c7cf.png

* Surfaces-> :doc:`Sphere (Surface) </nodes/surface/surface_sphere>`
* Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`
* Fields-> :doc:`Noise Vector Field </nodes/field/noise_vfield>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

An example with more complex field:

.. image:: https://user-images.githubusercontent.com/284644/79371656-23aea680-7f6e-11ea-97e1-1ac22cb194a1.png
  :target: https://user-images.githubusercontent.com/284644/79371656-23aea680-7f6e-11ea-97e1-1ac22cb194a1.png

* Surfaces-> :doc:`Sphere (Surface) </nodes/surface/surface_sphere>`
* Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`
* Fields-> :doc:`Vector Field Formula </nodes/field/vector_field_formula>`
* Fields-> :doc:`Vector Field Math </nodes/field/vector_field_math>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`