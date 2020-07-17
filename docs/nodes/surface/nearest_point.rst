Nearest Point on Surface
========================

Dependencies
------------

This node requires SciPy_ library to work.

.. _SciPy: https://scipy.org/

Functionality
-------------

This node searches for the point on the surface, which is the nearest (the
closest) to the given point.

Note that the search is implemented with a numeric algorithm, so it may be not
very fast. In case you know how to solve this task analytically (with formula)
for your particular surface, that will be much faster. This node, on the other
hand, is usable in cases when you do not know formulas for your surface - for
example, it was received by some approximation.

At the first step of it's algorithm, this node evaluates the surface in points
of a carthesian grid, and selects the closest of them. This point is then used
as an initial guess for the more precise algorithm.

In case there are several points on the surface with equal distance to the
original point, the node will return one of them (it is not guaranteed which
one).

Inputs
------

This node has the following inputs:

* **Surface**. The surface to find the nearest point on. This input is mandatory.
* **Point**. The point to search the nearest for. The default value is ``(0, 0, 0)``.

Parameters
----------

This node has the following parameters:

* **Init Resolution**. Number of samples to evaluate the surface in, for the
  initial guess. The higher this value is, the more precise the initial guess
  will be, so the less work for the numeric algorithm. The default value is 10.
  In many simple cases you do not have to change this value.
* **Precise**. If checked, then a numeric algorithm will be used to find exact
  location of the nearest point. Otherwise, the node will return the initial
  guess. So if this parameter is not checked, the **Init Resolution** parameter
  will define the precision of the node. Checked by default.
* **Method**. This parameter is available in the N panel only. The algorithm
  used to find the nearest point. The available algorithms are:

   * L-BFGS-B
   * Conjugate Gradient
   * Truncated Newton
   * SLSQP -  Sequential Least SQuares Programming algorithm.

   The default option is L-BFGS-B. In simple cases, you do not have to change
   this parameter. In more complex cases, you will have to try all algorithms
   and select the one which fits you the best.

Outputs
-------

This node has the following outputs:

* **Point**. The nearest point on the surface, in 3D space.
* **UVPoint**. The point in surface's U/V space, which corresponds to the
  nearest point. Z coordinate of this output is always zero, X and Y correspond
  to U and V.

Example of usage
----------------

.. image:: https://user-images.githubusercontent.com/284644/87247996-782fc800-c470-11ea-8ccc-e15021b59591.png

