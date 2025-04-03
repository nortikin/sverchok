Decompose Vector Field
======================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/90c65c97-8446-4401-b451-63f8e2bec00a
  :target: https://github.com/nortikin/sverchok/assets/14288520/90c65c97-8446-4401-b451-63f8e2bec00a

Functionality
-------------

This node generates three Scalar Fields by decomposing a Vector Field into it's coordinates.

Inputs
------

This node has the following input:

* **Field**. The vector field to be decomposed. The input is mandatory.

Parameters
----------

This node has the following parameter:

* **Coordinates**. This defines the coordinate system to be used. The available options are:

  * **Cartesian**. The vector field is decomposed into X, Y and Z fields.
  * **Cylindrical**. The vector field is decomposed into Rho, Phi and Z fields.
  * **Spherical**. The vector field is decomposed into Rho, Phi and Theta fields.

  The default mode is **Cartesian**.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/3c46726b-7bec-4ff6-8129-db98fe31c097
      :target: https://github.com/nortikin/sverchok/assets/14288520/3c46726b-7bec-4ff6-8129-db98fe31c097

Outputs
-------

The names of the outputs depend on the **Coordinates** parameter:

* **X** / **Rho** / **Rho**. The first scalar field.
* **Y** / **Phi** / **Phi**. The second scalar field.
* **Z** / **Z** / **Theta**. The third scalar field.

Example of usage
----------------

.. image:: https://github.com/nortikin/sverchok/assets/14288520/031274cb-f44e-41ff-bc8d-ee84bcc581b2
  :target: https://github.com/nortikin/sverchok/assets/14288520/031274cb-f44e-41ff-bc8d-ee84bcc581b2

* Generator->Generatots Extended-> :doc:`Spiral </nodes/generators_extended/spiral_mk2>`
* Fields-> :doc:`Vector Field Formula </nodes/field/vector_field_formula>`
* Fields-> :doc:`Evaluate Scalar Field </nodes/field/scalar_field_eval>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Number-> :doc:`Map Range </nodes/number/range_map>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Metaball Out </nodes/viz/viewer_metaball>`

.. image:: https://github.com/nortikin/sverchok/assets/14288520/ae879c61-3759-48e5-82dc-74e34bcb5ff9
  :target: https://github.com/nortikin/sverchok/assets/14288520/ae879c61-3759-48e5-82dc-74e34bcb5ff9

---------

Use only one component of some attraction vector field to scale the cubes:

.. image:: https://user-images.githubusercontent.com/284644/79474322-ae9ba980-801f-11ea-9cb0-0d6d5085e22a.png
  :target: https://user-images.githubusercontent.com/284644/79474322-ae9ba980-801f-11ea-9cb0-0d6d5085e22a.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Fields-> :doc:`Attractor Field </nodes/field/attractor_field_mk2>`
* Fields-> :doc:`Evaluate Scalar Field </nodes/field/scalar_field_eval>`
* Spacial-> :doc:`Vector P Field </nodes/spatial/homogenous_vector_field>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`