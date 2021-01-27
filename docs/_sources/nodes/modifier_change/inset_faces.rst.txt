Inset faces
===========

.. image:: https://user-images.githubusercontent.com/28003269/70852237-a89e8c00-1eb8-11ea-8563-1ef453f0f50d.png

Functionality
-------------
The node has similar functionality with Blender inset command, so it just insert face into face.
In spite of Blender inset command the node can apply different values per face in most cases.

Category
--------

CAD -> Inset faces

Inputs
------

- **Verts** - vertices of base mesh.
- **Faces** - edges of base mesh (optionally).
- **Edges** - faces of base mesh.
- **Face data** - any data related with given faces like material indexes (optionally).
- **Face mask** - selection list to mark faces in which the node should insert faces, in all daces by default.
- **Thickness** - Set the size of the offset. Can get multiple values - one value per face.
- **Depth** - Raise or lower the newly inset faces to add depth. Can get multiple values - one value per face.

Outputs
-------

- **Verts** - vertices
- **Edges** - edges, one can generate them from faces.
- **Faces** - faces.
- **Face data** - give values according topological changes if face data was given via input socket else give indexes of old faces.
- **Mask** - give selection mask according chosen option(s).

Parameters
----------

+--------------------------+--------+--------------------------------------------------------------------------------+
| Parameters               | Type   | Description                                                                    |
+==========================+========+================================================================================+
| Individual / Region      | switch | Switch between to modes                                                        |
+--------------------------+--------+--------------------------------------------------------------------------------+

N panel
-------

+--------------------------+--------+--------------------------------------------------------------------------------+
| Parameters               | Type   | Description                                                                    |
+==========================+========+================================================================================+
| Offset even              | bool   | Scale the offset to give a more even thickness                                 |
+--------------------------+--------+--------------------------------------------------------------------------------+
| Offset Relative          | bool   | Scale the offset by lengths of surrounding geometry                            |
+--------------------------+--------+--------------------------------------------------------------------------------+
| Boundary                 | bool   | Determines whether open edges will be inset or not                             |
+--------------------------+--------+--------------------------------------------------------------------------------+
| Edge Rail                | bool   | Created vertices slide along the original edges of the inner                   |
|                          |        |                    geometry, instead of the normals                            |
+--------------------------+--------+--------------------------------------------------------------------------------+
| Outset                   | bool   | Create an outset rather than an inset. Causes the geometry to be               |
|                          |        |                 "created surrounding selection (instead of within)             |
+--------------------------+--------+--------------------------------------------------------------------------------+

Usage
-----

Inserting faces with different thickness per face:

.. image:: https://user-images.githubusercontent.com/28003269/70705645-d5527800-1ced-11ea-9042-6a1ec6e09d5b.png

Using face data node for setting color to faces:

.. image:: https://user-images.githubusercontent.com/28003269/70713317-2fa80480-1cff-11ea-9bb7-b8db2fb6264a.png

Mask can be used ofr filtering output mesh with `list mask out` node for example:

.. image:: https://user-images.githubusercontent.com/28003269/70850212-39696d80-1ea1-11ea-9c41-0b6e9b99d420.gif

Insert region mode can be used with multiple input values of thickness and depth
but in this case sometimes result can be unexpected.
The logic of work in this mode is next: mesh split into islands divided by faces with 0 values or 0 mask,
then for each island average thickness and depth is calculated and then faces are inserted.

In this mode outset is not supported.

.. image:: https://user-images.githubusercontent.com/28003269/70794911-2e86de00-1db8-11ea-8e13-1dd8d52fe38b.png

Examples
--------

.. image:: https://user-images.githubusercontent.com/28003269/70851464-f0b8b100-1eae-11ea-840c-f4d61e44826b.png