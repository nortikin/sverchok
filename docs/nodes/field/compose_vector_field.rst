Compose Vector Field
====================

Functionality
-------------

This node generates a Vector Field by composing it from three Scalar Fields which represent different coordinates of the vectors.

Inputs
------

Names of the inputs depend on coordinate system defined in the **Coordinates** parameter:

* **X** / **Rho** / **Rho**. The first scalar field. The input is mandatory.
* **Y** / **Phi** / **Phi**. The second scalar field. The input is mandatory.
* **Z** / **Z** / **Theta**. The third scalar field. The input is mandatory.

Parameters
----------

This node has the following parameter:

* **Coordinates**. This defines the coordinate system being used. The available modes are:

  * **Carthesian**. Compose the vector field from X, Y and Z fields.
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

