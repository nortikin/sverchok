Intersect Curve with Surface
============================

Dependencies
------------

This node requires SciPy_ library to work.

.. _SciPy: https://scipy.org/

Functionality
-------------

This node searches for the intersections of a Curve with a Surface.

This node uses a numerical method to find the intersections, so it can be not
very fast. If you happen to know how to find intersections of your specific
surface and curve by formulas, that will be much faster and more precise.

To find all intersections, the node splits the curve into several segments and
then searches for sinle intersection in each segment.

For the initial guess, at the first step the node generates a rough
approximation of the surface with a mesh by evaluating the surface in points of
carthesian grid.

Inputs
------

This node has the following inputs:

* **Curve***. The curve to search intersections with. This input is mandatory.
* **Surface**. The surface to search intersections with. This input is mandatory.

Parameters
----------

Thisnode has the following parameters:

* **Init Surface Samples**. Number of samples of the surface for initial
  approximation. More samples will give a better initial guess, so less work
  for more precise numerical algorithm, but the longer initial step. In many
  simple cases you do not have to change this parameter. The default value is
  10.
* **Init Curve Samples**. Number of samples of the curve for initial
  approximation. The number of intersection points of each curve that this node
  is able to find can not be greater than the value of this parameter. In some
  complex cases, you will have to set this parameter to a value a lot greater
  than the number of expected intersections. But in most simple cases, you do
  not have to change this parameter. The default value is 10.
* **Method**. This parameter is available in the N panel only. Type of numeric
  method to be used. The available options are:

   * **Hybrd & Hybrj**. Use MINPACK’s hybrd and hybrj routines (modified Powell method).
   * **Levenberg-Marquardt**. Levenberg-Marquardt algorithm.
   * **Krylov**. Krylov algorithm.
   * **Broyden 1**. Broyden1 algorithm.
   * **Broyden 2**. Broyden2 algorithm.
   * **Anderson**. Anderson algorithm.
   * **DF-SANE**. DF-SANE method.

   The default option is **Hybrd & Hybrj**. In simple cases, you do not
   have to change this parameter. In more complex cases, you will have to try
   all of them and decide which one fits you better.

* **Accuracy**. This parameter is available in the N panel only. Numerical
  precision - the number of exact digits after decimal point. The default value
  is 4.

Outputs
-------

This node has the following outputs:

* **Point**. The found intersection point in 3D space.
* **T**. Curve's T parameter value corresponding to the found point.

Example of usage
----------------

.. image:: https://user-images.githubusercontent.com/284644/87244933-8c68ca80-c45a-11ea-955e-e41800b9ca50.png

