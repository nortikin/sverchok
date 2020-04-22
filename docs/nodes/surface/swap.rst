Swap Surface U/V
================

Functionality
-------------

This node generates a Surface by swapping U and V directions of another Surface
parametrizations. More precisely, given the surface defined by formula `P =
S(U, V)`, it generates the surface defined by formula `P = S(V, U)`. This is
the same surface as the original one, but with another paramertization.

Surface domain: in the U direction - the same as of original surface in the V
direction; and vice versa, in the V direction - the same as of original surface
in the U direction.

Inputs
------

This node has the following input:

* **Surface**. The surface to be processed. This input is mandatory.

Outputs
-------

This node has the following output:

* **Surface**. The new surface.

