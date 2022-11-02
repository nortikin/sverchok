Bisect
======

.. image:: https://user-images.githubusercontent.com/14288520/198821589-833a940d-ffd1-43fc-85eb-8bf46cca7fa3.png
  :target: https://user-images.githubusercontent.com/14288520/198821589-833a940d-ffd1-43fc-85eb-8bf46cca7fa3.png

Functionality
-------------

This can give the cross section of an object shape from any angle. The implementation is from ``bmesh.ops.bisect_plane`` `see: bisect plane <bisect_plane>`_. It can also provide either side of the cut, separate or joined.

.. image:: https://user-images.githubusercontent.com/14288520/198822836-5e03d362-c761-4be3-8627-a09373cd6045.png
  :target: https://user-images.githubusercontent.com/14288520/198822836-5e03d362-c761-4be3-8627-a09373cd6045.png

Inputs
------

*Vertices*, *PolyEdges* and *Matrix*


Parameters
----------

+-------------+------+-----------------------------------------------------+
| Parameter   | Type | Description                                         |
+=============+======+=====================================================+
| Inner       | bool | don't include the negative side of the Matrix cut   |
+-------------+------+-----------------------------------------------------+
| Outer       | bool | don't include the positive side of the Matrix cut   |
+-------------+------+-----------------------------------------------------+
| Fill cuts   | bool | generates a polygon from the bisections             |
+-------------+------+-----------------------------------------------------+
| Per Object  | bool | One matrix per mesh or multiple matrixes per object |
+-------------+------+-----------------------------------------------------+

* **Inner, Outer**

.. image:: https://user-images.githubusercontent.com/14288520/198823779-7902f7b4-3f7e-4116-92eb-0b40e85b6d91.png
  :target: https://user-images.githubusercontent.com/14288520/198823779-7902f7b4-3f7e-4116-92eb-0b40e85b6d91.png

* **Fill cuts**

.. image:: https://user-images.githubusercontent.com/14288520/198823915-c9021a1d-3232-467f-817a-8d89cc5ae54a.png
  :target: https://user-images.githubusercontent.com/14288520/198823915-c9021a1d-3232-467f-817a-8d89cc5ae54a.png

Advanced Parameters
-------------------

In the N-Panel (and on the right-click menu) you can find:

**Simplify Output**: Method to keep output data suitable for most of the rest of the Sverchok nodes
  - None: Do not perform any change on the data. Only for advanced users
  - Join: The node will join the deepest level of bisections in one object
  - Flat: It will flat the output to keep the one bisection per object (default)

**Match List Global**: Define how list with different lengths should be matched. Refers to the matching of groups (level 1)


Outputs
-------

*Vertices*, *Edges*, and *Polygons*.

See also
--------

* CAD-> :doc:`Crop Mesh 2D </nodes/CAD/crop_mesh_2d>`

Examples
--------

.. image:: https://user-images.githubusercontent.com/14288520/198824224-348d85d8-e823-4321-b3ed-c9d49830677c.png
  :target: https://user-images.githubusercontent.com/14288520/198824224-348d85d8-e823-4321-b3ed-c9d49830677c.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://user-images.githubusercontent.com/14288520/198824283-b664eafc-3e17-4337-b52a-c0a4e111530c.png
  :target: https://user-images.githubusercontent.com/14288520/198824283-b664eafc-3e17-4337-b52a-c0a4e111530c.png

Notes
-----
