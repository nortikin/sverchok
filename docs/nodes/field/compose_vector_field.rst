Compose Vector Field
====================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/ad20fcb7-7cf0-4275-9598-c7f609889b44
  :target: https://github.com/nortikin/sverchok/assets/14288520/ad20fcb7-7cf0-4275-9598-c7f609889b44

Functionality
-------------

This node generates a Vector Field by composing it from three Scalar Fields which represent different coordinates of the vectors.

Inputs
------

Names of the inputs depend on coordinate system defined in the **Coordinates** parameter:

* **X** / **Rho** / **Rho**. The first scalar field. The input is mandatory.
* **Y** / **Phi** / **Phi**. The second scalar field. The input is mandatory.
* **Z** / **Z** / **Theta**. The third scalar field. The input is mandatory.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/cf8d285a-4ff8-42cb-b27c-9994e0989be1
  :target: https://github.com/nortikin/sverchok/assets/14288520/cf8d285a-4ff8-42cb-b27c-9994e0989be1

Parameters
----------

This node has the following parameter:

* **Coordinates**. This defines the coordinate system being used. The available modes are:

  * **Cartesian**. Compose the vector field from X, Y and Z fields.
  * **Cylindrical**. Compose the vector field from Rho, Phi and Z fields.
  * **Spherical**. Compose the vector field from Rho, Phi and Theta fields.

Outputs
-------

This node has the following output:

* **Field**. The generated vector field.

Example of usage
----------------

Compose the vector field from three attraction fields:

.. image:: https://user-images.githubusercontent.com/284644/79472827-c07c4d00-801d-11ea-8ada-7494115955cc.png
  :target: https://user-images.githubusercontent.com/284644/79472827-c07c4d00-801d-11ea-8ada-7494115955cc.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Fields-> :doc:`Attractor Field </nodes/field/attractor_field_mk2>`
* Fields-> :doc:`Vector Field Graph </nodes/field/vector_field_graph>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`