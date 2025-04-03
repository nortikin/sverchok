Distance From a Point
=====================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/81fbca08-46c5-49a5-9ba3-2d7e5e7babf7
  :target: https://github.com/nortikin/sverchok/assets/14288520/81fbca08-46c5-49a5-9ba3-2d7e5e7babf7

Functionality
-------------

.. image:: https://github.com/nortikin/sverchok/assets/14288520/3a7b31e5-5fc4-4cb9-9699-ebbb1e7e3cfe
  :target: https://github.com/nortikin/sverchok/assets/14288520/3a7b31e5-5fc4-4cb9-9699-ebbb1e7e3cfe

Inputs
------

Parameters
----------

* **Metric**.

   * **Euclidean**. Standard euclidean distance - sqrt(dx*dx + dy*dy + dz*dz)
   * **Chebyshev**. Chebyshev distance - abs(dx, dy, dz)
   * **Manhattan**. Manhattan distance - abs(dx) + abs(dy) + abs(dz)
   * **Custom**. Custom Minkowski metric defined by exponent factor

      .. image:: https://github.com/nortikin/sverchok/assets/14288520/819881bb-4371-4f2f-a0ca-81593dc21448
        :target: https://github.com/nortikin/sverchok/assets/14288520/819881bb-4371-4f2f-a0ca-81593dc21448


* **Exponent**. Exponent for Minkowski metric. Only for Metric is "Custom".

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/5f80a860-a7ca-46f5-b8d4-5e46b4bdda6c
      :target: https://github.com/nortikin/sverchok/assets/14288520/5f80a860-a7ca-46f5-b8d4-5e46b4bdda6c

* **Falloff type**. 

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/eaa82fe0-c7b8-4c6b-9c8c-0a2dc3cf0024
      :target: https://github.com/nortikin/sverchok/assets/14288520/eaa82fe0-c7b8-4c6b-9c8c-0a2dc3cf0024

* **Clamp**. Restrict coefficient with R.
* **Center**. 
* **Amplitude**
* **Coefficient**

Outputs
-------

* **Field**

Examples of usage
-----------------

.. image:: https://github.com/nortikin/sverchok/assets/14288520/0b2fb4f0-ba5d-44d0-9e6c-a33d3f297370
  :target: https://github.com/nortikin/sverchok/assets/14288520/0b2fb4f0-ba5d-44d0-9e6c-a33d3f297370

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Fields-> :doc:`Evaluate Scalar Field </nodes/field/scalar_field_eval>`
* Spacial-> :doc:`Vector P Field </nodes/spatial/homogenous_vector_field>`
* Transform-> :doc:`Noise Displace </nodes/transforms/noise_displace>`
* Number-> :doc:`Map Range </nodes/number/range_map>`
* MUL X: Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Matrix-> :doc:`Matrix Math </nodes/matrix/matrix_math>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://github.com/nortikin/sverchok/assets/14288520/d5984e13-43c9-495e-9545-90055055b157
  :target: https://github.com/nortikin/sverchok/assets/14288520/d5984e13-43c9-495e-9545-90055055b157