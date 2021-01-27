Random points on mesh
=====================

.. image:: https://user-images.githubusercontent.com/28003269/70866264-f088e600-1f80-11ea-91b2-f8b785c597a3.png

Functionality
-------------
Computes the Constrained Delaunay Triangulation of a set of vertices,
with edges and faces that must appear in the triangulation. Some triangles may be eaten away,
or combined with other triangles, according to output type.
The returned verts may be in a different order from input verts, may be moved slightly,
and may be merged with other nearby verts.

Category
--------

Modifiers -> Modifier make -> Delaunay 2D cdt

Inputs
------

- **Verts** - vertices of given mesh(es)
- **Edges** - edges of given mesh(es)
- **Faces** - faces of given mesh(es)
- **Face data** (optional, one value per face of mesh) - Any data related with given faces.


Outputs
-------

- **Verts** - vertices, some can be deleted
- **Edges** - new and old edges
- **Faces** - new and old faces
- **Face data** - filtered according topology changes given face data if was give one or indexes of old faces

Modes
-----

- **Convex** - given mesh will be triangulated into bounding convex face
- **Inside** - all parts outside given faces or closed edge loops will be ignored by triangulation algorithm

N panel
-------

- **Epsilon** - For nearness tests; number of figures after coma

Examples
--------

**Combine of a line and random points into Delaunay triangulation:**

.. image:: https://user-images.githubusercontent.com/28003269/70866163-b10dca00-1f7f-11ea-9fb3-5af27c211b4a.png

**Triangulation of points inside given face:**

.. image:: https://user-images.githubusercontent.com/28003269/70858673-aa4f6a80-1f1f-11ea-8c94-dbae1ce37909.png

**Keeping color initial faces:**

.. image:: https://user-images.githubusercontent.com/28003269/70865972-0399b700-1f7d-11ea-9d23-c3dafe3158a5.png