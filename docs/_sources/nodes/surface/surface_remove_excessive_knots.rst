Remove Excessive Knots (NURBS Surface)
======================================

Functionality
-------------

This node performs "knot removal" procedure for a NURBS surface, trying to
remove as many knots, and as many times, as it is possible, without changing
the shape of the surface too much. Allowed change of shape is controlled by
"tolerance" parameter.

This node can only work with NURBS surfaces.

Inputs
------

This node has the following input:

* **Surface**. The Surface object to work on. This input is mandatory.

Parameters
----------

This node has the following parameters:

* **Direction**. This defines, in which parametric directions should the knot
  removal procedure be performed. The available options are **U+V** (both
  directions), **U** and **V**. The default value is **U+V**.
* **Tolerance**. This defines how much is it allowed to change the shape of the
  surface by knot removal procedure. The default value is ``10^-6``.

Outputs
-------

This node has the following output:

* **Surface**. The resulting Surface object.

