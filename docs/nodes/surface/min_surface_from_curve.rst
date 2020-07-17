Minimal Surface from Curve
==========================

Dependencies
------------

This node requires SciPy_ library to work.

.. _SciPy: https://scipy.org/

Functionality
-------------

This node generates a Surface, based on the provided Curve, by use of RBF_
method. To do so, the node evaluates the curve in many points, and then
generates an RBF surface for these points.  Depending on node parameters, the
curve can be either interpolating (go through all points) or only approximating.

The generated surface is not, strictly speaking, guaranteed to be minimal_; but
in many simple cases it is close enough to the minimal.

.. _RBF: http://www.scholarpedia.org/article/Radial_basis_function
.. _minimal: https://en.wikipedia.org/wiki/Minimal_surface

Inputs
------

This node has the following inputs:

* **Curve**. The curve to generate surface from. This input is mandatory.
* **Samples**. Number of samples to evaluate the curve in. Theoretically,
  greater number of samples will give the surface which follows the curve more
  precisely. However, for some RBF functions too high values generate weird
  results. The default value is 50.
* **Epsilon**. Epsilon parameter of used RBF function; it affects the shape of
  generated surface. The default value is 1.0.
* **Smooth**. Smoothness parameter of used RBF function. If this is zero, then
  the surface will go through all provided points; otherwise, it will be only an
  approximating surface. The default value is 0.0.

Parameters
----------

This node has the following parameter:

* **Function**. The specific function used by the node. The available values are:

  * Multi Quadric
  * Inverse
  * Gaussian
  * Cubic
  * Quintic
  * Thin Plate

  The default function is Multi Quadric.

Outputs
-------

This node has the following outputs:

* **Surface**. The generated surface object.
* **TrimCurve**. The curve in surface's U/V space, which corresponds to the
  provided input Curve. This output can be used with "Trim & Tessellate" or
  "Adaptive tessellate" nodes to trim the surface.
* **Curve**. The curve from **TrimCurve** output mapped to the surface.

Example of usage
----------------

.. image:: https://user-images.githubusercontent.com/284644/87231392-54b54080-c3d0-11ea-8374-a7e1c0528e5b.png

