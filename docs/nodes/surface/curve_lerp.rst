Linear Surface
==============

Functionality
-------------

This node generates a Surface as a linear interpolation of two Curve objects.

Along U parameter, such surface forms a curve calculated as a linear interpolation of two curves.
Along V parameter, such surface is always a straight line.

Surface domain: In U direction - from 0 to 1. In V direction - defined by node inputs, by default from 0 to 1. V = 0 corresponds to the first curve; V = 1 corresponds to the second curve.

Inputs
------

This node has the following inputs:

* **Curve1**. The first curve to interpolate. This input is mandatory.
* **Curve2**. The second curve to interpolate. This input is mandatory.
* **VMin**. The minimum value of curve V parameter. The default value is 0.
* **VMax**. The maximum value of curve V parameter. The default value is 1.

Outputs
-------

This node has the following output:

* **Surface**. The generated surface.

Examples of usage
-----------------

Generate a linear surface between a triangle and a hexagon:

.. image:: https://user-images.githubusercontent.com/284644/79353388-6e232980-7f54-11ea-87a8-b08d78ea34ff.png

Generate a linear surface between two cubic splines:

.. image:: https://user-images.githubusercontent.com/284644/79353383-6cf1fc80-7f54-11ea-855b-ec782edf2c5f.png

