Kinked Curve
============

.. image:: https://user-images.githubusercontent.com/14288520/205459954-6d595c27-0b4d-4bd8-813f-4544d1b081ec.png
  :target: https://user-images.githubusercontent.com/14288520/205459954-6d595c27-0b4d-4bd8-813f-4544d1b081ec.png

Functionality
-------------

This node generates a "kinky" curve, i.e. a curve that is smooth in some places
and sharp in others. The node allows the ability to control a specific angle
threshold where the curve will transition from a kinked line to a smooth
interpolated curve.

.. image:: https://user-images.githubusercontent.com/14288520/205460382-798cddf0-3fa8-42bd-8c38-ad66b5608a17.png
  :target: https://user-images.githubusercontent.com/14288520/205460382-798cddf0-3fa8-42bd-8c38-ad66b5608a17.png

This node calculates angles between consequent segments of a polyline built
from original points; if the angle at a point is less than specified threshold,
the curve will have sharp angle at this point; otherwise, the curve will be
smooth.

The node generates a separate Curve object for each smooth segment of a curve;
these segments can be optionally concatenated into one Curve object.

Inputs
------

This node has the following inputs:

* **Vertices**. The vertices to interpolate between. This input is mandatory.
* **AngleThreshold**. Threshold of the angle between points, which defines at
  which points the curve will have sharp corners. The value is expected in
  radians. The default value is ``pi/6``.

.. image:: https://user-images.githubusercontent.com/14288520/205460666-76feff7d-5cea-4a3b-8b92-556c788f90e7.png
  :target: https://user-images.githubusercontent.com/14288520/205460666-76feff7d-5cea-4a3b-8b92-556c788f90e7.png

Parameters
----------

This node has the following parameters:

* **Concatenate**. If checked, the node will output single Curve object for
  each set of points. Otherwise, it will generate a separate Curve object for
  each smooth segment of the curve. Checked by default.

.. image:: https://user-images.githubusercontent.com/14288520/205460811-0814b605-ffc1-4b12-a12b-6d862cff012e.png
  :target: https://user-images.githubusercontent.com/14288520/205460811-0814b605-ffc1-4b12-a12b-6d862cff012e.png

* **Cyclic**. If checked, the node will generate a cyclic (closed) curve.
  Unchecked by default.

.. image:: https://user-images.githubusercontent.com/14288520/205460979-21eac21e-cfb0-49c3-93f7-1f42d7af2040.gif
  :target: https://user-images.githubusercontent.com/14288520/205460979-21eac21e-cfb0-49c3-93f7-1f42d7af2040.gif

* **NURBS output**. This parameter is available in the N panel only. If
  checked, the node will output a NURBS curve. Built-in NURBS maths
  implementation will be used. If not checked, the node will output generic
  concatenated curve from several straight segments and circular arcs. In most
  cases, there will be no difference; you may wish to output NURBS if you want
  to use NURBS-specific API methods with generated curve, or if you want to
  output the result in file format that understands NURBS only. Unchecked by
  default.

.. image:: https://user-images.githubusercontent.com/14288520/205461077-fbf75b36-5d5e-4c69-add8-4df6d274907e.png
  :target: https://user-images.githubusercontent.com/14288520/205461077-fbf75b36-5d5e-4c69-add8-4df6d274907e.png

* **Metric**. This parameter is available in the N panel only. This defines the
  metric used to calculate curve's T parameter values corresponding to
  specified curve points. The available values are:

   * Manhattan
   * Euclidean
   * Points (just number of points from the beginning)
   * Chebyshev.

   The default value is Euclidean.

.. image:: https://user-images.githubusercontent.com/14288520/205461520-05d351b9-6dc2-41d7-803b-b5f5bffb8e64.gif
  :target: https://user-images.githubusercontent.com/14288520/205461520-05d351b9-6dc2-41d7-803b-b5f5bffb8e64.gif

Outputs
-------

This node has the following output:

* **Curve**. Generated curve object(s).

Examples of usage
-----------------

A simple example:

.. image:: https://user-images.githubusercontent.com/14288520/205461748-b2bdfd6e-2d96-4b17-a60f-22c6f650a279.png
  :target: https://user-images.githubusercontent.com/14288520/205461748-b2bdfd6e-2d96-4b17-a60f-22c6f650a279.png

* Number-> :doc:`A Number </nodes/number/numbers>`
* RADIAND: Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* Vector-> :doc:`Vector sort </nodes/vector/vertices_sort>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`
* Viz-> :doc:`Viewer Index+ </nodes/viz/viewer_idx28>`
* Scene-> :doc:`Get Objects Data </nodes/scene/get_objects_data>`

---------

Similar example with a closed curve:

.. image:: https://user-images.githubusercontent.com/14288520/205461887-70252d9b-4858-42ab-a510-921b1c71ea5d.png
  :target: https://user-images.githubusercontent.com/14288520/205461887-70252d9b-4858-42ab-a510-921b1c71ea5d.png