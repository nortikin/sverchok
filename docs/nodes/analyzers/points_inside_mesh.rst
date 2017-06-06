Points Inside Mesh
==================

Functionality
-------------

This node takes a list of probe points, and an associated manifold boundary mesh (verts, faces). It analyses for each of the probe points whether it is located inside or outside of the boundary mesh.

A small implementation issue is the imprecise categorization when the associated boundary mesh is low poly.