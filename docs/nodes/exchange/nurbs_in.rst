NURBS In
========

Dependencies
------------

This node requires Geomdl_ library to work.

.. _Geomdl: https://onurraufbingol.com/NURBS-Python/

Functionality
-------------

This node allows to bring NURBS_ Curve and / or Surface objects from Blender's scene into Sverchok.

.. _NURBS: https://en.wikipedia.org/wiki/Non-uniform_rational_B-spline

Inputs
------

This node does not have any inputs.

Operators
---------

This node has the following operator button:

* **GET**. When pressed, the node will update the list of objects bringed into
  Sverchok with a list of currently selected objects. If there are objects
  along selected ones, which are not NURBS curves or surfaces, the node will
  skip them.

Parameters
----------

This node has the following parameters:

* **Sort**. If checked, the node will sort selected objects by name. Checked by default.
* **Apply matricess**. If checked, the node will apply all transforms to
  Blender's objects before bringing the coordinates into Sverchok. Checked by
  default.

In the lower part of the node, the list of currently imported objects is shown.

