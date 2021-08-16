Remove Knot (NURBS Curve)
=========================

Functionality
-------------

This node performs "knot removal" procedure for a NURBS curve.

Given a NURBS Curve object and a knot value, the node reduces the multiplicity
of this knot in curve's knotvector. This procedure can not always be performed.
In general, this procedure changes the shape of the curve. There is "tolerance"
parameter, defining how much is it allowed to change the shape of the curve.

This node can work only with NURBS and NURBS-like curves.

Inputs
------

This node has the following inputs:

* **Curve**. The curve to work on. This input is mandatory.
* **Knot**. The value of the knot to be removed. The default value is 0.5.
* **Count**. Number of times the knot is to be removed. The default value is 1.

Parameters
----------

This node has the following parameters:

* **Only if possible**. If this flag is checked, the node will try to remove
  the knot **Count** times; if it is not possible to remove it that many times,
  the node will just remove it as many times as it can. If not checked, then
  the node will fail (become red) in such a situation, and the processing will
  stop. Unchecked by default.
* **Tolerance**. This parameter is available in the N panel only. This defines
  how much is it allowed to change the shape of the curve by knot removal
  procedure. The default value is ``10^-6``.

Outputs
-------

This node has the following output:

* **Curve**. The resulting curve.

