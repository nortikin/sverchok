Catenary Curve
==============

Dependencies
------------

This node requires SciPy_ library to work.

.. _SciPy: https://scipy.org/

Functionality
-------------

This node generates a catenary_ curve, given it's two end points and it's length.

.. _catenary: https://en.wikipedia.org/wiki/Catenary

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

Parameters
----------

This node has the following parameter:

* **Join**. If checked, then the node will output single flat list of curves
  for all input lists of points. Otherwise, the node will output a separate
  list of curves for each list of input points. Checked by default.

Outputs
-------

This node has the following output:

* **Curve**. The generated catenary curve object.

Examples of usage
-----------------

Catenary curve hanging down between two points:

.. image:: https://user-images.githubusercontent.com/284644/86517687-4b622c00-be44-11ea-8265-32d7bba9f8ee.png

Catenary arch:

.. image:: https://user-images.githubusercontent.com/284644/86518000-04c20100-be47-11ea-993f-19808ee3d2a5.png

