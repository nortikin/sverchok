Scalar Field Math
=================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/631deb22-c5ee-4a3c-b726-5ac2280d2a8c
  :target: https://github.com/nortikin/sverchok/assets/14288520/631deb22-c5ee-4a3c-b726-5ac2280d2a8c

Functionality
-------------

This node generates a Scalar Field by executing one of supported mathematical operations on the Scalar Fields provided as inputs.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/07c858a3-55f5-4b03-9f2f-ec9a0802ffae
  :target: https://github.com/nortikin/sverchok/assets/14288520/07c858a3-55f5-4b03-9f2f-ec9a0802ffae

Inputs
------

This node has the following inputs:

* **FieldA**. The first scalar field. The input is mandatory when available.
* **FieldB**. The second scalar field. The input is mandatory when available.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/c3d5d5f9-64ca-401f-a79d-e999cfc67d06
      :target: https://github.com/nortikin/sverchok/assets/14288520/c3d5d5f9-64ca-401f-a79d-e999cfc67d06

Parameters
----------

This node has the following parameter:

* **Operation**. This defines the mathematical operation to perform. The available operations are:

  * **Add**. Add two scalar fields.
  * **Sub**. Subtract one scalar field from another.
  * **Multiply**. Multiply two scalar fields.
  * **Minimum**. Create a scalar field, the value of which is calculated as
    minimal of values of two scalar fields at the same point.
  * **Maximum**. Create a scalar field, the value of which is calculated as
    maximal of values of two scalar fields at the same point.
  * **Average**. Arithmetic mean (average) of two scalar fields - (A + B)/2.
  * **Negate**. Negate the scalar field values.

Outputs
-------

The node has the following output:

* **FieldC**. The resulting scalar field.

Examples of usage
-----------------

.. image:: https://github.com/nortikin/sverchok/assets/14288520/6cc7ad1d-89d7-4601-888d-e992f02dc546
  :target: https://github.com/nortikin/sverchok/assets/14288520/6cc7ad1d-89d7-4601-888d-e992f02dc546

* Generator-> :doc:`Segment </nodes/generator/segment>`
* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Surfaces-> :doc:`Marching Cubes </nodes/surface/marching_cubes>`
* Fields-> :doc:`Voronoi Field </nodes/field/voronoi_field>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://github.com/nortikin/sverchok/assets/14288520/6d7e940b-5be8-4779-b125-7bd2cce14125
  :target: https://github.com/nortikin/sverchok/assets/14288520/6d7e940b-5be8-4779-b125-7bd2cce14125

---------

Example #1:

.. image:: https://user-images.githubusercontent.com/284644/79497591-60979d80-8041-11ea-9c23-1e0d6be96708.png
  :target: https://user-images.githubusercontent.com/284644/79497591-60979d80-8041-11ea-9c23-1e0d6be96708.png

* Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`
* Fields-> :doc:`Attractor Field </nodes/field/attractor_field_mk2>`
* Fields-> :doc:`Evaluate Scalar Field </nodes/field/scalar_field_eval>`
* Spacial-> :doc:`Vector P Field </nodes/spatial/homogenous_vector_field>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Example #2:

.. image:: https://user-images.githubusercontent.com/284644/79497828-cbe16f80-8041-11ea-957f-54c011afe3a3.png
  :target: https://user-images.githubusercontent.com/284644/79497828-cbe16f80-8041-11ea-957f-54c011afe3a3.png

* Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`
* Fields-> :doc:`Attractor Field </nodes/field/attractor_field_mk2>`
* Fields-> :doc:`Noise Vector Field </nodes/field/noise_vfield>`
* Fields-> :doc:`Vector Field Math </nodes/field/vector_field_math>`
* Fields-> :doc:`Evaluate Scalar Field </nodes/field/scalar_field_eval>`
* Spacial-> :doc:`Vector P Field </nodes/spatial/homogenous_vector_field>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`