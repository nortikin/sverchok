Separate parts to indexes
=========================

.. image:: https://user-images.githubusercontent.com/28003269/73426269-4f49c980-434d-11ea-8dab-36513715f09a.png

Functionality
-------------
Marks mesh elements by indexes. All disjoint parts of mesh have different indexes.
Elements of one part have a same index.

Category
--------

Modifiers -> modifier change -> Separate perts to indexes

Inputs
------

- **Vertices** - vertices
- **Edges** - edges (optionally if faces are connected)
- **Faces** - faces (optionally if edges are connected)

Outputs
-------

- **Vert index** - index mask of verts
- **Edge index** - index mask of edges
- **Face index** - index mask of faces

Examples
--------

Using index mask for assigning material to separate parts of mesh:

.. image:: https://user-images.githubusercontent.com/28003269/72244444-b6564700-3607-11ea-8662-51727aaddfb4.png

Moving disjoint parts =):

.. image:: https://user-images.githubusercontent.com/28003269/73347577-469bb980-42a1-11ea-889b-b4d87c754f2d.gif

.. image:: https://user-images.githubusercontent.com/28003269/73347608-53201200-42a1-11ea-96bb-358ada087da4.png