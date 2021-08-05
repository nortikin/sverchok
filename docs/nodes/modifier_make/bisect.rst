Bisect
======

Functionality
-------------

This can give the cross section of an object shape from any angle. The implementation is from ``bmesh.ops.bisect_plane``. It can also provide either side of the cut, separate or joined.


Inputs
------

*Vertices*, *PolyEdges* and *Matrix*


Parameters
----------

+-------------+------+-----------------------------------------------------+
| Parameter   | Type | Description                                         |
+=============+======+=====================================================+
| Clear Inner | bool | don't include the negative side of the Matrix cut   |
+-------------+------+-----------------------------------------------------+
| Clear Outer | bool | don't include the positive side of the Matrix cut   |
+-------------+------+-----------------------------------------------------+
| Fill cuts   | bool | generates a polygon from the bisections             |
+-------------+------+-----------------------------------------------------+
| Per Object  | bool | One matrix per mesh or multiple matrixes per object |
+-------------+------+-----------------------------------------------------+

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



Examples
--------

.. image:: https://cloud.githubusercontent.com/assets/619340/4187440/f2a873f6-3769-11e4-9192-01ee23770ec8.PNG
  :alt: bisectdemo1.png

.. image:: https://cloud.githubusercontent.com/assets/619340/4187718/422d78a2-376c-11e4-8634-3d8b84b272d0.PNG
  :alt: bisectdemo2.png

Notes
-----
