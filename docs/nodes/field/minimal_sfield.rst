RBF Scalar Field
================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/7b7cc987-f48d-40b5-886b-4f716f3b916b
  :target: https://github.com/nortikin/sverchok/assets/14288520/7b7cc987-f48d-40b5-886b-4f716f3b916b

Dependencies
------------

This node optionally uses SciPy_ library to work.

.. _SciPy: https://scipy.org/

Functionality
-------------

This node generates a Scalar Field for given set of points in 3D space and
corresponding scalar field values, by use of RBF_ method. Depending on node
parameters, the field can be interpolating, i.e. have exactly the provided
values in the provided points, or only approximating.

.. _RBF: http://www.scholarpedia.org/article/Radial_basis_function

.. image:: https://github.com/nortikin/sverchok/assets/14288520/05f3c475-dd46-43db-8e48-f1ef383f8dc9
  :target: https://github.com/nortikin/sverchok/assets/14288520/05f3c475-dd46-43db-8e48-f1ef383f8dc9

Inputs
------

This node has the following inputs:

* **Vertices**. The set of points where the values of scalar fields are known.
  This input is mandatory.
* **Values**. Values of the scalar field in the specified points. This input is
  mandatory.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/51175cf8-c62b-4d49-a73d-cbe9a36dd67e
  :target: https://github.com/nortikin/sverchok/assets/14288520/51175cf8-c62b-4d49-a73d-cbe9a36dd67e

* **Epsilon**. Epsilon parameter of used RBF function; it affects the shape of
  generated field. The default value is 1.0.
* **Smooth**. Smoothness parameter of used RBF function. If this is zero, then
  the field will have exactly the specified values in all provided points;
  otherwise, it will be only an approximating field. The default value is 0.0.

Parameters
----------

This node has the following parameter:

* **Function**. The specific function used by the node. The available values are:

  * Multi Quadric
  * Inverse
  * Gaussian
  * Cubic
  * Quintic
  * Thin Plate

      .. image:: https://github.com/nortikin/sverchok/assets/14288520/515076c7-0f6c-4ffe-a29a-6019aa6960b4
        :target: https://github.com/nortikin/sverchok/assets/14288520/515076c7-0f6c-4ffe-a29a-6019aa6960b4


  The default function is Multi Quadric.

Outputs
-------

This node has the following output:

* **Field**. The generated scalar field.

Example of usage
----------------

The field is generated by following data:

* In the origin, it has value of 0;
* In eight vertices of 2x2x2 cube, it has the value of 2;
* In the vertices of 4x4x4 cube, it has the value of 4.

.. image:: https://user-images.githubusercontent.com/284644/87240833-7f39e480-c436-11ea-9706-d7e55849c136.png
  :target: https://user-images.githubusercontent.com/284644/87240833-7f39e480-c436-11ea-9706-d7e55849c136.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Fields-> :doc:`Scalar Field Graph </nodes/field/scalar_field_graph>`
* Number-> :doc:`List Input </nodes/number/list_input>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Let's move the smaller cube slightly and generate an iso-surface instead of iso-curves:

.. image:: https://user-images.githubusercontent.com/284644/87240927-4ea67a80-c437-11ea-9b36-04b56a6ae696.png
  :target: https://user-images.githubusercontent.com/284644/87240927-4ea67a80-c437-11ea-9b36-04b56a6ae696.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Surfaces-> :doc:`Marching Cubes </nodes/surface/marching_cubes>`
* Number-> :doc:`List Input </nodes/number/list_input>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

.. image:: https://github.com/nortikin/sverchok/assets/14288520/055dc1d2-6c59-4568-b095-52b74ac27d52
  :target: https://github.com/nortikin/sverchok/assets/14288520/055dc1d2-6c59-4568-b095-52b74ac27d52

* Generator-> :doc:`Segment </nodes/generator/segment>`
* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Generator->Generators Extended :doc:`Torus Knot </nodes/generators_extended/torus_knot_mk2>`
* Generator->Generatots Extended-> :doc:`Spiral </nodes/generators_extended/spiral_mk2>`
* Surfaces-> :doc:`Marching Cubes </nodes/surface/marching_cubes>`
* Transform-> :doc:`Noise Displace </nodes/transforms/noise_displace>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`
* List->List Struct-> :doc:`List Repeater </nodes/list_struct/repeater>`
* List->List Struct-> :doc:`List Item Insert </nodes/list_struct/item_insert>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

.. image:: https://github.com/nortikin/sverchok/assets/14288520/9d961a3f-3962-431e-a1d2-408d6664190f
  :target: https://github.com/nortikin/sverchok/assets/14288520/9d961a3f-3962-431e-a1d2-408d6664190f