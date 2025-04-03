Attractor Field
===============
 
.. image:: https://github.com/nortikin/sverchok/assets/14288520/f09028d8-4f03-4dfe-bc3c-d0d57cbb3fa7
  :target: https://github.com/nortikin/sverchok/assets/14288520/f09028d8-4f03-4dfe-bc3c-d0d57cbb3fa7

Functionality
-------------

This node generates a Vector Field and a Scalar Field, which are calculated as
force attracting points towards some objects. Several types of attractor
objects are supported. Several physics-like falloff laws are supported.
Falloffs similar to standard proportional editing mode are supported too (they
are marked with `(P)` in the name).

The scalar field generated equals to the norm of the vector field - i.e., the amplitude of the attracting force.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/3b593948-e9c1-4606-b942-c835baa4419e
  :target: https://github.com/nortikin/sverchok/assets/14288520/3b593948-e9c1-4606-b942-c835baa4419e

Inputs
------

This node has the following inputs:

* **Center**. The exact meaning of this input depends on the **Attractor type** parameter:

  * If attractor type is **Point**, then this is the attracting point itself;
  * if attractor type is **Line**, then this is the point lying on the attracting line;
  * if attractor type is **Plane**, then this is the point lying on the attracting plane.
  * if attractor type is **Mesh - Faces** or **Mesh - Edges**, then this is the set of mesh vertices.
  * If attractor type is **Circle**, then this is the center of the circle.

  It is possible to provide several attracting points. The default value is `(0, 0, 0)` (origin).

* **Direction**. The exact meaning of this input depends on the **Attractor type** parameter:

  * if attractor type is **Line**, then this is the directing vector of the line;
  * if attractor type is **Plane**, then this is the normal vector of the plane.
  * with other attractor types, this input is not available.

  The default value is `(0, 0, 1)` (Z axis).

* **Edges**. The edges of the attracting mesh. This input is available only
  when **Attractor type** parameter is set to **Mesh - Edges**.
* **Faces**. The faces of the attracting mesh. This input is available only
  when **Attractor type** parameter is set to **Mesh - Faces**.
* **Radius**. Circle radius. This input is only available when **Attractor type** parameter is set to **Circle**.
* **Amplitude**. The attracting force amplitude. The default value is 0.5.
* **Coefficient**. The coefficient used in the attracting force falloff
  calculation formula. The exact meaning of this input depends on fallof type:
  
   * If **Falloff type** is set to **Inverse exponent** or **Gauss**, then this
     is the coefficient K in the corresponding formula: ``exp(-K*R)`` or
     ``exp(-K*x^2/2)``.
   * If **Falloff type** is set to one of proportional editing modes (one
     starting with ``(P)`` prefix), this is the radius of proportional editing
     falloff.
   * For other falloff types, this input is not available.
     
   The default value is 0.5.

Parameters
----------

This node has the following parameters:

* **Attractor type**. The type of attractor object being used. The available values are:

   * **Point** is defined in the corresponding input.

      .. image:: https://github.com/nortikin/sverchok/assets/14288520/4657bd4f-5db7-4419-9098-a102e0241020
        :target: https://github.com/nortikin/sverchok/assets/14288520/4657bd4f-5db7-4419-9098-a102e0241020

   * **Line** is defined by a point and the directing vector.
 
      .. image:: https://github.com/nortikin/sverchok/assets/14288520/a2ef3148-4ea2-435d-a86e-ca972c8e0f8f
        :target: https://github.com/nortikin/sverchok/assets/14288520/a2ef3148-4ea2-435d-a86e-ca972c8e0f8f

   * **Plane** is defined by a point and the normal vector.

      .. image:: https://github.com/nortikin/sverchok/assets/14288520/9d0a3d14-fca9-4c71-803b-4de670a5831f
        :target: https://github.com/nortikin/sverchok/assets/14288520/9d0a3d14-fca9-4c71-803b-4de670a5831f

   * **Mesh - Faces** is defined by vertices and faces.

      .. image:: https://github.com/nortikin/sverchok/assets/14288520/039473f5-5fdd-4d39-94c2-22564477cb3b
        :target: https://github.com/nortikin/sverchok/assets/14288520/039473f5-5fdd-4d39-94c2-22564477cb3b

   * **Mesh - Edges** is defined by vertices and edges.

      .. image:: https://github.com/nortikin/sverchok/assets/14288520/a902a3b6-c247-4b68-9f0b-1418c42c6375
        :target: https://github.com/nortikin/sverchok/assets/14288520/a902a3b6-c247-4b68-9f0b-1418c42c6375


   The default value is **Point**.

