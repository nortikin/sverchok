NURBS Curve Nodes
=================

Functionality
-------------

This node calculates so-called *node* points (also known as Greville points or
average knot points, or simply edit points) of the NURBS curve.
NURBS curve *nodes* (or Greville abscissaes) are defined as:
``t[i] = sum(u[i+j] for j from 1 to p) / p``, where ``u`` is curve's knotvector, and
``p`` is curve's degree.
NURBS curve *node points* (or Greville points) are points at the curve at
parameter values equal to node values.
The number of curve's nodes is equal to the number of curve's control points.
Node points of the curve are positioned on the curve near corresponding control
points. So in many NURBS algorithms, node points are used to define the shape
of NURBS curve, instead of control points.

Inputs
------

This node has the following input:

* **Curve**. The NURBS Curve object to calculate nodes for. This input is mandatory.

Outputs
-------

This node has the following outputs:

* **Points**. The calculated node points on the curve.
* **T**. The calculated node values (values of curve's T parameter corresponding to node points).

Example of Usage
----------------

Orange is curve's control polygon; dark blue are curve's node points (Greville points):

.. image:: https://user-images.githubusercontent.com/284644/186223165-72a48126-b290-4eb9-a3cc-262fd23bf426.png

