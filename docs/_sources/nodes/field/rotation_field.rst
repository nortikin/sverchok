Rotation Field
==============

.. image:: https://github.com/nortikin/sverchok/assets/14288520/024400d8-69ae-4482-9ab7-f22e67df09c0
  :target: https://github.com/nortikin/sverchok/assets/14288520/024400d8-69ae-4482-9ab7-f22e67df09c0

Functionality
-------------

This node generates a Vector Field which is calculated as
force rotating points around some axis. Several physics-like falloff laws are supported.
Falloffs similar to standard proportional editing mode are supported too (they
are marked with `(P)` in the name).

.. image:: https://github.com/nortikin/sverchok/assets/14288520/5ef50da8-6d61-4266-8e31-8db6d66262fe
  :target: https://github.com/nortikin/sverchok/assets/14288520/5ef50da8-6d61-4266-8e31-8db6d66262fe

Inputs
------

This node has the following inputs:

* **Location**. Point on the rotating axis

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/bee32d7c-da5b-4e6f-9250-817e92c032fd
      :target: https://github.com/nortikin/sverchok/assets/14288520/bee32d7c-da5b-4e6f-9250-817e92c032fd

  It is possible to provide several location points. The default value is `(0, 0, 0)` (origin).

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/f75c6563-c894-41d4-bade-b4fbb30b0597
      :target: https://github.com/nortikin/sverchok/assets/14288520/f75c6563-c894-41d4-bade-b4fbb30b0597

* **Direction**. Direction of the rotation axis.  The default value is `(0, 0, 1)` (Z axis).

.. image:: https://github.com/nortikin/sverchok/assets/14288520/25cdcca7-0347-4cbe-801c-6d003a3226f5
  :target: https://github.com/nortikin/sverchok/assets/14288520/25cdcca7-0347-4cbe-801c-6d003a3226f5

.. image:: https://github.com/nortikin/sverchok/assets/14288520/356a88c5-aa31-41d1-9d27-dba7c75acc3e
  :target: https://github.com/nortikin/sverchok/assets/14288520/356a88c5-aa31-41d1-9d27-dba7c75acc3e

* **Amplitude**. The attracting force amplitude. The default value is 0.5.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/bd77d08b-d5eb-4eb0-9506-31501db70d2c
      :target: https://github.com/nortikin/sverchok/assets/14288520/bd77d08b-d5eb-4eb0-9506-31501db70d2c

* **Coefficient**. The coefficient used in the attracting force falloff
  calculation formula. The exact meaning of this input depends on fallof type:

   * If **Falloff type** is set to **Inverse exponent** or **Gauss**, then this
     is the coefficient K in the corresponding formula: ``exp(-K*R)`` or
     ``exp(-K*x^2/2)``.

      .. image:: https://github.com/nortikin/sverchok/assets/14288520/12681a87-6547-4574-86f2-e81c923362ff
        :target: https://github.com/nortikin/sverchok/assets/14288520/12681a87-6547-4574-86f2-e81c923362ff

      .. image:: https://github.com/nortikin/sverchok/assets/14288520/42e354b8-baaa-4de5-a7b7-c7e291de4f44
        :target: https://github.com/nortikin/sverchok/assets/14288520/42e354b8-baaa-4de5-a7b7-c7e291de4f44

   * If **Falloff type** is set to one of proportional editing modes (one
     starting with ``(P)`` prefix), this is the radius of proportional editing
     falloff.

        .. image:: https://github.com/nortikin/sverchok/assets/14288520/475f6396-80b6-437b-8570-1f52420891b6
          :target: https://github.com/nortikin/sverchok/assets/14288520/475f6396-80b6-437b-8570-1f52420891b6

        .. image:: https://github.com/nortikin/sverchok/assets/14288520/d7ea8b5e-6cdc-40e7-a2fd-5541197a359d
          :target: https://github.com/nortikin/sverchok/assets/14288520/d7ea8b5e-6cdc-40e7-a2fd-5541197a359d

   * For **other** falloff types, this input is not available.

   The default value is 0.5.

Parameters
----------

This node has the following parameters:

* **Join mode**. This determines how the distance is calculated when multiple
  attraction centers are provided. The available values are:

  * **Average**. Calculate the average of the attracting forces towards the
    provided centers. This mode is used in physics. This option is the default
    one.
  * **Nearest**. Use only the force of the attraction towards the nearest attraction center.
  * **Separate**. Generate a separate field of attraction force for each attraction center.

   This parameter is not available when the **Attractor type** is set to **Mesh - Faces**.

* **Clamp**. If checked, then the amplitude of attracting force vector will be
  restricted with the distance to attractor object. Unchecked by default.

Outputs
-------

* **VField**. Vector field of the rotating force.

Examples of usage
-----------------

.. image:: https://github.com/nortikin/sverchok/assets/14288520/ebd38346-a271-456f-a8c1-22c5d9dfd2fb
  :target: https://github.com/nortikin/sverchok/assets/14288520/ebd38346-a271-456f-a8c1-22c5d9dfd2fb

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Generator-> :doc:`Segment </nodes/generator/segment>`
* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Fields-> :doc:`Apply Vector Field </nodes/field/vector_field_apply>`
* Fields-> :doc:`Evaluate Vector Field </nodes/field/vector_field_eval>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* MUL X,Y: Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* LEN: Vector-> :doc:`Vector Math </nodes/vector/math_mk3>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

.. image:: https://user-images.githubusercontent.com/10011941/107337942-45f45080-6abb-11eb-8245-74afc5fab5df.png
  :target: https://user-images.githubusercontent.com/10011941/107337942-45f45080-6abb-11eb-8245-74afc5fab5df.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Fields-> :doc:`Apply Vector Field </nodes/field/vector_field_apply>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`