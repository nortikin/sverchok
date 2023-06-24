Surface Frame
=============

.. image:: https://github.com/nortikin/sverchok/assets/14288520/3e76ce84-cbb1-440d-b416-9b5dfc5ddd68
  :target: https://github.com/nortikin/sverchok/assets/14288520/3e76ce84-cbb1-440d-b416-9b5dfc5ddd68

Functionality
-------------

This node outputs information about normals and tangents of the surface at
given points, together with a matrix giving reference frame according to
surface normals.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/588ffb4c-9caf-45a4-9e17-3afd4910e1c2
  :target: https://github.com/nortikin/sverchok/assets/14288520/588ffb4c-9caf-45a4-9e17-3afd4910e1c2

* Surfaces-> :doc:`Plane (Surface) </nodes/surface/plane>`
* Surfaces-> :doc:`Apply Field to Surface </nodes/surface/apply_field_to_surface>`
* Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`
* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Fields-> :doc:`Noise Vector Field </nodes/field/noise_vfield>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Matrix Multiply: Matrix-> :doc:`Matrix Math </nodes/matrix/matrix_math>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

Inputs
------

* **Surface**. The surface to analyze. This input is mandatory.
* **U**, **V**. Values of U and V surface parameters. These inputs are
  available only when **Input mode** parameter isset to **Separate**. The
  default value is 0.5.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/b533e68e-dee5-4fe5-a1d0-3d60c971e3fc
      :target: https://github.com/nortikin/sverchok/assets/14288520/b533e68e-dee5-4fe5-a1d0-3d60c971e3fc

    * Number-> :doc:`List Input </nodes/number/list_input>`

* **UVPoints**. Points at which the surface is to be analyzed. Only two of
  three coordinates will be used; the coordinates used are defined by the
  **Orientation** parameter. This input is available and mandatory if the
  **Input mode** parameter is set to **Vertices**.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/ff435e77-d707-452d-b5ad-9d27bf803d87
      :target: https://github.com/nortikin/sverchok/assets/14288520/ff435e77-d707-452d-b5ad-9d27bf803d87

Parameters
----------

This node has the following parameters:

* **Input mode**. The available options are:

   * **Separate**. The values of U and V surface parameters will be provided in
     **U** and **V** inputs, correspondingly.
   * **Vertices**. The values of U and V surface parameters will be provided in
     **Vertices** input; only two of three coordinates of the input vertices
     will be used.
   
   The default mode is **Separate**.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/14e36482-d111-4c37-8a58-8acb482d425b
      :target: https://github.com/nortikin/sverchok/assets/14288520/14e36482-d111-4c37-8a58-8acb482d425b

* **Input orientation**. This parameter is available only when  **Input mode**
  parameter is set to **Vertices**. This defines which coordinates of vertices
  provided in the **Vertices** input will be used. The available options are
  XY, YZ and XZ. For example, if this is set to XY, then the X coordinate of
  vertices will be used as surface U parameter, and Y coordinate will be used
  as V parameter. The default value is XY.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/7cd6a990-2fe0-4510-8bc2-135e7f77c393
      :target: https://github.com/nortikin/sverchok/assets/14288520/7cd6a990-2fe0-4510-8bc2-135e7f77c393

* **Clamp**. This defines how the node will process the values of
  surface U and V parameters which are out of the surface's domain. The
  available options are:

   * **As is**. Do not do anything special, just pass the parameters to the
     surface calculation algorithm as they are. The behaviour of the surface
     when the values of parameters provided are out of domain depends on
     specific surface: some will just calculate points by the same formula,
     others will give an error.
   * **Clamp**. Restrict the parameter values to the surface domain: replace
     values that are greater than the higher bound with higher bound value,
     replace values that are smaller than the lower bound with the lower bound
     value. For example, if the surface domain along U direction is `[0 .. 1]`,
     and the value of U parameter is 1.05, calculate the point of the surface
     at U = 1.0.
   * **Wrap**. Wrap the parameter values to be within the surface domain, i.e.
     take the values modulo domain. For example, if the surface domain along U
     direction is `[0 .. 1]`, and the value of U parameter is 1.05, evaluate
     the surface at U = 0.05.

   The default mode is **As is**.

Outputs
-------

This node has the following outputs:

* **Normal**. Unit normal vectors of the surface at the specified points.

  .. image:: https://github.com/nortikin/sverchok/assets/14288520/817ea4da-bbfa-442f-a8c0-e1a9334b7355
    :target: https://github.com/nortikin/sverchok/assets/14288520/817ea4da-bbfa-442f-a8c0-e1a9334b7355

* **TangentU**. Unit tangent vectors of the surface at the specified points
  along the U direction; more precisely, if the surface is defined by ``P =
  F(u, v)``, then this is ``dF/du`` vector divided by it's length.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/f8be4cf9-68fc-43a1-a7a6-170214c22c18
      :target: https://github.com/nortikin/sverchok/assets/14288520/f8be4cf9-68fc-43a1-a7a6-170214c22c18

* **TangentV**. Unit tangent vectors of the surface at the specified points
  along the V direction; more precisely, if the surface is defined by ``P =
  F(u, v)``, then this is ``dF/dv`` vector divided by it's length.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/0d294ee7-954a-478a-8aee-45399a7e539c
      :target: https://github.com/nortikin/sverchok/assets/14288520/0d294ee7-954a-478a-8aee-45399a7e539c

* **AreaStretch**. Coefficient of the stretching of the surface area in the
  mapping of areas in the UV space to 3D space, in the provided points. This
  equals to ``|dF/du| * |dF/dv|`` (norm of derivative by U multiplied by norm
  of derivative by V). So, **AreaStretch** is always equal to product of
  **StretchU** by **StretchV**.
* **StretchU**. Coefficient of stretching the surface along the U direction;
  this equals to ``|dF/du|``.
* **StretchV**. Coefficient of stretching the surface along the V direction;
  this equals to ``|dF/dv|``.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/abfa65dc-40c6-417c-be56-19982032ff72
      :target: https://github.com/nortikin/sverchok/assets/14288520/abfa65dc-40c6-417c-be56-19982032ff72

    * A*SCALAR, CROSS, LEN: Vector-> :doc:`Vector Math </nodes/vector/math_mk3>`
    * Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

* **Matrix**. Reference frame at the surface point, defined by the surface's
  normal and parametric tangents: it's Z axis is looking along surface normal;
  it's X axis is looking along **TangentU**, and it's Y axis is looking along
  **TangentV**.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/023899ab-7463-4813-bd64-2bf97405decd
      :target: https://github.com/nortikin/sverchok/assets/14288520/023899ab-7463-4813-bd64-2bf97405decd

* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Matrix Multiply: Matrix-> :doc:`Matrix Math </nodes/matrix/matrix_math>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

