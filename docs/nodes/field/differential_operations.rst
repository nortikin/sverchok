Field Differential Operations
=============================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/095ac40e-048e-46a2-8b54-f3bf2c38bcc9
  :target: https://github.com/nortikin/sverchok/assets/14288520/095ac40e-048e-46a2-8b54-f3bf2c38bcc9

Functionality
-------------

This node calculates Vector or Scalar Field by performing one of supported
differential operations on the fields provided as inputs.

Note that the differentiation is done numerically, and so there is always some
calculation error. The error can be minimizing by adjusting the "step"
parameter.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/88159366-b4ab-4b72-a5e4-3cb0d8d89b6d
  :target: https://github.com/nortikin/sverchok/assets/14288520/88159366-b4ab-4b72-a5e4-3cb0d8d89b6d

.. image:: https://github.com/nortikin/sverchok/assets/14288520/2694d9e3-f0c7-4117-a50d-02772ead70dd
  :target: https://github.com/nortikin/sverchok/assets/14288520/2694d9e3-f0c7-4117-a50d-02772ead70dd

* Fields-> :doc:`Attractor Field </nodes/field/attractor_field_mk2>`

Inputs
------

This node has the following inputs:

* **SFieldA**. Scalar field to operate on. This input is mandatory when available.
* **VFieldA**. Vector field to operate on. This input is mandatory when available.

The availability of the inputs is defined by the selected operation.

Parameters
----------

This node has the following parameters:

* **Operation**. The differential operation to perform. The available operations are:

  * **Gradient**. Calculate the gradient of the scalar field. The result is a vector field.
  * **Divergence**. Calculate the divergence of the vector field. The result is a scalar field.
  * **Laplacian**. Calculate the Laplace operator on the scalar field. The result is a scalar field.
  * **Rotor**. Calculate the rotor operator on the vector field. The result is a vector field.

* **Step**. Derivatives calculation step. The default value is 0.001. Bigger values give smoother fields.

Outputs
-------

This node has the following outputs:

* **SFieldB**. The resulting scalar field.
* **VFieldB**. The resulting vector field.

Examples of usage
-----------------

Generate a scalar field, calculate it's gradient, and apply that to a cube:

.. image:: https://user-images.githubusercontent.com/284644/79501054-deaa7300-8046-11ea-8cf6-d01471cb1eea.png
  :target: https://user-images.githubusercontent.com/284644/79501054-deaa7300-8046-11ea-8cf6-d01471cb1eea.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Fields-> :doc:`Scalar Field Formula </nodes/field/scalar_field_formula>`
* Fields-> :doc:`Apply Vector Field </nodes/field/vector_field_apply>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

.. image:: https://github.com/nortikin/sverchok/assets/14288520/a0b8f975-3266-4c7a-be3e-68a6c11f72b3
  :target: https://github.com/nortikin/sverchok/assets/14288520/a0b8f975-3266-4c7a-be3e-68a6c11f72b3

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Fields-> :doc:`Attractor Field </nodes/field/attractor_field_mk2>`
* Fields-> :doc:`Vector Field Lines </nodes/field/vector_field_lines>`
* Transform-> :doc:`Noise Displace </nodes/transforms/noise_displace>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Color-> :doc:`Color In </nodes/color/color_in_mk1>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Scene-> :doc:`Frame Info </nodes/scene/frame_info_mk2>`