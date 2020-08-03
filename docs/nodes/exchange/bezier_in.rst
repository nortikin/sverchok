Bezier In
=========

Functionality
-------------

This node allows to bring Bezier_ Curve objects from Blender's scene into Sverchok.

.. _Bezier: https://en.wikipedia.org/wiki/B%C3%A9zier_curve

Inputs
------

This node does not have any inputs.

Operators
---------

This node has the following operator button:

* **GET**. When pressed, the node will update the list of objects bringed into
  Sverchok with a list of currently selected objects. If there are objects
  along selected ones, which are not Bezier curves, the node will skip them.

Parameters
----------

This node has the following parameters:

* **Sort**. If checked, the node will sort selected objects by name. Checked by default.
* **Apply matricess**. If checked, the node will apply all transforms to
  Blender's objects before bringing the coordinates into Sverchok. Checked by
  default.

In the lower part of the node, the list of currently imported objects is shown.

Outputs
-------

This node has the following outputs:

* **Curves**. Generated Curve objects.
* **Matrices**. Transformation matrices of selected objects.

