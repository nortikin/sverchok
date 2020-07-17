JSON to NURBS
=============

Dependencies
------------

This node requires Geomdl_ library to work.

.. _Geomdl: https://onurraufbingol.com/NURBS-Python/

Functionality
-------------

This node allows to import a set of NURBS_ Curve and / or Surface objects from
JSON format, supported by rw3dm_ utility. That utility can be used to generate
such JSON files from Rhinoceros ® 3D file format.

.. _rw3dm: https://github.com/orbingol/rw3dm
.. _NURBS: https://en.wikipedia.org/wiki/Non-uniform_rational_B-spline

Inputs
------

This node does not have any inputs.

Parameters
----------

This node has the following parameter:

* **Text**. The name of Blender's text buffer, from where the JSON definition
  will be read. The default value is `nurbs.json`.

Outputs
-------

This node has the following outputs:

* **Curves**. Curve objects read from JSON file.
* **Surfaces**. Surface objects read from JSON file.

