Curve Domain
============

Functionality
-------------

This node outputs the domain of the curve, i.e. the range of values the curve's T parameter is allowed to take.

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

