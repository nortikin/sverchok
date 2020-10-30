Surface Boundary
================

Functionality
-------------

This node outputs the curve (or curves) which represent the boundaries of some surface. The supported types of surfaces are:

* Plain (plane-like); for such surfaces, the boundary is one closed curve (in
  many cases it will have four non-smooth points).
* Closed in U or in V direction (cylinder-like). For such surface, the boundary
  is represented by two closed curves at two open sides of the surface.

If the surface is closed in both U and V direction (torus-like), then it will not have any boundary.

Inputs
------

This node has the following input:

* **Surface**. The surface to calculate boundary for. This input is mandatory.

Parameters
----------

This node has the following parameters:

* **Cyclic**. This defines whether the surface is closed in some directions. The available options are:

  * **Plain**. The surface is not closed in any direction, so it has single closed curve as a boundary.
  * **U Cyclic**. The surface is closed along the U direction. It has two closed curves as boundary.
  * **V Cyclic**. The surface is closed along the V direction.

* **Concatenate**. This parameter is available only if **Cyclic** parameter is
  set to **Plain**. If checked, then four edges of the surface will be
  concatenated into one Curve object. Otherwise, the node will output four
  separate Curve objects. Checked by default.

Outputs
-------

This node has the following output:

* **Boundary**. Curve or curves representing surface's boundary.

Examples of usage
-----------------

Visualize the boundary of some random plane-like surface:

.. image:: https://user-images.githubusercontent.com/284644/78506070-b8581e00-7790-11ea-9af1-2c3c84264dc8.png

Visualize the boundary of cylinder-like surface:

.. image:: https://user-images.githubusercontent.com/284644/78506074-b9894b00-7790-11ea-9b5b-714a9fc79927.png

