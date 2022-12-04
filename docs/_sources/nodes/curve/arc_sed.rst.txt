Arc Start / End / Tangent
=========================

.. image:: https://user-images.githubusercontent.com/14288520/205436389-16711634-8691-48a2-8b50-9e6f8ab22823.png
  :target: https://user-images.githubusercontent.com/14288520/205436389-16711634-8691-48a2-8b50-9e6f8ab22823.png

Functionality
-------------

This node generates a Curve object, which represents a circular arc, given it's
starting point, end point and a tangent vector at the starting point.  The node
also outputs key properties of such an arc: center, radius and angle.

.. image:: https://user-images.githubusercontent.com/14288520/205436737-a301707e-430f-42e6-a643-f2ff56dcf798.png
  :target: https://user-images.githubusercontent.com/14288520/205436737-a301707e-430f-42e6-a643-f2ff56dcf798.png

See also:

* Curves-> :doc:`Circle (Curve) </nodes/curve/curve_circle>`
* Curves-> :doc:`Arc 3pt (Curve) </nodes/curve/arc_3pt>`

Inputs
------

This node has the following inputs:

* **Start**. Starting point of the arc. The default value is ``(0, 0, 0)``.
* **End**. End point of the arc. The default value is ``(1, 0, 0)``.
* **Tangent**. Tangent vector of the arc at the starting point. The default
  value is ``(0, 1, 0)``. Note that the length of this vector does not matter,
  only direction is used.

.. image:: https://user-images.githubusercontent.com/14288520/205437107-47552cb9-e31e-44a2-8163-818b21e65854.png
  :target: https://user-images.githubusercontent.com/14288520/205437107-47552cb9-e31e-44a2-8163-818b21e65854.png

.. image:: https://user-images.githubusercontent.com/14288520/205437034-4e95b36a-4e87-4d35-9372-7d19a5eff982.png
  :target: https://user-images.githubusercontent.com/14288520/205437034-4e95b36a-4e87-4d35-9372-7d19a5eff982.png

Parameters
----------

This node has the following parameter:

* **Join**. If checked, then the node will output single flat list of curves
  for all provided sets of points. Otherwise, there will be separate list of
  Curve objects generated for each list of input points. Checked by default.

.. image:: https://user-images.githubusercontent.com/14288520/205437582-79a62988-b767-4a53-950a-49619273d946.png
  :target: https://user-images.githubusercontent.com/14288520/205437582-79a62988-b767-4a53-950a-49619273d946.png

Outputs
-------

This node has the following outputs:

* **Arc**. The arc curve object.

.. image:: https://user-images.githubusercontent.com/14288520/205437853-49badc6f-1a07-45d5-8625-050dfb84e403.png 
  :target: https://user-images.githubusercontent.com/14288520/205437853-49badc6f-1a07-45d5-8625-050dfb84e403.png

* **Circle**. A circle curve - the same as in the Arc output, but this curve
  goes the whole 360 degrees.

.. image:: https://user-images.githubusercontent.com/14288520/205437944-e4e5cef6-9cc6-4196-93be-4ee584e5a2ba.png
  :target: https://user-images.githubusercontent.com/14288520/205437944-e4e5cef6-9cc6-4196-93be-4ee584e5a2ba.png

* **Center**. The matrix which defines the location of arc's center, and the
  orientation of the arc. The Z axis of this matrix always looks along the
  normal of the arc plane. The X axis of this matrix always looks towards the
  first point of arc (one which is provided in the **Start** input).

.. image:: https://user-images.githubusercontent.com/14288520/205438028-ee547178-7467-4b88-a3cc-697367d62ab1.png
  :target: https://user-images.githubusercontent.com/14288520/205438028-ee547178-7467-4b88-a3cc-697367d62ab1.png

.. image:: https://user-images.githubusercontent.com/14288520/205438257-0582cc33-1d3d-45ae-a2be-7da308a258ab.gif
  :target: https://user-images.githubusercontent.com/14288520/205438257-0582cc33-1d3d-45ae-a2be-7da308a258ab.gif

* **Radius**. The radius of the arc.
* **Angle**. The angle of the arc, in radians.

.. image:: https://user-images.githubusercontent.com/14288520/205438352-940ee01d-3d9c-411e-b148-579903626fef.png
  :target: https://user-images.githubusercontent.com/14288520/205438352-940ee01d-3d9c-411e-b148-579903626fef.png

Examples of usage
-----------------

**Default settings**:

.. image:: https://user-images.githubusercontent.com/14288520/205438495-04c09262-1fc2-467b-bbc5-0537ba4e3ed4.png
  :target: https://user-images.githubusercontent.com/14288520/205438495-04c09262-1fc2-467b-bbc5-0537ba4e3ed4.png

* Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`

---------

**Vectorization example**:

.. image:: https://user-images.githubusercontent.com/14288520/205438850-c00274cc-deb1-4313-989e-95d672f2987c.png
  :target: https://user-images.githubusercontent.com/14288520/205438850-c00274cc-deb1-4313-989e-95d672f2987c.png

.. image:: https://user-images.githubusercontent.com/14288520/205438954-eac6ec86-b350-4400-9676-2e95fa5d25e6.gif
  :target: https://user-images.githubusercontent.com/14288520/205438954-eac6ec86-b350-4400-9676-2e95fa5d25e6.gif

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Vector-> :doc:`Vector Polar Input </nodes/vector/vector_polar_in>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`