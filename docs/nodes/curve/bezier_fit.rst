Approximate Bezier Curve
========================

Dependencies
------------

This node requires SciPy_ library to work.

.. _SciPy: https://scipy.org/

Functionality
-------------

This node builds a Bezier_ Curve object, which approximate the given set of
points, i.e. goes as close to them as possible while remaining a smooth curve.

.. _Bezier: https://en.wikipedia.org/wiki/B%C3%A9zier_curve

Inputs
------

This node has the following inputs:

* **Vertices**. The points to be approximated. This input is mandatory.
* **Degree**. Degree of the curve to be build. The default value is 3.

Parameters
----------

This node has the following parameter:

* **Metric**. This parameter is available in the N panel only. It defines the
  metric to be used for calculation of curve's T parameter which correspond to
  specified vertices. The default value is **Euclidian**. Usually you do not
  have to adjust this parameter.

Outputs
-------

This node has the following outputs:

* **Curve**. The generated Bezier Curve object.
* **ControlPoints**. Control points of the generated curve.

Example of usage
----------------

Take points fro Greasepencil drawing and approximate them with a smooth curve:

.. image:: https://user-images.githubusercontent.com/284644/86514558-7fc9ee00-be2c-11ea-8399-811e14ba38b7.png

