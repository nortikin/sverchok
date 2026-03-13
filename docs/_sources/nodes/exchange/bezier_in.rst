Bezier Input
============

.. image:: https://github.com/user-attachments/assets/233fafda-4aef-48f1-80b0-a1a48f77e4a4
  :target: https://github.com/user-attachments/assets/233fafda-4aef-48f1-80b0-a1a48f77e4a4

Functionality
-------------

This node allows to bring Bezier_ Curve objects from Blender's scene into Sverchok.

.. _Bezier: https://en.wikipedia.org/wiki/B%C3%A9zier_curve

Additional description see :doc:`Get Objects Data </nodes/scene/get_objects_data>`.

If objects has red color then they cannot be used as spline (Mesh, Nurbs, Empty, Lamp and other). If collection has red color then some objects cannot be used as bezier splines.

  .. image:: https://github.com/user-attachments/assets/faa5717b-178a-4b2a-9b83-bb074e430d63
    :target: https://github.com/user-attachments/assets/faa5717b-178a-4b2a-9b83-bb074e430d63

Unprocessed objects also shown in the node buttom with yellow color.

Inputs
------

Objects Socket. You can select object or link to Collection picker node to select a collection.

Operators
---------

This node has the following operator button:

* **GET Selected**. When pressed, the node will update the list of objects bringed into
  Sverchok with a list of currently selected objects. If there are objects
  along selected ones, which are not Bezier curves, the node will skip them.

Parameters
----------

This node has the following parameters:

* **Sort**. If checked, the node will sort selected objects by name. Checked by default.
* **Apply matrices**. If checked, the node will apply all transforms to
  Blender's objects before bringing the coordinates into Sverchok. Checked by
  default.
* **Concatenate segments**. If checked, join Bezier segments of the curve into
  a single Curve object; otherwise, output a separate Curve object for each
  segment.

In the lower part of the node, the list of currently imported objects is shown.

Outputs
-------

This node has the following outputs:

* **Curves**. Generated Curve objects.
* **ControlPoints**. Control points of Bezier curves. This output contains a list of 4 points for each segments of each Bezier curve.
* **Matrices**. Transformation matrices of selected objects.
* **Tilt**. Tilt values from Blender's curve object. This output contains one
  value for each Bezier's control point in Blender terms (or, in more strict
  terms, one value for each point where one Bezier segment ends and new one
  starts).
* **Radius**. Radius values from Blender's curve object. Similar to **Tilt** output.

