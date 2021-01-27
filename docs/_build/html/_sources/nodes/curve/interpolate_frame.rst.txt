Interpolate Curve Frame
=======================

Dependencies
------------

This node requires SciPy_ library to work.

.. _SciPy: https://scipy.org/

Functionality
-------------

This node takes several matrices (= reference frames), lying along some curve,
and makes a new reference frame (= matrix) by interpolating between these input
frames along the curve.

If the origins of the provided matrices do not lie exactly on the curve, the
matrices will be moved to the curve along their local XOY planes (or another,
depending on the **Orientation** parameter).

Interpolation is calculated by quaternion spherical interpolation ("slerp").

Inputs
------

This node has the following inputs:

* **Curve**. The curve to interpolate the matrices on. This input is mandatory.
* **Frames**. List of matrices (reference frames) along the curve, to
  interpolate between them. This input is mandatory.
* **T**. The value of curve's T parameter to calculate interpolated reference
  frame for. The default value is 0.5.

Parameters
----------

This node hsa the following parameters:

* **Orientation**. The axis of the input reference frames, which is supposed to
  point along curve. The available values are **X**, **Y** and **Z**. The
  default option is **Z**.
* **Curve Resolution**. This affects the precision of finding the correct point
  on the curve for each input matrix. If the curve has very complex form, with
  too small value of this parameter this node can select the wrong point. But
  with higher values the calculation will be slower. The default value is 5,
  which is enough for more or less simple curves.
* **Join**. If checked, the node will output a single flat list of matrices for
  all input curves. Otherwise, it will output a separate list of matrices for
  each input curve. Checked by default.
* **Accuracy**. This parameter is available in the N panel only. Accuracy level
  for finding the correct point on the curve for each input matrix - a number
  of exact digits after decimal point. The default value is 4. In most cases
  you do not have to change this parameter. 

Outputs
-------

This node has the following output:

* **Frame**. The interpolated matrix (reference frame). It's origin is always
  lying on the curve.

Examples of usage
-----------------

Interpolate rotation along the curve to place Suzannes:

.. image:: https://user-images.githubusercontent.com/284644/87054349-7077e580-c21c-11ea-9b65-0936da624e5d.png

Similar, but with rotation around Suzanne's X axis:

.. image:: https://user-images.githubusercontent.com/284644/87055074-4d9a0100-c21d-11ea-83d1-f543cc873086.png

Similar example to build arbitrarily twisted surface:

.. image:: https://user-images.githubusercontent.com/284644/86527479-7e460780-beb8-11ea-9567-d8649b6adeaf.png

Interpolate matrices along the curve:

.. image:: https://user-images.githubusercontent.com/284644/86527477-7d14da80-beb8-11ea-8ed2-5f3e58f4d130.png

