Curve Frame
===========

.. image:: https://user-images.githubusercontent.com/14288520/210581705-55a64f81-6a4d-40b3-81bd-03179b7cbd16.png
  :target: https://user-images.githubusercontent.com/14288520/210581705-55a64f81-6a4d-40b3-81bd-03179b7cbd16.png

Functionality
-------------

This node calculates a reference frame of a curve (also known as Frenet_ frame)
for the given value of curve's T parameter. Basically, the node allows one to
place some object at the curve, by aligning the object with curve's "natural"
orientation.

.. image:: https://user-images.githubusercontent.com/14288520/210584549-8a57a141-95a3-4ae2-8afb-be674cb7b1c0.png
  :target: https://user-images.githubusercontent.com/14288520/210584549-8a57a141-95a3-4ae2-8afb-be674cb7b1c0.png

.. _Frenet: https://en.wikipedia.org/wiki/Frenet%E2%80%93Serret_formulas

**Note 1**: Frenet frame of the curve rotates around curve's tangent according to
curve's own torsion. Thus, if you place something by this frame, the result can
be somewhat twisted. If you want to minimize the twist, you may wish to use
**Zero-Twist Frame** node.

.. image:: https://user-images.githubusercontent.com/14288520/210585812-b8893694-5d38-43b2-9921-cc03e29714d3.png
  :target: https://user-images.githubusercontent.com/14288520/210585812-b8893694-5d38-43b2-9921-cc03e29714d3.png

**Note 2**: it is not possible to correctly calculate Frenet frame of the curve
at points where it has zero curvature (or at straight segments of the curve).
The node will give an error or produce invalid output in such cases.

.. image:: https://user-images.githubusercontent.com/14288520/210587935-40dd1b37-ba5c-412c-b88c-277aeb5f782f.png
  :target: https://user-images.githubusercontent.com/14288520/210587935-40dd1b37-ba5c-412c-b88c-277aeb5f782f.png

Inputs
------

This node has the following inputs:

* **Curve**. The curve to calculate frame for. This input is mandatory.
* **T**. The value of curve's T parameter. The default value is 0.5.

.. image:: https://user-images.githubusercontent.com/14288520/210601868-cb2097f6-8736-435e-9284-9efd4a4afca0.png
  :target: https://user-images.githubusercontent.com/14288520/210601868-cb2097f6-8736-435e-9284-9efd4a4afca0.png

Parameters
----------

This node has the following parameters:

* **Join**. If checked, the node will output the single list of matrices,
  joined from any number of input curves provided. Otherwise, the node will
  output a separate list of matrices for each input curve. Checked by default.

.. image:: https://user-images.githubusercontent.com/14288520/210603851-9f5659d6-5904-4dcc-a0c5-3cba1303eeff.png
  :target: https://user-images.githubusercontent.com/14288520/210603851-9f5659d6-5904-4dcc-a0c5-3cba1303eeff.png

* **On zero curvature**. This parameter is only available in the N panel. This
  defines what the node should do if it is instructed to calculate curve frame
  at the point where curve has zero curvature. The available options are:

   * **Raise error**. The node will raise an error (become red) and will not
     process such input.
   * **Arbitrary frame**. The node will return some arbitrary frame, with only
     guaranteed property of having Z axis parallel to curve's tangent (two
     other axes will be chosen arbitrarily).

  The default option is **Raise error**.

.. image:: https://user-images.githubusercontent.com/14288520/210600874-0b03994e-c1fb-4203-9de8-9ce8c8fda0a4.png
  :target: https://user-images.githubusercontent.com/14288520/210600874-0b03994e-c1fb-4203-9de8-9ce8c8fda0a4.png


Outputs
-------

This node has the following outputs:

* **Matrix**. The matrix defining the Frenet frame for the curve at the
  specified value of T parameter. The location component of the matrix is the
  point of the curve. Z axis of the matrix points along curve's tangent.
* **Normal**. The direction of curve's main normal at the specified value of T parameter.
* **Binormal**. The direction of curve's binormal at the specified value of T parameter.

.. image:: https://user-images.githubusercontent.com/14288520/210584549-8a57a141-95a3-4ae2-8afb-be674cb7b1c0.png
  :target: https://user-images.githubusercontent.com/14288520/210584549-8a57a141-95a3-4ae2-8afb-be674cb7b1c0.png

Examples of usage
-----------------

Visualize curve's frame at some points:

.. image:: https://user-images.githubusercontent.com/14288520/210607852-abd7b756-69cb-4a29-a2fa-684df1020529.png
  :target: https://user-images.githubusercontent.com/14288520/210607852-abd7b756-69cb-4a29-a2fa-684df1020529.png

* Generator-> :doc:`Random Vector </nodes/generator/random_vector_mk3>`
* Curves-> :doc:`Cubic Spline </nodes/curve/cubic_spline>`
* Curves-> :doc:`Cubic Domain </nodes/curve/curve_range>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Use these frames to put cubes along the curve, aligning them along curve's natural orientation:

.. image:: https://user-images.githubusercontent.com/14288520/210609386-6a21cb63-bcce-4ad1-a8d0-893ac7b11861.png
  :target: https://user-images.githubusercontent.com/14288520/210609386-6a21cb63-bcce-4ad1-a8d0-893ac7b11861.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Generator-> :doc:`Random Vector </nodes/generator/random_vector_mk3>`
* Curves-> :doc:`Cubic Spline </nodes/curve/cubic_spline>`
* Curves-> :doc:`Cubic Domain </nodes/curve/curve_range>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`