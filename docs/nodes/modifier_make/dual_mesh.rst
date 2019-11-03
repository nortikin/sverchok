Dual Mesh
=========

Functionality
-------------

This node generates dual mesh for the given mesh. Dual mesh is defined as a
mesh which has vertices at center of each face of source mesh; edges of the
dual mesh connect the vertices, which correspond to faces of original mesh with
common edge.

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

