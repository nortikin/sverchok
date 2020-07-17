Surface Extremes
================

Dependencies
------------

This node requires SciPy_ library to work.

.. _SciPy: https://scipy.org/

Functionality
-------------

This node searches for point on the surface, where the specified scalar field
reaches it's minimal or maximum value. Most often this node is used with the
"Coordinate scalar field" node to find, for example, points on the surface with
minimal Z coordinate.

Note that this node searches for extremes by use of numerical methods, so it
may be not very fast. In cases when you can find the points in question
analytically (by writing down all formulas for your field and your surface), it
will be much faster to calculate points by formulas. This node, in turn, is
most useful when you do not know exact formulas for the surface and / or for the
scalar field - for example, if they were defined by approximation.

Inputs
------

This node has the following inputs:

* **Surface**. The surface to find extremes for. This input is mandatory.
* **Field**. The scalar field in question. This input is mandatory.
* **StartUV**. The point in surface's U/V space to be used as an initial point
  for extremes search. This input is optional. You may use this input in case
  there are many local maximums / minimums on the surface, so that the node can
  try to start search from different points to find different local minimums /
  maximums, and then, optionally, select the best of them.

Parameters
----------

This node has the following parameters:

* **Direction**. This defines what kind of extreme points it is required to
  find. The available values are **Min** and **Max**. The default option is
  **Max**.
* **Search Best**. If checked, the node will try to find global maximum or
  minimum. Otherwise, the node will return all points it managed to find.
* **Method**. This parameter is available in the N panel only. The algorithm
  used to find the exterme point. The available values are:

   * L-BFGS-B
   * Conjugate Gradient
   * Truncated Newton
   * SLSQP -  Sequential Least SQuares Programming algorithm.

   The default option is L-BFGS-B. In simple cases, you do not have to change
   this parameter. In more complex cases, you will have to try all algorithms
   and select the one which fits you the best.

* **On fail**. This parameter is available in the N panel only. This defines
  what the node should do if it was not able to find the extreme point. The
  available options are:

   * **Fail**. The node will raise an exception (become red).
   * **Skip**. The node will skip this input set and process all others.

   The default option is **Fail**.

Outputs
-------

This node has the following outputs:

* **Point**. Extreme point in 3D space.
* **T**. Curve's T parameter, corresponding to the extreme point.

Example of usage
----------------

.. image:: https://user-images.githubusercontent.com/284644/87250867-4d9a3b00-c481-11ea-9726-041087fb8941.png

