Catenary Curve
==============

.. image:: https://user-images.githubusercontent.com/14288520/205445101-09994c2b-6646-475d-999c-571bbe871c9e.png
  :target: https://user-images.githubusercontent.com/14288520/205445101-09994c2b-6646-475d-999c-571bbe871c9e.png

Dependencies
------------

This node requires SciPy_ library to work.

.. _SciPy: https://scipy.org/

Functionality
-------------

This node generates a catenary_ curve, given it's two end points and it's length.

.. _catenary: https://en.wikipedia.org/wiki/Catenary

.. image:: https://user-images.githubusercontent.com/14288520/205445321-ad399ddf-044b-4adb-9f42-1aa49cca05f7.png
  :target: https://user-images.githubusercontent.com/14288520/205445321-ad399ddf-044b-4adb-9f42-1aa49cca05f7.png

.. image:: https://user-images.githubusercontent.com/14288520/205445676-b73fffcb-dfea-4334-8390-e33edc272c62.gif
  :target: https://user-images.githubusercontent.com/14288520/205445676-b73fffcb-dfea-4334-8390-e33edc272c62.gif

Inputs
------

This node has the following inputs:

* **Point1**. Starting point of the curve. The default value is ``(-1, 0, 0)``.
* **Point2**. Ending point of the curve. The default value is ``(1, 0, 0)``.
* **Gravity**. Gravity force vector, i.e. the direction where curve's arc will
  be hanging to. Only direction of this vector is used, it's length has no
  meaning. The default value is ``(0, 0, -1)``.
* **Length**. The length of the curve between starting and ending point. The
  default value is 3.0.

.. image:: https://user-images.githubusercontent.com/14288520/205446031-26fbf80a-6301-4d04-9304-238cf298834e.png
  :target: https://user-images.githubusercontent.com/14288520/205446031-26fbf80a-6301-4d04-9304-238cf298834e.png

Parameters
----------

This node has the following parameter:

* **Join**. If checked, then the node will output single flat list of curves
  for all input lists of points. Otherwise, the node will output a separate
  list of curves for each list of input points. Checked by default.

.. image:: https://user-images.githubusercontent.com/14288520/205446519-6960e757-2eeb-4790-9202-ec426687218c.png
  :target: https://user-images.githubusercontent.com/14288520/205446519-6960e757-2eeb-4790-9202-ec426687218c.png

Outputs
-------

This node has the following output:

* **Curve**. The generated catenary curve object.

Examples of usage
-----------------

**Catenary curve hanging down between two points**:

.. image:: https://user-images.githubusercontent.com/14288520/205448797-4c859a2e-880c-4f21-9874-0f2861c91d3d.png
  :target: https://user-images.githubusercontent.com/14288520/205448797-4c859a2e-880c-4f21-9874-0f2861c91d3d.png

* Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`

---------

**Catenary arch**:

.. image:: https://user-images.githubusercontent.com/14288520/205449286-a68ea04b-3d67-4364-9902-0c883ef04f2f.png
  :target: https://user-images.githubusercontent.com/14288520/205449286-a68ea04b-3d67-4364-9902-0c883ef04f2f.png

* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Curves->Curve Primitives-> :doc:`Polyline </nodes/curve/polyline>`
* Surfaces-> :doc:`Extrude Curve Along Curve </nodes/surface/extrude_curve>`
* Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`