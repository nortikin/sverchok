Coordinate Scalar Field
=======================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/0be09d92-f2da-40e3-96b1-a7565f66cbc6
  :target: https://github.com/nortikin/sverchok/assets/14288520/0be09d92-f2da-40e3-96b1-a7565f66cbc6

Functionality
-------------

This node generates a Scalar Field, the value of which at each point equals to
one of coordinates of that point. For example, this node can generate a scalar
field generated by function `S(x,y,z) = x`.

Cartesian, cylindrical and spherical coordinates are supported.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/17b237ba-b394-42c4-ad8c-a8f41da2a98c
  :target: https://github.com/nortikin/sverchok/assets/14288520/17b237ba-b394-42c4-ad8c-a8f41da2a98c

Inputs
------

This node has no inputs.

Parameters
----------

This node has the following parameter:

* **Coordinate**. The coordinate to use. The available values are:

  * **X**. Cartesian X coordinate. This option is the default one.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/cabfb96e-f2b1-430c-8355-47a46c7d8685
      :target: https://github.com/nortikin/sverchok/assets/14288520/cabfb96e-f2b1-430c-8355-47a46c7d8685

  * **Y**. Cartesian Y coordinate.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/df3efe56-83ee-4ccb-b514-138c7600724d
      :target: https://github.com/nortikin/sverchok/assets/14288520/df3efe56-83ee-4ccb-b514-138c7600724d

  * **Z**. Cartesian Z coordinate, or cylindrical Z coordinate - they are identical.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/b57f0e6a-e0b5-48b6-9060-4db22f62ec67
      :target: https://github.com/nortikin/sverchok/assets/14288520/b57f0e6a-e0b5-48b6-9060-4db22f62ec67

  * **Rho - Cylindrical**. Cylindrical Rho coordinate.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/06f6f981-554c-4882-8304-5d2bd1b8aa58
      :target: https://github.com/nortikin/sverchok/assets/14288520/06f6f981-554c-4882-8304-5d2bd1b8aa58

  * **Phi**. Cylindrical or spherical Phi coordinate - they are identical.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/ee7f4a5a-8c30-4794-afe5-21cbb5809b5d
      :target: https://github.com/nortikin/sverchok/assets/14288520/ee7f4a5a-8c30-4794-afe5-21cbb5809b5d

  * **Rho - Spherical**. Spherical Rho coordinate.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/55de4207-31ce-4648-9a5b-70731368dc3d
      :target: https://github.com/nortikin/sverchok/assets/14288520/55de4207-31ce-4648-9a5b-70731368dc3d

  * **Theta - Spherical**. Spherical Theta coordinate.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/c6fca188-671c-4b80-ac9e-15cdb6c6ac9c
      :target: https://github.com/nortikin/sverchok/assets/14288520/c6fca188-671c-4b80-ac9e-15cdb6c6ac9c

Outputs
-------

This node has the following output:

* **Field**. The generated scalar field.

Example of usage
----------------

.. image:: https://github.com/nortikin/sverchok/assets/14288520/d7eb084f-7773-4d3e-8299-2b4b8d1ca690
  :target: https://github.com/nortikin/sverchok/assets/14288520/d7eb084f-7773-4d3e-8299-2b4b8d1ca690

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Surfaces-> :doc:`Marching Cubes </nodes/surface/marching_cubes>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`
* Color-> :doc:`Color In </nodes/color/color_in_mk1>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

This node is useful in combination with "scalar field math", "vector field math", "compose vector field" and similar nodes. For example:

.. image:: https://user-images.githubusercontent.com/284644/80824284-8e5f1380-8bf7-11ea-86e1-c7f590deb247.png
  :target: https://user-images.githubusercontent.com/284644/80824284-8e5f1380-8bf7-11ea-86e1-c7f590deb247.png

* Surfaces-> :doc:`Plane (Surface) </nodes/surface/plane>`
* Surfaces-> :doc:`Apply Field to Surface </nodes/surface/apply_field_to_surface>`
* Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`
* Fields-> :doc:`Scalar Field Math </nodes/field/scalar_field_math>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`