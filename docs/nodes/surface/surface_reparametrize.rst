Reparametrize Surface
=====================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/e7393f95-adf8-40c9-b815-5187240ac6a5
  :target: https://github.com/nortikin/sverchok/assets/14288520/e7393f95-adf8-40c9-b815-5187240ac6a5

Functionality
-------------

Given a Surface, this node generates another Surface object, which represents
the same surface with another parametrization. The parametrization is changed
so that the domain of the new surface would be equal to specified U and V
intervals.

This node may be useful, for example, if you have a surface with domain ``[0;
2] x [0; 2*pi]``, but another node expects a surface with domain ``[0; 1] x [0; 1]``.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/ea1f7a22-17bb-4438-adb6-c70482417613
  :target: https://github.com/nortikin/sverchok/assets/14288520/ea1f7a22-17bb-4438-adb6-c70482417613

Inputs
------

This node has the following inputs:

* **Surface**. The original surface. This input is mandatory.
* **NewUMin**, **NewUMax**. Lower and upper bounds of the new surface domain in
  U parameter. The default values are 0 and 1.
* **NewVMin**, **NewVMax**. Lower and upper bounds of the new surface domain in
  V parameter. The default values are 0 and 1.

Outputs
-------

This node has the following output:

* **Surface**. Reparametrized surface.

