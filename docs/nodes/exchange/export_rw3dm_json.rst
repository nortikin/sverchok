NURBS to JSON
=============

Dependencies
------------

This node requires Geomdl_ library to work.

.. _Geomdl: https://onurraufbingol.com/NURBS-Python/

Functionality
-------------

This node allows to export a set of NURBS_ Curve or Surface objects to a
JSON format, supported by rw3dm_ utility; that utility can be used to convert
such JSON formath to Rhinoceros ® 3D format.

.. _rw3dm: https://github.com/orbingol/rw3dm
.. _NURBS: https://en.wikipedia.org/wiki/Non-uniform_rational_B-spline

Inputs
------

This node has the following inputs:

* **Curves**. List of NURBS curves to be exported. If passed curves are not
  NURBS, the node will raise an exception. This input is available only when
  **Export** parameter is set to **Curves**.
* **Surfaces**. List of NURBS surfaces to be exported. If passed surfaces are
  not NURBS, the node will raise an exception. This input is available only
  when **Export** parameter is set to **Surfaces**.


Parameters
----------

This node has the following parameters:

* **Export NURBS**. This defines what kind of objects will be exported. The
  available values are **Curves** and **Surfaces**. The default value is
  **Curves**.
* **Text**. This defines the name of Blender's text buffer, where generated
  JSON will be stored. The default value is ``nurbs.json``.

Operators
---------

This node has the following operator button:

* **Export!**. When this button is pressed, the node will take currently
  provided curves or surfaces and write them into Blender's text buffer in JSON
  format.

Outputs
-------

This node does not have any outputs.

