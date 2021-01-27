Concatenate Curves
==================

Functionality
-------------

This node composes one Curve object from several Curve objects, by "glueing"
their ends. It assumes that end points of the curves being concatenated are
already coinciding. You can make the node check this fact additionaly.

Curve domain: summed up from domains of curves being concatenated.

Inputs
------

This node has the following input:

* **Curves**. A list of curves to be concatenated. This input is mandatory.

Parameters
----------

This node has the following parameters:

* **Check coincidence**. If enabled, then the node will check that the end points of curves being concatenated do actually coincide (within threshold). If they do not, the node will give an error (become red), and the processing will stop.
* **Max distance**. Maximum distance between end points of the curves, which is allowable to decide that they actually coincide. The default value is 0.001. This parameter is only available if **Check coincidence** parameter is enabled.
* **All NURBS**. This parameter is available in the N panel only. If checked,
  then the node will try to convert all input curves to NURBS, and output a
  NURBS curve. The node will fail (become red) if it was not able either to
  convert one of input curves, or join resulting NURBS curves.

Outputs
-------

This node has the following output:

* **Curve**. The resulting concatenated curve.

Example of usage
----------------

Make single curve from two segments of line and an arc:

.. image:: https://user-images.githubusercontent.com/284644/77555651-50c0e980-6ed9-11ea-915f-8eb490c5904f.png

