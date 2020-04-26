Arc 3pt (Curve)
===============

Functionality
-------------

This node generates a Curve object, which represent a circular arc, going
through the three specified points. The node also outputs key properties of
such an arc: center, radius and angle.

See also the Circle node.

Inputs
------

This node has the following inputs:

* **Point1**. The first point to draw an arc through. The default value is `(0, 0, 0)`.
* **Point2**. The second point to draw an arc through. The default value is `(1, 0, 0)`.
* **Point3**. The third point to draw an arc through. The default value is `(0, 1, 0)`.

Parameters
----------

This node has the following parameter:

* **Join**. If checked, the node will output a flat (level 1) list of Curve
  objects, even if the inputs contain a list of lists of points (level 3 list).
  Otherwise, the node will output list of lists of Curves in such situation.
  Checked by default.

Outputs
-------

This node has the following outputs:

* **Arc**. The arc curve object.
* **Circle**. A circle curve - the same as in the Arc output, but this curve goes the whole 360 degrees.
* **Center**. The matrix which defines the location of arc's center, and the
  orientation of the arc. The Z axis of this matrix always looks along the
  normal of the arc plane. The X axis of this matrix always looks towards the
  first point of arc (one which is provided in the **Point1** input).
* **Radius**. The radius of the arc.
* **Angle**. The angle of the arc, in radians.

Example of usage
----------------

Build an arc via three points, and visualize it's center matrix:

.. image:: https://user-images.githubusercontent.com/284644/80307642-c8897900-87e3-11ea-831f-ab4b5ef68c3f.png