Examples of Usage
-----------------

Visualize Matrix outputfor some formula-defined surface:

.. image:: https://github.com/nortikin/sverchok/assets/14288520/25a59ce8-5a83-44cc-adf9-8707589ede3d
  :target: https://github.com/nortikin/sverchok/assets/14288520/25a59ce8-5a83-44cc-adf9-8707589ede3d

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Surfaces-> :doc:`Surface Formula </nodes/surface/surface_formula>`
* Surfaces-> :doc:`Surface Domain </nodes/surface/surface_domain>`
* Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Matrix-> :doc:`Matrix Math </nodes/matrix/matrix_math>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Script-> :doc:`Formula </nodes/script/formula_mk5>`

.. image:: https://github.com/nortikin/sverchok/assets/14288520/8f2a3747-e78c-459a-91d4-e0527ecf621f
  :target: https://github.com/nortikin/sverchok/assets/14288520/8f2a3747-e78c-459a-91d4-e0527ecf621f

Use that matrices to place cubes, oriented accordingly:

.. image:: https://github.com/nortikin/sverchok/assets/14288520/9aa259ed-b40d-4aff-8ff0-4aabadaa616d
  :target: https://github.com/nortikin/sverchok/assets/14288520/9aa259ed-b40d-4aff-8ff0-4aabadaa616d

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Surfaces-> :doc:`Surface Formula </nodes/surface/surface_formula>`
* Surfaces-> :doc:`Surface Domain </nodes/surface/surface_domain>`
* Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Matrix-> :doc:`Matrix Math </nodes/matrix/matrix_math>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Script-> :doc:`Formula </nodes/script/formula_mk5>`

.. image:: https://github.com/nortikin/sverchok/assets/14288520/4b61b97f-ee5a-4268-940f-c082d6953588
  :target: https://github.com/nortikin/sverchok/assets/14288520/4b61b97f-ee5a-4268-940f-c082d6953588

As you can see, the surface in areas that are far from the center, so that cubes are put sparsely. Let's use StretchU and StretchV outputs to scale them:

.. image:: https://user-images.githubusercontent.com/284644/81722582-03a1d280-949b-11ea-8e99-9d9354f5e906.png
  :target: https://user-images.githubusercontent.com/284644/81722582-03a1d280-949b-11ea-8e99-9d9354f5e906.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`
* Surfaces-> :doc:`Surface Formula </nodes/surface/surface_formula>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Matrix-> :doc:`Matrix Deform </nodes/matrix/matrix_deform>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`