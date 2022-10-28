Insert Knot (NURBS Surface)
===========================

Functionality
-------------

This node performs "knot insertion" operation on a NURBS Surface object.

Given a NURBS Surface, the node adds the provided value in the surface's U- or
V-knotvector. If the provided value is already present in the knotvector, it's
multiplicity will be increased.

This node can work only with NURBS surfaces.

It is possible to provide a list of knot values (and corresponding
multiplicities) for each surface.

Inputs
------

This node has the following inputs:

* **Surface**. The Surface object to work with. This input is mandatory.
* **Knot**. The value of the new knot. The default value is 0.5.
* **Count**. Number of times the knot is to be inserted. The default value is 0.

Parameters
----------

This node has the following parameter:

* **Parameter**. This defines the parametric direction, for which to insert the
  knot. The available values are **U** and **V**. The default value is **U**.

Outputs
-------

This node has the following output:

* **Surface**. The resulting Surface object.

