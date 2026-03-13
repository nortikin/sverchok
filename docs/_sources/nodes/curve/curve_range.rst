Curve Domain
============

.. image:: https://github.com/nortikin/sverchok/assets/14288520/17bf2239-0e02-4455-8254-480eba33ba93
  :target: https://github.com/nortikin/sverchok/assets/14288520/17bf2239-0e02-4455-8254-480eba33ba93

Functionality
-------------

This node outputs the domain of the curve, i.e. the range of values the curve's T parameter is allowed to take.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/10ab8942-e5b2-4943-85c3-8dd07bf9a99c
  :target: https://github.com/nortikin/sverchok/assets/14288520/10ab8942-e5b2-4943-85c3-8dd07bf9a99c

* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`
* Scene-> :doc:`Bezier Input </nodes/exchange/bezier_in>`

Inputs
------

This node has the following input:

* **Curve**. The curve to be measured. This input is mandatory.

Outputs
-------

This node has the following outputs:

* **TMin**. The minimal allowed value of curve's T parameter.
* **TMax**. The maximum allowed value of curve's T parameter.
* **Range**. The length of curve's domain; this equals to the difference **TMax** - **TMin**.

Example of usage
----------------

The domain of circle curve is from 0 to 2*pi:

.. image:: https://user-images.githubusercontent.com/284644/78507901-792fca00-779c-11ea-90a7-e3c1cfecf39b.png
  :target: https://user-images.githubusercontent.com/284644/78507901-792fca00-779c-11ea-90a7-e3c1cfecf39b.png

* Curves-> :doc:`Circle (Curve) </nodes/curve/curve_circle>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`