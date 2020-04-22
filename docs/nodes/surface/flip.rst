Flip Surface
============

Functionality
-------------

This node generates a Surface by inverting the direction of parametrization of another Surface in either U or V direction, or in both directions. In other words, it generates the surface identical to the provided one, but flipped in one or two directions.

Note that flipping the surface in one of directions will flip it's normals. Flipping the surface in two directions will keep original normals.

Surface domain: the same as of original surface.

Inputs
------

This node has the following input:

* **Surface**. The surface to be flipped. This input is mandatory.

Parameters
----------

This node has the following parameter:

* **Flip**. The direction in which the surface parametrization is to be
  flipped. The available values are **UV** (both directions), **U** and **V**.
  The default value is **UV**.

Outputs
-------

This node has the following output:

* **Surface**. The flipped surface.

