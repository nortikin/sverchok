Ruled Surface
==============

Functionality
-------------

This node generates a Surface as a linear interpolation of two Curve objects.
Such surface is widely known as a ruled surface, or a linear surface.

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

Parameters
----------

This node has the following parameter:

* **Native**. This parameter is available in the N panel only. If checked, then
  the node will try to use specific implementation of the ruled surface for
  cases when it is available. For example, if two curves provided are NURBS
  curves of equal degree, then the node will produce a NURBS surface. When not
  checked, or there is no specific implementation for provided curves, a
  generic algorithm will be used In most cases, the only visible difference is
  that the resulting surface can have different parametrization depending on
  this parameter. Also this parameter can be important if you wish to save the
  resulting surface into some file format that understands NURBS, or for Python
  API usage. Checked by default.

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

