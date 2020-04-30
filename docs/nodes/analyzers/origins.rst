Origins
=======

.. image:: https://user-images.githubusercontent.com/28003269/72983385-96d6cf80-3dfa-11ea-900d-fe1448dff5f7.png

Functionality
-------------

The node produces centers, normals, tangents for any element of given mesh. Also it can combine the data into matrix.
The output is close how blender is placing moving axis of selected mesh element in normal mode.

Category
--------

analyzers -> origins

Inputs
------

- **Vertices** - vertices
- **Edges** - edges (optionally)
- **Faces** - faces (optionally)

Outputs
-------

- **Origin** - center of element, in vertex mode just coordinates of current vertex
- **Normal** - normal of current element
- **Tangent** - tangent to current element
- **Matrix** - built from origin, normal and tangent data matrix

Parameters
----------

+--------------------------+-------+--------------------------------------------------------------------------------+
| Parameters               | Type  | Description                                                                    |
+==========================+=======+================================================================================+
| Element mode             | enum  | Vertex, edge or face                                                           |
+--------------------------+-------+--------------------------------------------------------------------------------+
| Flat matrixes list       | bool  | Put matrixes of each input object into one list (N-panel)                      |
+--------------------------+-------+--------------------------------------------------------------------------------+

Usage
-----

Using of corner case of tangent for vertices connected only with one face:

.. image:: https://user-images.githubusercontent.com/28003269/72985862-5bd79a80-3e00-11ea-9b55-1bf9ff814b6a.png

Using matrix output for mesh instancing, looks like work of adaptive polygon node:

.. image:: https://user-images.githubusercontent.com/28003269/72985868-5ed28b00-3e00-11ea-8c9f-dfda491712c9.png