* **Join mode**. This determines how the distance is calculated when multiple
  attraction centers are provided. The available values are:

  * **Average**. Calculate the average of the attracting forces towards the
    provided centers. This mode is used in physics. This option is the default
    one.

      .. image:: https://github.com/nortikin/sverchok/assets/14288520/6a087b53-a13c-4aac-96d0-455aaf24ccd7
        :target: https://github.com/nortikin/sverchok/assets/14288520/6a087b53-a13c-4aac-96d0-455aaf24ccd7

  * **Nearest**. Use only the force of the attraction towards the nearest attraction center.

      .. image:: https://github.com/nortikin/sverchok/assets/14288520/2d818246-30f2-458c-aa04-939ab6d9390b
        :target: https://github.com/nortikin/sverchok/assets/14288520/2d818246-30f2-458c-aa04-939ab6d9390b

  * **Separate**. Generate a separate field of attraction force for each attraction center.
    This parameter is not available when the **Attractor type** is set to **Mesh - Faces**.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/84cd12cb-e392-453c-81cd-90830a839d18
      :target: https://github.com/nortikin/sverchok/assets/14288520/84cd12cb-e392-453c-81cd-90830a839d18

    * Generator-> :doc:`NGon </nodes/generator/ngon>`
    * List->List Main-> :doc:`List Decompose </nodes/list_main/decompose>`
    * Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

* **Signed**. This parameter is available only when **Attractor type**
  parameter is set to **Mesh - faces**. If checked, then the resulting scalar field
  will be signed: it will have positive values at the one side of the mesh
  (into which the mesh normals are pointing), and negative values at the other
  side of the mesh. Otherwise, the scalar field will have positive values
  everywhere. This flag does not affect the calculated vector field. Unchecked
  by default.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/475f18d7-46a7-45f1-ac7d-5264cbdf6514
      :target: https://github.com/nortikin/sverchok/assets/14288520/475f18d7-46a7-45f1-ac7d-5264cbdf6514

* **Metric**. This parameter is available only when **Attractor type**
  parameter is set to **Point**. The metric to be used to calculate distances.
  The available options are:

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/470925a1-83c4-48e1-8669-9424f4e8097b
      :target: https://github.com/nortikin/sverchok/assets/14288520/470925a1-83c4-48e1-8669-9424f4e8097b

  * **Euclidean**

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/96269a83-dea6-4c39-b382-9ebc47bea4d5
      :target: https://github.com/nortikin/sverchok/assets/14288520/96269a83-dea6-4c39-b382-9ebc47bea4d5

  * **Manhattan**

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/f191c23c-1032-4b99-95da-4b96a21af1dc
      :target: https://github.com/nortikin/sverchok/assets/14288520/f191c23c-1032-4b99-95da-4b96a21af1dc

  * **Chebyshev**

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/831c1e3a-020e-4274-bacf-cb0f95896b1b
      :target: https://github.com/nortikin/sverchok/assets/14288520/831c1e3a-020e-4274-bacf-cb0f95896b1b

  * **Custom**. A generic Minkowski metric defined by formula
    ``sum(abs(dx_i)**P)**(1.0/P)``, where P is defined in the Exponent
    parameter.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/6f6e615e-fc63-4f5e-a15b-16e9c5e2aae3
      :target: https://github.com/nortikin/sverchok/assets/14288520/6f6e615e-fc63-4f5e-a15b-16e9c5e2aae3
   
  The default value is **Euclidean**.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/b8ad8079-1518-4d47-88d6-a0fc7e8dbebd
      :target: https://github.com/nortikin/sverchok/assets/14288520/b8ad8079-1518-4d47-88d6-a0fc7e8dbebd

* **Exponent**. This parameter is available only when **Attractor** parameter
  is set to **Point**, and **Metric** parameter is set to **Custom**. Exponent
  for generic Minkowski distance. The available values are from 1.0 to
  infinity. The default value is 2.0, which defines Euclidean metric.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/6f6e615e-fc63-4f5e-a15b-16e9c5e2aae3
      :target: https://github.com/nortikin/sverchok/assets/14288520/6f6e615e-fc63-4f5e-a15b-16e9c5e2aae3
   

* **Falloff type**. The force falloff type to be used. The available values are:

   * **None - R**. Do not use falloff: the force amplitude is proportional to the distance from the attractor object (grows with the distance).
   * **Inverse - 1/R**. Calculate the force value as 1/R.
   * **Inverse square - 1/R^2**. Calculate the force value as `1/R^2`. This law is most commonly used in physics.
   * **Inverse cubic - 1/R^3**. Calculate the force value as `1/R^3`.
   * **Inverse exponent - Exp(-R)**. Calculate the force value as `Exp(- K*R)`.
   * **Gauss - Exp(-R^2/2)**. Calculate the force value as `Exp(- K * R^2/2)`.
   * **(P) Smooth**. Equivalent of "Smooth" proportional editing falloff.
   * **(P) Sphere**. Equivalent of "Sphere" proportional editing falloff.
   * **(P) Root**. Equivalent of "Root" proportional editing falloff.
   * **(P) Inverse Square**. Equivalent of "Inverse Square" proportional editing falloff.
   * **(P) Linear**. Equivalent of "Linear" proportional editing falloff.
   * **(P) Constant**. Equivalent of "Constant" proportional editing falloff.

   The default option is **None**.
* **Clamp**. If checked, then the amplitude of attracting force vector will be
  restricted with the distance to attractor object. Unchecked by default.

Outputs
-------

This node has the following outputs:

* **VField**. Vector field of the attracting force.
* **SField**. Scalar field of the attracting force (amplitude of the attracting force).

Examples of usage
-----------------

