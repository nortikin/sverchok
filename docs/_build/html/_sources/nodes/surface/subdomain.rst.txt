Surface Subdomain
=================

Functionality
-------------

This node generates a Surface, which is defined as a subset of the input
Surface with a smaller range of allowed U and V parameter values. In other
words, the output surface is the same as input one, but with restricted range
of U and V values allowed.

Output surface domain: defined by node inputs.

Output surface parametrization: the same as of input surface.

Inputs
------

This node has the following inputs:

* **Surface**. The surface to cut. This input is mandatory.
* **UMin**, **UMax**. The minimum and maximum values of the new surface's U parameter.
* **VMin**, **VMax**. The minimum and maximum values of the new surface's V parameter.

Outputs
-------

This node has the following output:

* **Surface**. The new surface (the subset of the input surface).

Example of usage
----------------

The formula-generated surface (green) and a subdomain of it (red one):

.. image:: https://user-images.githubusercontent.com/284644/79385737-83af4800-7f82-11ea-96e4-f4fb779646db.png

