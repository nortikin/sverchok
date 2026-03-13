RBF Vector Field
================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/91843f6d-fe55-4a20-b48b-f062ce73b28f
  :target: https://github.com/nortikin/sverchok/assets/14288520/91843f6d-fe55-4a20-b48b-f062ce73b28f

Dependencies
------------

This node optionally uses SciPy_ library to work.

.. _SciPy: https://scipy.org/

Functionality
-------------

This node generates a Vector Field for given set of points in 3D space and
corresponding vector field values (vectors), by use of RBF_ method. Depending
on node parameters, the field can be interpolating, i.e. have exactly the
provided values in the provided points, or only approximating.

.. _RBF: http://www.scholarpedia.org/article/Radial_basis_function

.. image:: https://github.com/nortikin/sverchok/assets/14288520/f329b42f-367c-43cf-93f4-afce5f944492
  :target: https://github.com/nortikin/sverchok/assets/14288520/f329b42f-367c-43cf-93f4-afce5f944492

Inputs
------

This node has the following inputs:

* **VerticesFrom**. The set of points where the values of the vector field are
  known. This input is mandatory.
* **VerticesTo**. The values of the vector field (i.e. vectors) in points
  defined by **VerticesFrom** input. This input is mandatory.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/8b9e9bbb-aa10-494e-a96b-8e0681a8bee4
      :target: https://github.com/nortikin/sverchok/assets/14288520/8b9e9bbb-aa10-494e-a96b-8e0681a8bee4

* **Epsilon**. Epsilon parameter of used RBF function; it affects the shape of
  generated field. The default value is 1.0.
* **Smooth**. Smoothness parameter of used RBF function. If this is zero, then
  the field will have exactly the specified values in all provided points;
  otherwise, it will be only an approximating field. The default value is 0.0.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/1e639272-7a9b-4c5f-9749-5ed969a4feb6
      :target: https://github.com/nortikin/sverchok/assets/14288520/1e639272-7a9b-4c5f-9749-5ed969a4feb6

Parameters
----------

This node has the following parameters:

* **Field type**. The available options are:

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/06c34294-1f26-44d7-b46d-b884a51073b6
      :target: https://github.com/nortikin/sverchok/assets/14288520/06c34294-1f26-44d7-b46d-b884a51073b6

  * **Relative**. The node will output a "relative" vector field, i.e. it will
    be supposed to work with :doc:`Fields->Apply Vector Field </nodes/field/vector_field_apply>` node. The vectors in
    **VerticesTo** input are supposed to be "force vectors", i.e. vectors that
    should be added to points in **VectorsFrom** input.
  * **Absolute**. The node will output an "absolute" vector field, i.e. it will
    be supposed to work with :doc:`Fields->Evaluate Vector Field </nodes/field/vector_field_eval>` node. The vectors in
    **VerticesTo** input are supposed to be points where points from
    **VerticesFrom** input should be mapped to.

  The default option is **Relative**.

* **Function**. The specific function used by the node. The available values are:

  * Multi Quadric
  * Inverse
  * Gaussian
  * Cubic
  * Quintic
  * Thin Plate

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/da412d29-d035-4dcf-b2eb-a4413dbd50f3
      :target: https://github.com/nortikin/sverchok/assets/14288520/da412d29-d035-4dcf-b2eb-a4413dbd50f3

  The default function is Multi Quadric.

Outputs
-------

This node has the following output:

* **Field**. The generated vector field.

Example of usage
----------------

Define eight "force" vectors for each of eight vertices of a cube. Build an interpolating vector field for such vectors. Then apply it to better subdivided cube:

.. image:: https://user-images.githubusercontent.com/284644/87243779-19f3ec80-c452-11ea-8570-b95db6e11efb.png
  :target: https://user-images.githubusercontent.com/284644/87243779-19f3ec80-c452-11ea-8570-b95db6e11efb.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Fields-> :doc:`Apply Vector Field </nodes/field/vector_field_apply>`
* Number-> :doc:`List Input </nodes/number/list_input>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

.. image:: https://github.com/nortikin/sverchok/assets/14288520/e1035edc-cec7-47b1-8fb6-f6b3e01827d6
  :target: https://github.com/nortikin/sverchok/assets/14288520/e1035edc-cec7-47b1-8fb6-f6b3e01827d6

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Generator-> :doc:`Segment </nodes/generator/segment>`
* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Fields-> :doc:`Evaluate Vector Field </nodes/field/vector_field_eval>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Vector-> :doc:`Vector Polar Input </nodes/vector/vector_polar_in>`
* ADD: Vector-> :doc:`Vector Math </nodes/vector/math_mk3>`
* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`