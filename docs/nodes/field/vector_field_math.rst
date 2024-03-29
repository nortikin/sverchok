Vector Field Math
=================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/9f9cd508-8e02-423b-b8bf-9679b0577360
  :target: https://github.com/nortikin/sverchok/assets/14288520/9f9cd508-8e02-423b-b8bf-9679b0577360

Functionality
-------------

This node generates a Vector Field and/or Scalar Field by executing one of
supported mathematical operations between the provided Vector and / or Scalar
fields.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/f634b376-d969-4c2a-a0c4-9c3e32558c28
  :target: https://github.com/nortikin/sverchok/assets/14288520/f634b376-d969-4c2a-a0c4-9c3e32558c28

Inputs
------

This node has the following inputs:

* **VFieldA**. The first vector field. This input is mandatory when available.
* **VFieldB**. The second vector field. This input is mandatory when available.
* **SFieldB**. The scalar field. This input is mandatory when available.

The availability of the inputs is defined by the mathematical operation being
used. Input names are adjusted corresponding to the selected operation.

Parameters
----------

This node has the following parameter:

* **Operation**. This defines the mathematical operation to execute. The following operations are available:

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/e26ddaff-6305-4f08-9047-62af4df7ef67
      :target: https://github.com/nortikin/sverchok/assets/14288520/e26ddaff-6305-4f08-9047-62af4df7ef67

  * **Add**. Calculate vector (coordinate-wise) sum of two vector fields - VFieldA + VFieldB.
  * **Sub**. Calculate vector (coordinate-wise) difference between two vector fields - VFieldA - VFieldB.
  * **Average**. Calculate the average between two vector fields - (VFieldA + VFieldB) / 2.
  * **Scalar Product**. Calculate scalar (dot) product of two vector fields.
  * **Vector Product**. Calculate vector (cross) product of two vector fields.
  * **Multiply Scalar**. Multiply the vectors of vector field by scalar values of scalar field.
  * **Projection decomposition**. Project the vectors of the first vector field
    to the vectors of the second vector field ("basis"); output the component
    of the first vector field which is colinear to the basis ("Projection") and
    the residual component ("Coprojection").
  * **Composition VB(VA(X))**. Functional composition of two vector fields; the
    resulting vector is calculated by evaluating the first vector field, and
    then evaluating the second vector field at the resulting point of the first
    evaluation.
  * **Composition SB(VA(X))**. Functional composition of vector field and a
    scalar field. The result is a scalar field. The resulting scalar is
    calculated by first evaluating the vector field at original point, and then
    evaluating the scalar field at the resulting point.
  * **Norm**. Calculate the norm (length) of vector field vectors. The result is a scalar field.
  * **Lerp A -> B**. Linear interpolation between two vector fields. The
    interpolation coefficient is defined by a scalar field. The result is a
    vector field.
  * **Relative -> Absolute**. Given the vector field VF, return the vector field which maps point X to `X + VF(X)`.
  * **Absolute -> Relative**. Given the vector field VF, return the vector field which maps point X to `VF(X) - X`.

Outputs
-------

This node has the following outputs:

* **VFieldC**. The first vector field result of the calculation.
* **SFieldC**. The scalar field result of the calculation.
* **VFieldD**. The second vector field result of the calculation.

The availability of the outputs is defined by the mathematical operation being
used. Output names are adjusted corresponding to the selected operation.

Examples of usage
-----------------

.. image:: https://github.com/nortikin/sverchok/assets/14288520/bc10d442-348f-4d22-9bfa-8b4030bfefcb
  :target: https://github.com/nortikin/sverchok/assets/14288520/bc10d442-348f-4d22-9bfa-8b4030bfefcb

* Fields-> :doc:`Attractor Field </nodes/field/attractor_field_mk2>`
* Fields-> :doc:`Vector Field Lines </nodes/field/vector_field_lines>`
* Spacial-> :doc:`Vector P Field </nodes/spatial/homogenous_vector_field>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://github.com/nortikin/sverchok/assets/14288520/a15cdc61-a0a6-4c92-9651-a44ee2c3fe45
  :target: https://github.com/nortikin/sverchok/assets/14288520/a15cdc61-a0a6-4c92-9651-a44ee2c3fe45

---------

Make a vector field as difference of two attraction fields:

.. image:: https://user-images.githubusercontent.com/284644/79495842-a56e0500-803e-11ea-91ed-611abf181ec2.png
  :target: https://user-images.githubusercontent.com/284644/79495842-a56e0500-803e-11ea-91ed-611abf181ec2.png

* Fields-> :doc:`Attractor Field </nodes/field/attractor_field_mk2>`
* Fields-> :doc:`Vector Field Lines </nodes/field/vector_field_lines>`
* Spacial-> :doc:`Vector P Field </nodes/spatial/homogenous_vector_field>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Make a vector field as a vector product of noise field and an attraction field:

.. image:: https://user-images.githubusercontent.com/284644/79495812-9be49d00-803e-11ea-8ea0-9f9cfd7dc01e.png
  :target: https://user-images.githubusercontent.com/284644/79495812-9be49d00-803e-11ea-8ea0-9f9cfd7dc01e.png

* Fields-> :doc:`Attractor Field </nodes/field/attractor_field_mk2>`
* Fields-> :doc:`Noise Vector Field </nodes/field/noise_vfield>`
* Spacial-> :doc:`Vector P Field </nodes/spatial/homogenous_vector_field>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Apply such a field to a plane:

.. image:: https://user-images.githubusercontent.com/284644/79495805-9ab37000-803e-11ea-9fb4-4eff7839cd23.png
  :target: https://user-images.githubusercontent.com/284644/79495805-9ab37000-803e-11ea-9fb4-4eff7839cd23.png

* Fields-> :doc:`Attractor Field </nodes/field/attractor_field_mk2>`
* Fields-> :doc:`Noise Vector Field </nodes/field/noise_vfield>`
* Surfaces-> :doc:`Plane (Surface) </nodes/surface/plane>`
* Surfaces-> :doc:`Apply Field to Surface </nodes/surface/apply_field_to_surface>`
* Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`