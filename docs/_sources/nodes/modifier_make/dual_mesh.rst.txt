Dual Mesh
=========

Functionality
-------------

This node generates dual mesh for the given mesh. Dual mesh is defined as a
mesh which has vertices at center of each face of source mesh; edges of the
dual mesh connect the vertices, which correspond to faces of original mesh with
common edge.

This node may be useful to convert the mesh consisting of Tris to mesh
consisting to NGons, or backwards.

Note that the volume of dual mesh is always a bit smaller than that of original mesh.

Inputs
------

This node has the following inputs:

- **Vertices**. Vertices of original mesh. This input is mandatory.
- **Edges**. Edges of original mesh.
- **Faces**. Faces of original mesh. This input is mandatory.

Outputs
-------

This node has the following outputs:

- **Vertices**. Vertices of the dual mesh.
- **Faces**. Faces of the dual mesh.

Examples of Usage
-----------------

Dual mesh for cube is an octahedron:

.. image:: https://user-images.githubusercontent.com/284644/68086032-278bb800-fe69-11e9-80d5-5b46bde8d9b0.png

Dual mesh for Voronoi diagram is Delaunay triangulation:

.. image:: https://user-images.githubusercontent.com/284644/68086114-fcee2f00-fe69-11e9-95f5-d57f03dbbf0f.png

