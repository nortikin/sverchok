Curve Torsion
=============

Functionality
-------------

This node calculates the torsion_ value of a curve at the certain value of curve's T paramter.

.. _torsion: https://en.wikipedia.org/wiki/Torsion_of_a_curve

Inputs
------

This node has the following inputs:

* **Curve**. The curve to measure torsion for. This input is mandatory.
* **T**. The value of curve's T parameter to measure torsion at. The default value is 0.5.

Parameters
----------

This node does not have parameters.

Outputs
-------

This node has the following output:

* **Torsion**. The torsion value.

Example of usage
----------------

Calculate torsion value at several points of some random curve:

.. image:: https://user-images.githubusercontent.com/284644/78502538-12e67f80-777b-11ea-8ba6-d4d1d6360ce2.png

Note that calculating torsion at end points of a curve, or at some other
signular points of the curve may give unusable results.

