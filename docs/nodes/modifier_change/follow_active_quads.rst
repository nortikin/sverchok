Follow active quads
===================

.. image:: https://user-images.githubusercontent.com/28003269/72198433-af340b00-3446-11ea-95f3-caa61581220a.png

Functionality
-------------
The Follow Active Quads node takes the selected faces and lays them out by following continuous face loops,
even if the mesh face is irregularly-shaped. Note that it does not respect the image size, so you may have
to scale them all down a bit to fit the image area. Also it ignores any faces with number of edges unequal 4.

**Note:**

Please note that it is the shape of the active quad in UV space that is being followed, not its shape in 3D space.
To get a clean 90-degree unwrap make sure the active quad is a rectangle in UV space before using `Follow active quad`.
If active face does not have UV map, in case when UV vertices and UV faces was not connected to the node
or all UV coordinate have X and Y equal 0, than unwrapping are created automatically.
Default unwrapping is quad with sides equal 1.

Category
--------

Modifiers -> Modifier change -> Follow active quads

Inputs
------

- **Verts** - vertices of a mesh
- **Faces** - faces of a mesh (don't try to plug edges)
- **UV verts** - also regular 3d vertices, optionally
- **UV faces** - standard faces which represent 2D representation of given mesh (UV map), optionally
- **Index active quad** - index(es) of active quad, start of unwrapping, default 0
- **Face mask** - selection mask, True (1) are selection of face, optional, by default all faces are selected

Outputs
-------

- **UV verts** - 3d vertices
- **UV faces** - standard faces which represent 2D representation of given mesh (UV map)

Parameters
----------

+--------------------------+-------+--------------------------------------------------------------------------------+
| Parameters               | Type  | Description                                                                    |
+==========================+=======+================================================================================+
| Edge length mode         | enum  | Even, length, average length                                                   |
+--------------------------+-------+--------------------------------------------------------------------------------+
| all                      | bool  | Unwrap all mesh, useful if mesh has disjoint parts                             |
+--------------------------+-------+--------------------------------------------------------------------------------+

- **Even** - Space all UVs evenly.
- **Length** - Average space UVs edge length of each loop.
- **Average** - undocumented *(does not find in Blender help)*

Active index
------------

By default active quad index is 0. If active quad is not a quad you will get error of node.
Also it is possible to set multiple indexes. It can be useful if a mesh has multiple disjoint parts.
The node has protection from re unwrapping. If face a face was unwrapping once it will never be unwrapping again.
So you can set indexes of all faces in mesh but all faces will be unwrapped only once from first index of active face.

Examples
--------

Logic of unwrapping according shape of active quad:

.. image:: https://user-images.githubusercontent.com/28003269/71973268-f7291700-3227-11ea-9792-2676ebf35d39.gif

.. image:: https://user-images.githubusercontent.com/28003269/71924095-bd183080-31a7-11ea-8ce8-94d1915a2c8f.png

Setting indexes of all faces of mesh (or just click `all` button) for unwrapping all mesh:

.. image:: https://user-images.githubusercontent.com/28003269/72132929-a1747c00-3399-11ea-8da4-bdd039cd7c7e.png