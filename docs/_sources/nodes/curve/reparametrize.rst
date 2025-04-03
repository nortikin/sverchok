Reparametrize Curve
===================

.. image:: https://user-images.githubusercontent.com/14288520/211383863-f90734a0-00fc-4fc9-88f2-03eb641d0ea9.png
  :target: https://user-images.githubusercontent.com/14288520/211383863-f90734a0-00fc-4fc9-88f2-03eb641d0ea9.png

Functionality
-------------

Given a Curve, this node generates another Curve object, which represents the
same curve with another parametrization. The parametrization of the curve is
changed so that the domain of the curve would be equal to specified ``[T_min;
T_max]`` interval.

This node may be useful, for example, if you have a curve with domain ``[-1;
5]``, but another node expects a curve with domain ``[0; 1]``.

.. image:: https://user-images.githubusercontent.com/14288520/211384676-4811e872-5fed-4ba1-bb6e-a91ce61d617c.png
  :target: https://user-images.githubusercontent.com/14288520/211384676-4811e872-5fed-4ba1-bb6e-a91ce61d617c.png

* Scene-> :doc:`Bezier Input </nodes/exchange/bezier_in>`
* Curves-> :doc:`Curve Domain </nodes/curve/curve_range>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

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

