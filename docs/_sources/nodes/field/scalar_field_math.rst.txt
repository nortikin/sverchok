Scalar Field Math
=================

Functionality
-------------

This node generates a Scalar Field by executing one of supported mathematical operations on the Scalar Fields provided as inputs.

Inputs
------

This node has the following inputs:

* **FieldA**. The first scalar field. The input is mandatory when available.
* **FieldB**. The second scalar field. The input is mandatory when available.

Parameters
----------

This node has the following parameter:

* **Operation**. This defines the mathematical operation to perform. The available operations are:

  * **Add**. Add two scalar fields.
  * **Sub**. Substract one scalar field from another.
  * **Multiply**. Multiply two scalar fields.
  * **Minimum**. Create a scalar field, the value of which is calculated as
    minimal of values of two scalar fields at the same point.
  * **Maximum**. Create a scalar field, the value of which is calculated as
    maximal of values of two scalar fields at the same point.
  * **Average**. Arithmetic mean (average) of two scalar fields - (A + B)/2.
  * **Negate**. Negate the scalar field values.

Outputs
-------

The node has the following output:

* **FieldC**. The resulting scalar field.

Examples of usage
-----------------

Example #1:

.. image:: https://user-images.githubusercontent.com/284644/79497591-60979d80-8041-11ea-9c23-1e0d6be96708.png

Example #2:

.. image:: https://user-images.githubusercontent.com/284644/79497828-cbe16f80-8041-11ea-957f-54c011afe3a3.png

