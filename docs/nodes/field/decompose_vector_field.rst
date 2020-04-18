Decompose Vector Field
======================

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

  * **Carthesian**. The vector field is decomposed into X, Y and Z fields.
  * **Cylindrical**. The vector field is decomposed into Rho, Phi and Z fields.
  * **Spherical**. The vector field is decomposed into Rho, Phi and Theta fields.

  The default mode is **Carthesian**.

Outputs
-------

The names of the outputs depend on the **Coordinates** parameter:

* **X** / **Rho** / **Rho**. The first scalar field.
* **Y** / **Phi** / **Phi**. The second scalar field.
* **Z** / **Z** / **Theta**. The third scalar field.

Example of usage
----------------

Use only one component of some attraction vector field to scale the cubes:

.. image:: https://user-images.githubusercontent.com/284644/79474322-ae9ba980-801f-11ea-9cb0-0d6d5085e22a.png

