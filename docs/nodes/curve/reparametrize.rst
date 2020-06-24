Reparametrize Curve
===================

Functionality
-------------

Given a Curve, this node generates another Curve object, which represents the
same curve with another parametrization. The parametrization of the curve is
changed so that the domain of the curve would be equal to specified ``[T_min;
T_max]`` interval.

This node may be useful, for example, if you have a curve with domain ``[-1;
5]``, but another node expects a curve with domain ``[0; 1]``.

Inputs
------

This node has the following inputs:

* **Curve**. Original curve. This input is mandatory.
* **NewTMin**, **NewTMax**. Lower and upper bounds of the new curve domain.
  Default values are 0 and 1.

Outputs
-------

This node has the following output:

* **Curve**. Reparametrized curve.

