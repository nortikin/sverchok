Curve Curvature
===============

Functionality
-------------

This node calculates curve's curvature_ at certain value of the curve's T
parameter. It can also calculate curve's curvature radius and the center of
osculating circle.

.. _curvature: https://en.wikipedia.org/wiki/Curvature#Space_curves

Inputs
------

This node has the following inputs:

* **Curve**. The curve to measure curvature for. This input is mandatory.
* **T**. The value of curve's T parameter to measure curvature at. The default value is 0.5.

Parameters
----------

This node does not have parameters.

Outputs
-------

This node has the following outputs:

* **Curvature**. Curvature value.
* **Radius**. Curvature radius value.
* **Center**. This contains the center of osculating circle as well as circle's orientation.

Example of usage
----------------

Calculate and display curvature at several points of some random curve:

.. image:: https://user-images.githubusercontent.com/284644/78502370-470d7080-777a-11ea-9ee7-648946c89ab5.png

