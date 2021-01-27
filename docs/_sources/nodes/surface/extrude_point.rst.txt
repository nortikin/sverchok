Extrude to Point
================

Functionality
-------------

This node generates a Surface by extruding some Curve (called "profile")
towards one point (also called "tip"). So the resulting surface is, generally
speaking, a conical surface.

Surface domain: along U direction - the same as of "profile" curve; along V
direction - from 0 to 1. V = 0 corresponds to the initial position of profile
curve; V = 1 corresponds to the tip point.

Inputs
------

This node has the following inputs:

* **Profile**. The profile curve. This input is mandatory.
* **Point**. The point towards the profile is to be extruded. The default value is `(0, 0, 0)` (origin).

Outputs
-------

This node has the following output:

* **Surface**. The generated surface.

Examples of usage
-----------------

Extrude a pentagonal polyline towards one point, to make a pyramid:

.. image:: https://user-images.githubusercontent.com/284644/77252629-d133e000-6c76-11ea-9a04-f760827bf659.png

It is possible to use this node to fill planar (or semi-planar) curves with some grid:

.. image:: https://user-images.githubusercontent.com/284644/79359647-4c2da500-7f5c-11ea-8903-26beb236bbac.png

