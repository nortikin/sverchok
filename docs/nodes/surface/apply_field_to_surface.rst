Apply Field to Surface
======================

Functionality
-------------

This node generates a Surface by applying some vector field to another Surface.
More precisely, it generates the surface, points of which are calculated as `X
+ K * VF(X)`, where X is the point of initial surface, VF is the vector field,
  and K is some coefficient.

Surface domain: the same as of initial surface.

Inputs
------

This node has the following inputs:

* **Field**. Vector field to apply. This input is mandatory.
* **Surface**. The surface to apply the vector field to. This input is mandatory.
* **Coefficient**. The "strength" coefficient. Value of 0 will output the surface as it was. The default value is 1.0.

Outputs
-------

This node has the following output:

* **Surface**. The generated surface.

Examples of usage
-----------------

Noise field applied to the sphereical surface:

.. image:: https://user-images.githubusercontent.com/284644/79371205-6ae86780-7f6d-11ea-80f7-3bf5ca71c7cf.png

An example with more complex field:

.. image:: https://user-images.githubusercontent.com/284644/79371656-23aea680-7f6e-11ea-97e1-1ac22cb194a1.png

