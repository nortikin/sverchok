Curve Segment
=============

Functionality
-------------

This node generates a curve which is defined as a subset of the input curve
with a smaller range of allowed T parameter values. In other words, the output
curve is the same as input one, but with restricted range of T values allowed.

Output curve domain: defined by node inputs.

Output curve parametrization: the same as of input curve.

Inputs
------

This node has the following inputs:

* **Curve**. The curve to be cut. This input is mandatory.
* **TMin**. The value of curve's T parameter, at which the new curve should start. The default value is 0.2.
* **TMax**. The value of curve's T parameter, at which the new curve should end. The default value is 0.8.

Parameters
----------

This node has the following parameter:

* **Rescale to 0..1**. If checked, then the generated curve will have the
  domain (allowed range of T parameter values)  of `[0.0 .. 1.0]`. Otherwise,
  the domain of generated curve will be defined by node's inputs, i.e. `[TMin
  .. TMax]`. Unchecked by default.

Outputs
-------

This node has the following output:

* **Segment**. The resulting curve segment.

Examples of usage
-----------------

Generate some random curve (green) and take a subset from it with T values from 0.2 to 0.8 (red):

.. image:: https://user-images.githubusercontent.com/284644/78508073-99ac5400-779d-11ea-9a01-1d8824934ae4.png

Generate several segments of the same curve with different ranges of T parameter, to generate a dashed line:

.. image:: https://user-images.githubusercontent.com/284644/78508072-987b2700-779d-11ea-9b53-6490db257aed.png

