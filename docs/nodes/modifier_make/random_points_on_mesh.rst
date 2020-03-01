Random points on mesh
=====================

.. image:: https://user-images.githubusercontent.com/28003269/70495032-d1282e00-1b26-11ea-8776-1f66d247ceef.png

Functionality
-------------
The node distributes points on given mesh.

Category
--------

Modifiers -> Modifier make -> Random points on mesh

Inputs
------

- **Verts** - vertices of given mesh(es)
- **Faces** - faces of given mesh(es)
- **Face weight** (optional, one value per face of mesh) - any value per face, the less value the less number of vertices generates on current face. Values lessen then 0 will be changed to 0. This input can be used as mask. Just assign 0 values to faces on which there is no need in generation points.
- **Number** (one value per mesh) - number of vertices which should be distributed on given mesh
- **Seed** (one value per mesh) - seed for generation random vertices

Parameters
----------

This node has the following parameters:

- **Proportional**. If checked, then the number of points on each face will be
  proportional to the area of the face (and to the weight provided in the
  **Face weight** input). If not checked, then the number of points on each
  face will be only defined by **Face weight** input. Checked by default.

Outputs
-------

- **Verts** - random vertices on mesh
- **Face index** - indexes of faces to which random vertices lays

Examples
--------

.. image:: https://user-images.githubusercontent.com/28003269/70305616-4b526d00-181e-11ea-9133-e3391bf4453b.png

**Normals of faces of sphere, located on random points**

.. image:: https://user-images.githubusercontent.com/28003269/70305528-11816680-181e-11ea-8cc4-e755d9380b7a.png

**Distribution of points on sphere surface according distance to floating point**

.. image:: https://user-images.githubusercontent.com/28003269/70341948-7d3ef000-186d-11ea-8136-2fccad23be08.gif

**Voronoi from unevenly distributed points on faces**

.. image:: https://user-images.githubusercontent.com/28003269/70436420-ad230900-1aa2-11ea-869b-2d1993bd492a.png
