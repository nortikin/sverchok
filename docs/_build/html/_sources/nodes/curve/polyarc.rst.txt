Poly Arc
========

Functionality
-------------

This node generates a Curve, which goes through the specified points, made of
series of circular arcs and straight line segments. Arcs are created so that
they touch smoothly in their meeting points. User can specify the tangent
vector of the curve at it's starting point. If such tangent vector is not
specified, the node will calculate it automatically by some algorithm.

Inputs
------

This node has the following inputs:

* **Vertices**. List of points to build a curve through. This input is mandatory.
* **Tangent**. Tangent vector of the curve at it's starting point. This input
  is optional. If not connected, the node will calculate it on it's own.

Parameters
----------

This node has the following parameters:

* **Concatenate**. If checked, the node will concatenate all arcs into one
  Curve object. Otherwise, it will output separate Curve object for each arc.
  Checked by default.
* **Cyclic**. If checked, the node will generate closed (cyclic) curve, by
  connecting the last vertex to the first. Note that the curve will most
  probably be not smooth at that closing point. Unchecked by default.
* **NURBS output**. This parameter is available in the N panel only. If
  checked, the node will output a NURBS curve. Built-in NURBS maths
  implementation will be used. If not checked, the node will output generic
  concatenated curve from several straight segments and circular arcs. In most
  cases, there will be no difference; you may wish to output NURBS if you want
  to use NURBS-specific API methods with generated curve, or if you want to
  output the result in file format that understands NURBS only. Unchecked by
  default.

Outputs
-------

This node has the following outputs:

* **Curve**. Generated Curve object.
* **Center**. Centers of generated circular arcs, together with their orientation.
* **Radius**. Radiuses of generated circular arcs.
* **Angle**. Angles of generated circular arcs, in radians.

Examples of usage
-----------------

A simple example with specified starting tangent vector:

.. image:: https://user-images.githubusercontent.com/284644/83325996-3533df80-a28a-11ea-9e72-7e4c46fa4097.png

An example of closed polyarc curve (note that it is not smooth at the closing point):

.. image:: https://user-images.githubusercontent.com/284644/83328220-e6db0c80-a29a-11ea-9997-ebd3affd43eb.png

The curve is not necessarily should be flat:

.. image:: https://user-images.githubusercontent.com/284644/83325998-36fda300-a28a-11ea-88a4-abbe05f10a7a.png

