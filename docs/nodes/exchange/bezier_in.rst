Bezier Input
============

.. image:: https://github.com/user-attachments/assets/7225f2ce-0957-40f8-bb86-9542c219e008
  :target: https://github.com/user-attachments/assets/7225f2ce-0957-40f8-bb86-9542c219e008

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

* **Sort**. If checked, the node will sort selected objects by name in "Get Selection". Checked by default.
* **Apply matrices**. If checked, the node will apply all transforms to
  Blender's objects before bringing the coordinates into Sverchok. Checked by
  default.
* **Concatenate segments**. If checked, join Bezier segments of the curve into
  a single Curve object; otherwise, output a separate Curve object for each
  segment.
* **Legacy Mode** - Flats all data in all sockets. 

In the lower part of the node, the list of currently imported objects is shown.

Outputs
-------

This node has the following outputs:

* **Curves**. Generated Curve objects.
* **Cyclic U**. Make this curve or surface a closed loop in the U direction.
* **ControlPoints c0, c1, c2, c3**. Control points of Bezier curves. This output contains a lists of points for each segments of each Bezier curve.
* **Tilt**. Tilt values from Blender's curve object. This output contains one
  value for each Bezier's control point in Blender terms (or, in more strict
  terms, one value for each point where one Bezier segment ends and new one
  starts).
* **Radius**. Radius values from Blender's curve object. Similar to **Tilt** output.
* **Object Names** - Names from objects in Blender Scene
* **Matrices**. Transformation matrices of processed objects.

