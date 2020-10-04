Iso U/V Curve
=============

Functionality
-------------

This node generates a curve on the surface, which is defined by setting either
U or V surface parameter to some fixed value and letting the other parameter
slide along it's domain.

If input surface is a NURBS surface, then the node will try to output NURBS curves.

Inputs
------

This node has the following inputs:

* **Surface**. The surface to generate curves on. This input is mandatory.
* **Value**. The value of U or V surface parameter to generate curve at. The default value is 0.5.

Parameters
----------

This node has the following parameter:

* **Join**. If checked, the node will output a single flat list of Curve
  objects for all sets of input parameters. Otherwise, it will output a
  separate list of Curve objects for each set of input parameters. Checked by
  default.

Outputs
-------

This node has the following outputs:

* **UCurve**. The curve obtained by setting the U parameter of the surface to
  **Value** and letting V slide along it's domain. So, this curve is elongated
  along surface's V direction.
* **VCurve**. The curve obtained by setting the V parameter of the surface to
  **Value** and letting U slide along it's domain. So, this curve is elongated
  along surface's U direction.

Example of usage
----------------

Generate some surface and then draw curves along it's V direction:

.. image:: https://user-images.githubusercontent.com/284644/78507210-3a981080-7798-11ea-84b8-d4e6e7d66803.png

