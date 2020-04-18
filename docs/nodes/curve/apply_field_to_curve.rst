Apply Field to Curve
====================

Functionality
-------------

This node generates a Curve object by taking another Curve and "bending" it
according to some Vector Field. More precisely, it generates a curve, each
point of which is calculated as `x + Coefficient * VectorPoint(x)`.

Curve domain: the same as the domain of curve being deformed.

Inputs
------

This node has the following inputs:

* **Field**. Vector field to be applied to the curve. This input is mandatory.
* **Curve**. Curve to be "bent" by vector field. This input is mandatory.
* **Coefficient**. Vector field application coefficient (0 means vector field
  will have no effect). The default value is 1.0.

Parameters
----------

This node has no parameters.

Outputs
-------

This node has the following output:

* **Curve**. The curve modified by vector field.

Example of usage
----------------

Several Line curves modified by Noise vector field:

.. image:: https://user-images.githubusercontent.com/284644/77443601-fd816500-6e0c-11ea-9ed2-0516eba95951.png

