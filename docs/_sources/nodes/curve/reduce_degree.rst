Reduce Degree (NURBS Curve)
===========================

Functionality
-------------

This node reduces (decreases) the degree of a NURBS curve.

The action of this node is the opposite to the action of "Elevate Degree (NURBS Curve)" node.

Degree reduction is the process which can not be always performed exactly. Some
curves can not be degree reduced without visible deviation of curve's geometry.
For other, degree reduction produces only small error.

This node can work only with NURBS and NURBS-like curves.

Inputs
------

This node has the following inputs:

* **Curve**. The curve object to perform operation on. This input is mandatory.
* **Degree**. In **Reduce by** mode, this is the delta to be substracted from
  curve's degree. In **Set degree** mode, this is new curve degree to be set.
  New degree can not be greater than current degree of the curve. The default
  value is 1.
* **Tolerance**. Maximum tolerable deviation of new curve from original. If
  degree reduction process will have error estimation more than this tolerance,
  then, depending on **Only if possible** parameter, the node will either fail or
  return the curve untouched (or degree reduced by less than wanted value). The
  default value is ``0.0001``.

Parameters
----------

This node has the following parameters:

* **Mode**. This defines how the new degree of the curve is specified:

  * In **Reduce by** mode, **Degree** input specifies the number to be substracted
    from current degree of the curve.
  * In **Set degree** mode, **Degree** input specifies the new degree of the
    curve.

* **Only if possible**. If this flag is checked, the node will try to degree
  reduce the curve by requested amount; it it is not possible to do so without
  deviation greater than the specified tolerance, the node will just degree
  reduce the curve the number of times it can. If  not checked, then the node
  will fail (become red) in such a situation, and the processint will stop.
  Unchecked by default.

Outputs
-------

This node has the following output:

* **Curve**. The resulting curve.

Example of Usage
----------------

Here, the initial curve of 3rd degree is reduced to degree of 2. Orange is the
original curve, blue is it's control polygon; green is the resulting curve, and
red is it's control polygon. As you can see, in this case the operation could
not be performed without visible deviation.

.. image:: https://user-images.githubusercontent.com/284644/189500535-3a126895-7a36-453d-af8a-ff4b0615836e.png

