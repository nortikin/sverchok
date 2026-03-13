Rounded Rectangle
=================

.. image:: https://user-images.githubusercontent.com/14288520/205291207-1647c626-2621-4a1c-90ca-531dcfd8a623.png
  :target: https://user-images.githubusercontent.com/14288520/205291207-1647c626-2621-4a1c-90ca-531dcfd8a623.png

Functionality
-------------

This node generates a Curve object, which represents a rectangle with rounded corners.

.. image:: https://user-images.githubusercontent.com/14288520/205377156-d917f751-58b7-435f-90c9-7ff3df7acc6d.png
  :target: https://user-images.githubusercontent.com/14288520/205377156-d917f751-58b7-435f-90c9-7ff3df7acc6d.png

Inputs
------

This node has the following inputs:

* **Size X**. Size of the rectangle along the X axis (rectangle width). The default value is 10.
* **Size Y**. Size of the rectangle along the Y axis (rectangle height). The default value is 10.

.. image:: https://user-images.githubusercontent.com/14288520/205292970-0dfff7e9-0676-4514-88e1-f210df5348df.png
  :target: https://user-images.githubusercontent.com/14288520/205292970-0dfff7e9-0676-4514-88e1-f210df5348df.png

* **Radius**. Corner rounding radius. This input can consume lists of nesting
  level 2 or 3. If the input data have nesting level 3, then it is supposed
  that the input defines separate radius for each of 4 corners of each
  rectangle. If the radius is zero, then there will be no rounding arc
  generated at the corresponding corner of the rectangle. The default value is
  1.0.

.. image:: https://user-images.githubusercontent.com/14288520/205384976-69e9522c-f7d2-4a3a-b5b2-b7e3d5fc5502.png
  :target: https://user-images.githubusercontent.com/14288520/205384976-69e9522c-f7d2-4a3a-b5b2-b7e3d5fc5502.png

Parameters
----------

This node has the following parameters:

* **Center**. If checked, then the generated curve will be centered around
  world's origin; in other words, the center of the rectangle will be at ``(0,
  0, 0)``. If not checked, the left-down corner of the rectangle will be at the
  origin. Unchecked by default.

.. image:: https://user-images.githubusercontent.com/14288520/205377638-fdaea955-8187-4b8e-b820-e8ee00a5ae2b.png
  :target: https://user-images.githubusercontent.com/14288520/205377638-fdaea955-8187-4b8e-b820-e8ee00a5ae2b.png

* **Even domains**. If checked, give each segment a domain of length 1.
  Otherwise, each arc will have a domain of length ``pi/2``, and each straight
  line segment will have a domain of length equal to the segment's length.
  Unchecked by default.

.. image:: https://user-images.githubusercontent.com/14288520/205484897-1f56658d-72aa-4309-a4b5-7abc296f33e3.png
  :target: https://user-images.githubusercontent.com/14288520/205484897-1f56658d-72aa-4309-a4b5-7abc296f33e3.png

* **NURBS output**. This parameter is available in the N panel only. If
  checked, the node will output a NURBS curve. Built-in NURBS maths
  implementation will be used. If not checked, the node will output generic
  concatenated curve from several straight segments and circular arcs. In most
  cases, there will be no difference; you may wish to output NURBS if you want
  to use NURBS-specific API methods with generated curve, or if you want to
  output the result in file format that understands NURBS only. Unchecked by
  default.

.. image:: https://user-images.githubusercontent.com/14288520/205383334-f6104443-98ef-4b20-93c3-97b56882123b.png
  :target: https://user-images.githubusercontent.com/14288520/205383334-f6104443-98ef-4b20-93c3-97b56882123b.png

Outputs
-------

This node has the following outputs:

* **Curve**. The generated Curve object. The curve always lies in the XOY plane.
* **Centers**. Center points of generated arc segments.

.. image:: https://user-images.githubusercontent.com/14288520/205383758-9bef0d84-e50e-489d-828e-e8bbac59edad.png
  :target: https://user-images.githubusercontent.com/14288520/205383758-9bef0d84-e50e-489d-828e-e8bbac59edad.png

* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

Examples of usage
-----------------

**Simple example**:

.. image:: https://user-images.githubusercontent.com/14288520/205385695-b8760181-45fe-4388-a576-4997a1a580d7.png
  :target: https://user-images.githubusercontent.com/14288520/205385695-b8760181-45fe-4388-a576-4997a1a580d7.png

* Curves-> :doc:`Evaluate Curve </nodes/curve/eval_curve>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Matrix Multiply: Matrix-> :doc:`Matrix Math </nodes/matrix/matrix_math>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Viewer Index+ </nodes/viz/viewer_idx28>`

---------

**Vectorization example 1 - sizes only**:

.. image:: https://user-images.githubusercontent.com/14288520/205386294-aaef0166-7301-4838-b223-ed733d884ca3.png
  :target: https://user-images.githubusercontent.com/14288520/205386294-aaef0166-7301-4838-b223-ed733d884ca3.png

* Curves-> :doc:`Evaluate Curve </nodes/curve/eval_curve>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

**Vectorization example 2 - sizes and radiuses per rectangle**:

.. image:: https://user-images.githubusercontent.com/14288520/205387054-5d6b70d0-df27-4b03-959d-1e125bbd2eeb.png
  :target: https://user-images.githubusercontent.com/14288520/205387054-5d6b70d0-df27-4b03-959d-1e125bbd2eeb.png

* Curves-> :doc:`Evaluate Curve </nodes/curve/eval_curve>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Number-> :doc:`List Input </nodes/number/list_input>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

**Vectorization example 3 - sizes and radiuses per rectangle corner**:

.. image:: https://user-images.githubusercontent.com/14288520/205397056-e21a2b41-221f-4f4d-8ded-8e8192c951c8.png
  :target: https://user-images.githubusercontent.com/14288520/205397056-e21a2b41-221f-4f4d-8ded-8e8192c951c8.png

* Curves-> :doc:`Evaluate Curve </nodes/curve/eval_curve>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Number-> :doc:`List Input </nodes/number/list_input>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* List->List Struct-> :doc:`List Repeater </nodes/list_struct/repeater>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`