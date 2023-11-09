Bend Along Surface Field
========================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/e953f1d5-2071-4113-8b14-18dc46ee3645
  :target: https://github.com/nortikin/sverchok/assets/14288520/e953f1d5-2071-4113-8b14-18dc46ee3645

Functionality
-------------

This node generates a Vector Field, which bends some part of 3D space along the provided Surface object.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/32409cb1-9a50-4a29-9759-c787e15f5e2b
  :target: https://github.com/nortikin/sverchok/assets/14288520/32409cb1-9a50-4a29-9759-c787e15f5e2b

Inputs
------

This node has the following inputs:

* **Surface**. The surface to bend the space along. This input is mandatory.
* **Src U Min**, **Src U Max**. Minimum and maximum value of the first of
  orientation coordinates, which define the part of space to be bent. For
  example, if the **Object vertical axis** parameter is set to **Z**, then these
  are minimum and maximum values of X coordinates. Default values are -1 and 1.
* **Src V Min**, **Src V Max**. Minimum and maximum value of the second of
  orientation coordinates, which define the part of space to be bent. For
  example, if the **Object vertical axis** parameter is set to **Z**, then these
  are minimum and maximum values of Y coordinates. Default values are -1 and 1.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/ac115320-84de-4dc3-b80e-70194a8dcba1
      :target: https://github.com/nortikin/sverchok/assets/14288520/ac115320-84de-4dc3-b80e-70194a8dcba1

The field bends the part of space, which is between **Src U Min** and **Src U
Max** by one axis, and between **Src V Min** and **Src V Max** by another axis.
For example, with default settings, the source part of space is the space
between X = -1, X = 1, Y = -1, Y = 1. The behaviour of the field outside of
these bounds is not guaranteed.

Parameters
----------

This node has the following parameters:

* **Object vertical axis**. This defines which axis of the source space should
  be mapped to the normal axis of the surface. The available values are X, Y
  and Z. The default value is Z. This means that XOY plane will be mapped onto
  the surface.
* **Auto scale**. If checked, scale the source space along the vertical axis,
  trying to match the scale coefficient for two other axes. Otherwise, the
  space will not be scaled along the vertical axis. Unchecked by default.
* **As 2D**. If checked, it will discard the vertical axis. Enable to bend flat objects.
  Improves performance.
* **Flip surface**. This parameter is only available in the node's N panel. If
  checked, then the surface will be considered as flipped (turned upside down),
  so the vector field will also turn the space upside down. Unchecked by
  default.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/6a7e5fe1-597f-4e84-aebe-c654b3ccf3a8
      :target: https://github.com/nortikin/sverchok/assets/14288520/6a7e5fe1-597f-4e84-aebe-c654b3ccf3a8

Outputs
-------

This node has the following output:

* **Field**. The generated bending vector field.

Example of usage
----------------

Example of description

.. image:: https://github.com/nortikin/sverchok/assets/14288520/31188c66-c340-4246-bcc8-09d120a9886f
  :target: https://github.com/nortikin/sverchok/assets/14288520/31188c66-c340-4246-bcc8-09d120a9886f

* Generator->Generatots Extended-> :doc:`Hilbert </nodes/generators_extended/hilbert>`
* Surfaces-> :doc:`Plane (Surface) </nodes/surface/plane>`
* Surfaces-> :doc:`Sphere (Surface) </nodes/surface/surface_sphere>`
* Surfaces-> :doc:`Apply Field to Surface </nodes/surface/apply_field_to_surface>`
* Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`
* Fields-> :doc:`Distance From a Point </nodes/field/scalar_field_point>`
* Fields-> :doc:`Scalar Field Math </nodes/field/scalar_field_math>`
* Fields-> :doc:`Decompose Vector Field </nodes/field/decompose_vector_field>`
* Fields-> :doc:`Noise Vector Field </nodes/field/noise_vfield>`
* Fields-> :doc:`Vector Field Math </nodes/field/vector_field_math>`
* Fields-> :doc:`Apply Vector Field </nodes/field/vector_field_apply>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Number-> :doc:`List Input </nodes/number/list_input>`
* ADD: Vector-> :doc:`Vector Math </nodes/vector/math_mk3>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Matrix-> :doc:`Matrix Apply to Mesh </nodes/matrix/apply_and_join>`
* Matrix Multiply: Matrix-> :doc:`Matrix Math </nodes/matrix/matrix_math>`
* List->List Main-> :doc:`List Decompose </nodes/list_main/decompose>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Modifiers->Modifier Change-> :doc:`Subdivide to Quads </nodes/modifier_change/subdivide_to_quads>`
* Modifiers->Modifier Make-> :doc:`Solidify </nodes/modifier_make/solidify_mk2>`
* Modifiers->Modifier Make-> :doc:`Offset Line </nodes/modifier_make/offset_line>`

**1**

.. image:: https://github.com/nortikin/sverchok/assets/14288520/db8ed577-58f6-4da9-b519-626c838978c1
  :target: https://github.com/nortikin/sverchok/assets/14288520/db8ed577-58f6-4da9-b519-626c838978c1

**2**

.. image:: https://github.com/nortikin/sverchok/assets/14288520/11f40189-6759-48bf-b776-72f0ae0d9d3c
  :target: https://github.com/nortikin/sverchok/assets/14288520/11f40189-6759-48bf-b776-72f0ae0d9d3c

---------

Generate a rectangular grid of cubes, and bend it along formula-specified surface:

.. image:: https://user-images.githubusercontent.com/284644/79602628-42df3c80-8104-11ea-80c3-09be659d54f8.png
  :target: https://user-images.githubusercontent.com/284644/79602628-42df3c80-8104-11ea-80c3-09be659d54f8.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Surfaces-> :doc:`Surface Formula </nodes/surface/surface_formula>`
* Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`
* Fields-> :doc:`Apply Vector Field </nodes/field/vector_field_apply>`
* Matrix Apply: Matrix-> :doc:`Matrix Apply to Mesh </nodes/matrix/apply_and_join>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`