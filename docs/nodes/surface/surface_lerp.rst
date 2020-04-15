Surface Lerp
============

Functionality
-------------

This node generates a Surface by calculating the linear interpolation ("lerp") between two other Surfaces.

Surface domain: from 0 to 1 in both directions.

Inputs
------

This node has the following inputs:

* **Surface1**. The first surface for the interpolation. This input is mandatory.
* **Surface2**. The second surface for the interpolation. This input is mandatory.
* **Coefficient**. Interpolation coefficient. Value of 0 will generate the
  surface equivalent to Surface1. Value of 1 will generate the surface
  equivalent to Surface2. The default value is 0.5 (in the middle of two
  surfaces).

Outputs
-------

This node has the following output:

   * **Surface**. The interpolated surface.

Example of usage
----------------

Interpolation of some random surfaces:

.. image:: https://user-images.githubusercontent.com/284644/79361263-7f713380-7f5e-11ea-89de-60c74c4e1594.png

