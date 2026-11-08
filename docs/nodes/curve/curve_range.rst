Curve Domain
============

.. image:: https://github.com/user-attachments/assets/efcc1214-0180-4280-a467-6aa4484d5a80
  :target: https://github.com/user-attachments/assets/efcc1214-0180-4280-a467-6aa4484d5a80

Functionality
-------------

This node outputs the domain of the curve, i.e. the range of values the curve's T parameter is allowed to take.

.. image:: https://github.com/user-attachments/assets/32e7bb52-fdc1-4ef3-8a84-c7664d55e61f
  :target: https://github.com/user-attachments/assets/32e7bb52-fdc1-4ef3-8a84-c7664d55e61f

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

.. image:: https://github.com/user-attachments/assets/1e2b4d6b-26c3-4791-8764-3379a083fa2e
  :target: https://github.com/user-attachments/assets/1e2b4d6b-26c3-4791-8764-3379a083fa2e

* Curves-> :doc:`Circle (Curve) </nodes/curve/curve_circle>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`