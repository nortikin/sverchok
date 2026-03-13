Arc 3pt (Curve)
===============

.. image:: https://user-images.githubusercontent.com/14288520/205433902-77f0b2c1-1ca5-477a-bfda-f11d60e63f2d.png
  :target: https://user-images.githubusercontent.com/14288520/205433902-77f0b2c1-1ca5-477a-bfda-f11d60e63f2d.png

Functionality
-------------

This node generates a Curve object, which represent a circular arc, going
through the three specified points. The node also outputs key properties of
such an arc: center, radius and angle.

.. image:: https://user-images.githubusercontent.com/14288520/205434811-116e5ae9-3f57-4856-8de0-28c83bb0a865.png
  :target: https://user-images.githubusercontent.com/14288520/205434811-116e5ae9-3f57-4856-8de0-28c83bb0a865.png

See also:

* Curves-> :doc:`Circle (Curve) </nodes/curve/curve_circle>`
* Curves->Curve Primitives-> :doc:`Arc Start / End / Tangent </nodes/curve/arc_sed>`

Inputs
------

This node has the following inputs:

* **Point1**. The first point to draw an arc through. The default value is `(0, 0, 0)`.
* **Point2**. The second point to draw an arc through. The default value is `(1, 0, 0)`.
* **Point3**. The third point to draw an arc through. The default value is `(0, 1, 0)`.

.. image:: https://user-images.githubusercontent.com/14288520/205435111-4fd5c2b5-f0ad-46f1-bdae-4a7ce1b68c40.png
  :target: https://user-images.githubusercontent.com/14288520/205435111-4fd5c2b5-f0ad-46f1-bdae-4a7ce1b68c40.png

Parameters
----------

This node has the following parameter:

* **Join**. If checked, the node will output a flat (level 1) list of Curve
  objects, even if the inputs contain a list of lists of points (level 3 list).
  Otherwise, the node will output list of lists of Curves in such situation.
  Checked by default.

.. image:: https://user-images.githubusercontent.com/14288520/205434733-0720f257-c682-46af-8f0e-dd27be44e4dd.png
  :target: https://user-images.githubusercontent.com/14288520/205434733-0720f257-c682-46af-8f0e-dd27be44e4dd.png

* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

Outputs
-------

This node has the following outputs:

* **Arc**. The arc curve object.
* **Circle**. A circle curve - the same as in the Arc output, but this curve goes the whole 360 degrees.
* **Center**. The matrix which defines the location of arc's center, and the
  orientation of the arc. The Z axis of this matrix always looks along the
  normal of the arc plane. The X axis of this matrix always looks towards the
  first point of arc (one which is provided in the **Point1** input).

.. image:: https://user-images.githubusercontent.com/14288520/205435030-96b1d990-37b7-4adf-a4ef-d118d728ac19.gif
  :target: https://user-images.githubusercontent.com/14288520/205435030-96b1d990-37b7-4adf-a4ef-d118d728ac19.gif

* **Radius**. The radius of the arc.
* **Angle**. The angle of the arc, in radians.

.. image:: https://user-images.githubusercontent.com/14288520/205434830-63ff1aa9-4627-4002-b4fc-ff61e328d28f.png
  :target: https://user-images.githubusercontent.com/14288520/205434830-63ff1aa9-4627-4002-b4fc-ff61e328d28f.png

* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

Example of usage
----------------

Build an arc via three points, and visualize it's center matrix:

.. image:: https://user-images.githubusercontent.com/14288520/205435826-18619600-a339-4f93-974f-461ed094f5d6.png
  :target: https://user-images.githubusercontent.com/14288520/205435826-18619600-a339-4f93-974f-461ed094f5d6.png

* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`