===================
Split Mesh Elements
===================

.. image:: https://user-images.githubusercontent.com/28003269/178970616-173208d4-f0f9-48b1-8d79-4783f280c5a9.png
   :align: right
   :width: 200px

Functionality
-------------

The node split selected by mask elements. It has two modes:

edges
  It's similar to Split -> Faces by Edges Blender tool. When two or more
  touching interior edges, or a border edge is selected, a hole will be created,
  and the selected edges will be duplicated to form the border of the hole.

verts
  It's similar to Split -> Faces & Edges by Vertices Blender tool. It in the
  same way as in edges mode except that it also splits the vertices of the
  adjacent connecting edges.

Inputs
------

**Vertices** - Vertices of the input object

**Edges** - Edges of the input object

**Faces** - Faces of the input object

**FaceData** - Face attribute of the input object

**Mask** - Selection mask. It also has option which type of selection is given
(vertexes, edges or faces selection)

Outputs
-------

**Vertices** - Vertices of the final object

**Edges** - Edges of the final object

**Faces** - Faces of the final object

**FaceData** - Face attribute of the final object

Examples
--------

Split a mesh into random pieces

.. image:: https://user-images.githubusercontent.com/28003269/110217341-e5471080-7ecc-11eb-9954-522478ada365.png
   :width: 700 px
