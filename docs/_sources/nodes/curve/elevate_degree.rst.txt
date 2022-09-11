Elevate Degree (NURBS Curve)
============================

Functionality
-------------

This node elevates (increases) the degree of a NURBS curve.

The opposite action can be performed with "Reduce Degree (NURBS Curve)" node.

Curves of higher degrees have more control points, and so, with higher degree,
one control point controls smaller segment of the curve.

This node can work only with NURBS and NURBS-like curves.

Inputs
------

This node has the following inputs:

* **Curve**. The curve to perform operation on. This input is mandatory.
* **Degree**. In **Elevate by** mode, this is the delta to be added to curve's
  degree. In **Set degree** mode, this is new curve degree to be set. New
  degree can not be less than current degree of the curve. The default value is
  1.

Parameters
----------

This node has the following parameter:

* **Mode**. This defines how the new degree of the curve is specified:

  * In **Elevate by** mode, **Degree** input specifies the number to be added
    to current degree of the curve.
  * In **Set degree** mode, **Degree** input specifies the new degree of the
    curve.

Outputs
-------

This node has the following output:

* **Curve**. The curve of elevated degree.

Example of Usage
----------------

Here orange is the original curve of 3rd degree, and green is it's control
polygon. Red is the control polygon of curve with elevated (4th) degree.

.. image:: https://user-images.githubusercontent.com/284644/189500544-0b0d70b0-f312-43b6-ac5a-b726bce6ccbd.png

