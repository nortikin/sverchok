Arc Start / End / Tangent
=========================

Functionality
-------------

This node generates a Curve object, which represents a circular arc, given it's
starting point, end point and a tangent vector at the starting point.  The node
also outputs key properties of such an arc: center, radius and angle.

See also: Circle node; "Arc 3pt (Curve)" node.

Inputs
------

This node has the following inputs:

* **Start**. Starting point of the arc. The default value is ``(0, 0, 0)``.
* **End**. End point of the arc. The default value is ``(1, 0, 0)``.
* **Tangent**. Tangent vector of the arc at the starting point. The default
  value is ``(0, 1, 0)``. Note that the length of this vector does not matter,
  only direction is used.

Parameters
----------

This node has the following parameter:

* **Join**. If checked, then the node will output single flat list of curves
  for all provided sets of points. Otherwise, there will be separate list of
  Curve objects generated for each list of input points. Checked by default.

Outputs
-------

This node has the following outputs:

* **Arc**. The arc curve object.
* **Circle**. A circle curve - the same as in the Arc output, but this curve
  goes the whole 360 degrees.
* **Center**. The matrix which defines the location of arc's center, and the
  orientation of the arc. The Z axis of this matrix always looks along the
  normal of the arc plane. The X axis of this matrix always looks towards the
  first point of arc (one which is provided in the **Start** input).
* **Radius**. The radius of the arc.
* **Angle**. The angle of the arc, in radians.

Examples of usage
-----------------

Default settings:

.. image:: https://user-images.githubusercontent.com/284644/82756581-79d7fa80-9df4-11ea-9819-25616fd23aca.png

Vectorization example:

.. image:: https://user-images.githubusercontent.com/284644/82756583-7ba1be00-9df4-11ea-9048-3be46c6b85fe.png

