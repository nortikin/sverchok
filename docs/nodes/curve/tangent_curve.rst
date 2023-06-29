Tangents Curve
==============

.. image:: https://user-images.githubusercontent.com/14288520/205859161-43d923da-2419-44c1-91f1-e8306c5fa0d6.png
  :target: https://user-images.githubusercontent.com/14288520/205859161-43d923da-2419-44c1-91f1-e8306c5fa0d6.png

Functionality
-------------

This node generates a Curve object, defined by series of points, through which
the curve must pass, and tangent vectors of the curve at those points.

.. image:: https://user-images.githubusercontent.com/14288520/205862183-f8eb5c09-2ba5-4315-8a68-1dab9c102fca.png
  :target: https://user-images.githubusercontent.com/14288520/205862183-f8eb5c09-2ba5-4315-8a68-1dab9c102fca.png

The node can use one of two algorithms:

* Hermite_ spline. The curve is generated as a series of cubic Bezier curves.
  Control points of Bezier curves are defined as follows:

   * For each segment defined by a pair of input points, one Bezier curve is
     generated - for example, one curve for first and second point, one curve for
     second and third point, and so on.
   * For each segment, the first point is the starting point of Bezier curve, and
     the second point is the end point of Bezier curve.
   * Provided tangent vectors are placed so that the middle point of each vector
     is at corresponding input point - middle of the first tangent vector at the
     first input point, and so on. Then end points of these vectors will define
     additional control points for Bezier curves.

   Generated curves may be optionally concatenated into one Curve object.

* NURBS curve. The node creates interpolating NURBS curve (of 3rd degree)
  through the specified points, with additional condition that it should have
  specified tangents at those points.

.. _Hermite: https://en.wikipedia.org/wiki/Cubic_Hermite_spline

Inputs
------

This node has the following inputs:

* **Points**. List of points, through which the generated curve should pass.
  This input is mandatory, and must contain at least two points.
* **Tangents**. List of vectors, which are tangent vectors at corresponding
  points in the **Points** input. This input is mandatory.

Parameters
----------

This node has the following parameters:

* **Curve type**. This defines the algorithm to be used by the node, and the
  type of resulting curve. The available options are:

   * **Hermite**. Use Hermite_ spline algorithm, and generate either a list of
     Bezier curves, or concatenated NURBS curve.
   * **NURBS**. Use NURBS interpolation algorithm.

* **Cyclic**. If checked, then the node will generate additional Bezier curve
  segment to connect the last point with the first one. Unchecked by default.

.. image:: https://user-images.githubusercontent.com/14288520/205867628-5f3de9ae-ab0a-435b-9ebb-3dc409ff4e51.png
  :target: https://user-images.githubusercontent.com/14288520/205867628-5f3de9ae-ab0a-435b-9ebb-3dc409ff4e51.png

* **Concatenate**. This parameter is available only when **Curve type**
  parameter is set to **Hermite**. If checked, then the node will concatenate
  all generated Bezier curve segments into one Curve object. Otherwise, it will
  output each segment as a separate Curve object. Checked by default.

.. image:: https://user-images.githubusercontent.com/14288520/205943520-e9ec6cd6-54de-483f-8af9-753d4720d27e.png
  :target: https://user-images.githubusercontent.com/14288520/205943520-e9ec6cd6-54de-483f-8af9-753d4720d27e.png

Outputs
-------

This node has the following outputs:

* **Curve**. Generated curve (or list of curves).
* **ControlPoints**. Control points of all generated Bezier curves. This output
  contains a separate list of points for each generated curve segment.

.. image:: https://user-images.githubusercontent.com/14288520/205928727-2fbc4a59-9f2c-40c1-99a5-d9ce70dbff17.png
  :target: https://user-images.githubusercontent.com/14288520/205928727-2fbc4a59-9f2c-40c1-99a5-d9ce70dbff17.png

Examples of usage
-----------------

Simple example, with points and curves defined manually:

.. image:: https://user-images.githubusercontent.com/14288520/205932603-2cc1ab0f-0a42-4338-a0d8-bc9582cabe74.png
  :target: https://user-images.githubusercontent.com/14288520/205932603-2cc1ab0f-0a42-4338-a0d8-bc9582cabe74.png

* Generator-> :doc:`Segment </nodes/generator/segment>`
* Number-> :doc:`List Input </nodes/number/list_input>`
* List->List Main-> :doc:`List Delete Levels </nodes/list_main/delete_levels>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`

---------

More complex example: draw a smooth curve so that it would touch three circles in specific points:

.. image:: https://user-images.githubusercontent.com/14288520/205940676-fa6c2a08-a673-418e-836e-19139ffb9db6.png
  :target: https://user-images.githubusercontent.com/14288520/205940676-fa6c2a08-a673-418e-836e-19139ffb9db6.png

* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Curves-> :doc:`Circle (Curve) </nodes/curve/curve_circle>`
* Curves-> :doc:`Evaluate Curve </nodes/curve/eval_curve>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* ADD X: Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* A * SCALAR: Vector-> :doc:`Vector Math </nodes/vector/math_mk3>`
* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`
* List->List Struct-> :doc:`List Slice </nodes/list_struct/slice>`
* List->List Struct-> :doc:`List Split </nodes/list_struct/split>`
* Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Example of NURBS mode usage:

.. image:: https://user-images.githubusercontent.com/284644/209460542-535e4c0a-9c0f-44e4-a127-46fa104cd335.png
  :target: https://user-images.githubusercontent.com/284644/209460542-535e4c0a-9c0f-44e4-a127-46fa104cd335.png

