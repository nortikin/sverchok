Apply Vector Field
==================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/33c5d489-170a-48b1-9d8f-e091ca4877ec
  :target: https://github.com/nortikin/sverchok/assets/14288520/33c5d489-170a-48b1-9d8f-e091ca4877ec

Functionality
-------------

This node applies the Vector Field to provided points. More precisely, given
the vector field VF (which is a function from points to vectors) and a point X,
it calculates new point as `X + K * VF(X)`.

This node can also apply the field iteratively, by calculating `X + K*VF(X) +
K*VF(X + K*VF(X)) + ...`. In other words, it can apply the field to the result
of the first application, and repeat that several times.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/a3cf2027-53b1-4077-9b59-b2cd1dec0e8b
  :target: https://github.com/nortikin/sverchok/assets/14288520/a3cf2027-53b1-4077-9b59-b2cd1dec0e8b

Inputs
------

This node has the following inputs:

* **Field**. The vector field to be applied. This input is mandatory.
* **Vertices**. The points to which the field is to be applied. The default value is `(0, 0, 0)`.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/fe15638d-2f74-425b-b36f-64f00934b8d0
      :target: https://github.com/nortikin/sverchok/assets/14288520/fe15638d-2f74-425b-b36f-64f00934b8d0

* **Coefficient**. The vector field application coefficient. The default value is 1.0.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/475a7c12-1d8a-4eb1-bf5c-22c6d4781f0c
      :target: https://github.com/nortikin/sverchok/assets/14288520/475a7c12-1d8a-4eb1-bf5c-22c6d4781f0c

* **Iterations**. Number of vector field application iterations. For example, 2
  will mean that the node returns the result of field application to the result
  of first application. The default value is 1.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/c1c7af95-933b-4bb9-8da5-c068ff760dbf
      :target: https://github.com/nortikin/sverchok/assets/14288520/c1c7af95-933b-4bb9-8da5-c068ff760dbf

Parameters
----------

* **Output NumPy**. Outputs NumPy arrays in stead of regular python lists. Improves performance

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/6fc14f4d-932a-4fe3-bdec-dded8952f5ea
      :target: https://github.com/nortikin/sverchok/assets/14288520/6fc14f4d-932a-4fe3-bdec-dded8952f5ea

Outputs
-------

This node has the following output:

* **Vertices**. The result of the vector field application to the original points.

Performance Notes
-----------------

This node works faster when the vertices list are NumPy arrays

Examples of usage
-----------------

Example of Description:

.. image:: https://github.com/nortikin/sverchok/assets/14288520/dde29284-518a-40ad-8e12-84a043037bbe
  :target: https://github.com/nortikin/sverchok/assets/14288520/dde29284-518a-40ad-8e12-84a043037bbe

* Generator-> :doc:`Segment </nodes/generator/segment>`
* Fields-> :doc:`Rotation Field </nodes/field/rotation_field>`
* Modifiers->Modifier Make-> :doc:`UV Connection </nodes/modifier_make/uv_connect>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* SUB: Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* Number-> :doc:`Float to Integer </nodes/number/float_to_int>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Logic-> :doc:`Logic Functions </nodes/logic/logic_node>`
* Logic-> :doc:`Switch </nodes/logic/switch_MK2>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* List->List Struct-> :doc:`List Item </nodes/list_struct/item>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Viewer Index+ </nodes/viz/viewer_idx28>`

.. image:: https://github.com/nortikin/sverchok/assets/14288520/694fb6d9-6de6-42f5-9db3-aff214bb1c20
  :target: https://github.com/nortikin/sverchok/assets/14288520/694fb6d9-6de6-42f5-9db3-aff214bb1c20

---------

Apply noise vector field to the points of straight line segment:

.. image:: https://user-images.githubusercontent.com/284644/79487691-15c25980-8032-11ea-93e9-51f9b54bd36e.png
  :target: https://user-images.githubusercontent.com/284644/79487691-15c25980-8032-11ea-93e9-51f9b54bd36e.png

* Generator-> :doc:`Segment </nodes/generator/segment>`
* Fields-> :doc:`Noise Vector Field </nodes/field/noise_vfield>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Apply the same field to the same points, by only by a small amount; then apply the same field to the resulting points, and repeat that 10 times:

.. image:: https://user-images.githubusercontent.com/284644/79487987-7b164a80-8032-11ea-8197-c78314843ffa.png
  :target: https://user-images.githubusercontent.com/284644/79487987-7b164a80-8032-11ea-8197-c78314843ffa.png

* Generator-> :doc:`Segment </nodes/generator/segment>`
* Fields-> :doc:`Noise Vector Field </nodes/field/noise_vfield>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`