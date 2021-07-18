Insert Knot (NURBS Curve)
=========================

Functionality
-------------

This node performs "knot insertion" operation on a NURBS curve object.

Given a NURBS Curve, the node adds the provided value into curve's knotvector.
If the provided value is already present in the knotvector, it's multiplicity
will be increased.

This node can work only with NURBS and NURBS-like curves.

It is possible to provide a list of knot values (and corresponding
multiplicities) for each curve.

Inputs
------

This node has the following inputs:

* **Curve**. The Curve object to work with. This input is mandatory.
* **Knot**. The value of the new knot. The default value is 0.5.
* **Count**. Number of times the knot is to be inserted. The default value is 0.

Outputs
-------

This node has the following output:

* **Curve**. The resulting Curve object.

Example of Usage
----------------

Insert a knot twice into a circle curve, and move the new control point:

.. image:: https://user-images.githubusercontent.com/284644/126066221-95589c16-c04d-4b9c-add7-19c6ad4ab906.png