.. image:: https://github.com/nortikin/sverchok/assets/14288520/04da9358-4f2a-4fd8-98e8-dca6d166b1e9
  :target: https://github.com/nortikin/sverchok/assets/14288520/04da9358-4f2a-4fd8-98e8-dca6d166b1e9

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Fields-> :doc:`Evaluate Vector Field </nodes/field/vector_field_eval>`
* Fields-> :doc:`Evaluate Scalar Field </nodes/field/scalar_field_eval>`
* Spacial-> :doc:`Vector P Field </nodes/spatial/homogenous_vector_field>`
* Number-> :doc:`Map Range </nodes/number/range_map>`
* Color-> :doc:`Color Input </nodes/color/color_input>`
* Color-> :doc:`Color Out </nodes/color/color_out_mk1>`
* Color-> :doc:`Color In </nodes/color/color_in_mk1>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`


.. image:: https://github.com/nortikin/sverchok/assets/14288520/74da3378-369c-4513-8799-9e573927c527
  :target: https://github.com/nortikin/sverchok/assets/14288520/74da3378-369c-4513-8799-9e573927c527

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Fields-> :doc:`Evaluate Scalar Field </nodes/field/scalar_field_eval>`
* Spacial-> :doc:`Vector P Field </nodes/spatial/homogenous_vector_field>`
* Number-> :doc:`Map Range </nodes/number/range_map>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Color-> :doc:`Color Input </nodes/color/color_input>`
* Color-> :doc:`Color In </nodes/color/color_in_mk1>`
* Color-> :doc:`Color Out </nodes/color/color_out_mk1>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

The attraction field of one point visualized:

.. image:: https://user-images.githubusercontent.com/284644/79471192-b8bba900-801b-11ea-829e-2b003d9000da.png
  :target: https://user-images.githubusercontent.com/284644/79471192-b8bba900-801b-11ea-829e-2b003d9000da.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Fields-> :doc:`Vector Field Graph </nodes/field/vector_field_graph>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

The attraction field of Z axis visualized:

.. image:: https://user-images.githubusercontent.com/284644/79471186-b78a7c00-801b-11ea-8926-3cc14b792220.png
  :target: https://user-images.githubusercontent.com/284644/79471186-b78a7c00-801b-11ea-8926-3cc14b792220.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Fields-> :doc:`Vector Field Graph </nodes/field/vector_field_graph>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

The attraction field of a point applied to several planes:

.. image:: https://user-images.githubusercontent.com/284644/79471194-b9543f80-801b-11ea-89dc-3b631659f1b2.png
  :target: https://user-images.githubusercontent.com/284644/79471194-b9543f80-801b-11ea-89dc-3b631659f1b2.png

* Generator-> :doc:`Segment </nodes/generator/segment>`
* Surfaces-> :doc:`Plane (Surface) </nodes/surface/plane>`
* Surfaces-> :doc:`Apply Field to Surface </nodes/surface/apply_field_to_surface>`
* Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Use the attraction field of cylinder to move points of the plane up:

.. image:: https://user-images.githubusercontent.com/284644/80508641-bcdbb500-8991-11ea-9ed0-030ca6d0bc44.png
  :target: https://user-images.githubusercontent.com/284644/80508641-bcdbb500-8991-11ea-9ed0-030ca6d0bc44.png

* Generator-> :doc:`Cylinder </nodes/generator/cylinder_mk2>`
* Surfaces-> :doc:`Plane (Surface) </nodes/surface/plane>`
* Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`
* Fields-> :doc:`Vector Field Math </nodes/field/vector_field_math>`
* Transform-> :doc:`Rotate </nodes/transforms/rotate_mk3>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Field lines of field attracting to a circle:

.. image:: https://user-images.githubusercontent.com/284644/82155610-9d98bf00-988f-11ea-92db-6e7d2dfb6db0.png
  :target: https://user-images.githubusercontent.com/284644/82155610-9d98bf00-988f-11ea-92db-6e7d2dfb6db0.png

* Spacial-> :doc:`Vector P Field </nodes/spatial/homogenous_vector_field>`
* Fields-> :doc:`Vector Field Lines </nodes/field/vector_field_lines>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Field lines of field attracting to edges of a cube:

.. image:: https://user-images.githubusercontent.com/284644/82155611-9ec9ec00-988f-11ea-881b-54d90b71940c.png
  :target: https://user-images.githubusercontent.com/284644/82155611-9ec9ec00-988f-11ea-881b-54d90b71940c.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Fields-> :doc:`Vector Field Lines </nodes/field/vector_field_lines>`
* Spacial-> :doc:`Vector P Field </nodes/spatial/homogenous_vector_field>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Use of "Mesh - Edges" mode together with Marching Cubes node (from Sverchok-Extra addon):

.. image:: https://user-images.githubusercontent.com/284644/82155613-9ffb1900-988f-11ea-8cc1-b3ffe2768b90.png
  :target: https://user-images.githubusercontent.com/284644/82155613-9ffb1900-988f-11ea-8cc1-b3ffe2768b90.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Surfaces-> :doc:`Marching Cubes </nodes/surface/marching_cubes>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`