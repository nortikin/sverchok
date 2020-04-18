Field Differential Operations
=============================

Functionality
-------------

This node calculates Vector or Scalar Field by performing one of supported
differential operations on the fields provided as inputs.

Note that the differentiation is done numerically, and so there is always some
calculation error. The error can be minimizing by adjusting the "step"
parameter.

Inputs
------

This node has the following inputs:

* **SFieldA**. Scalar field to operate on. This input is mandatory when available.
* **VFieldA**. Vector field to operate on. This input is mandatory when available.

The availability of the inputs is defined by the selected operation.

Parameters
----------

This node has the following parameters:

* **Operation**. The differential operation to perform. The available operations are:

  * **Gradient**. Calculate the gradient of the scalar field. The result is a vector field.
  * **Divergence**. Calculate the divergence of the vector field. The result is a scalar field.
  * **Laplacian**. Calculate the Laplace operator on the scalar field. The result is a scalar field.
  * **Rotor**. Calculate the rotor operator on the vector field. The result is a vector field.

* **Step**. Derivatives calculation step. The default value is 0.001. Bigger values give smoother fields.

Outputs
-------

This node has the following outputs:

* **SFieldB**. The resulting scalar field.
* **VFieldB**. The resulting vector field.

Examples of usage
-----------------

Generate a scalar field, calculate it's gradient, and apply that to a cube:

.. image:: https://user-images.githubusercontent.com/284644/79501054-deaa7300-8046-11ea-8cf6-d01471cb1eea.png

