Helix (FreeCAD)
===============

Dependencies
------------

This node requires FreeCAD_ libraries installed to work.

.. _FreeCAD: https://www.freecadweb.org/

Functionality
-------------

This node generates a helix Curve. The helix can be either cylyndrical (by default) or conical.

The produced Curve object is NURBS-like, i.e. will be automatically converted
to NURBS by nodes which require NURBS curves.

Inputs
------

This node has the following inputs:

* **Radius**. Helix radius. The default value is 1.0.
* **Height**. Helix height. The default value is 4.0.
* **Pitch**. Helix pitch, i.e. the distance between turns of the helix. The
  default value is 1.0.
* **Angle**. Apex angle of the cone for conic helixes, in degrees; when this is
  set to 0 (by default), the node will generate a cylindrical helix.

Parameters
----------

This node has the following parameter:

* **Join**. When checked, the node will generate one flat list of Curves for
  all values in the input. If not checked, the node will produce a separate
  list of Curves for each list of input parameters. Unchecked by default.

Outputs
-------

This node has the following output:

* **Curve**. The generated helix Curve object.

Example of usage
----------------

.. image:: https://user-images.githubusercontent.com/284644/92306255-20609980-efa7-11ea-8efe-9903c10034d7.png

