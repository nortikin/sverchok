Subdivide Lite Node
==============

Functionality
-------------

This node applies Blender's Subvidide operation to the input mesh. Please note that of options available differs from usual editing operator.

Inputs
------

This node has the following inputs:

- **Vertices**. Put here vertices of mesh.
- **edge_poly**. Put here edges or polygons of mesh.
- **Selection**. Selected edges to be subdivided. Can be selected by "bool mask" or "int index". Faces surrounded by subdivided edges can optionally be subdivided too.

Parameters
----------

This node has the following parameters:

- **Show Options**. If checked, then following parameters will be shown on the node.
- **Show Old**. If checked, then outputs with "old" geometry will be shown. By default not checked.
- **Show New**. If checked, then outputs with newly created geometry will be shown. By default not checked.
- **Falloff**. Smooth falloff type. Please refer to examples below for demonstration.
- **Corner cut type**. This controls the way quads with only two adjacent selected edges are subdivided. Available values are:

  - **Inner vertices**
  - **Path**
  - **Fan**
  - **Straight Cut**
- **Select**. This controls which data Selection socket expects to select edges to which subdivision must be applied:

  - **by mask**. list of boolean like values.
  - **by index**. list of indices.
- **Grid fill**. If checked, then fully-selected faces will be filled with a grid (subdivided). Otherwise, only edges will be subdiveded, not faces. Checked by default.
- **Only Quads**. If checked, then only quad faces will be subdivided, other will not. By default not checked.
- **Single edge**. If checked, tessellate the case of one edge selected in a quad or triangle. By default not checked.
- **Even smooth**. Maintain even offset when smoothing. By default not checked.
- **Number of Cuts**. Specifies the number of cuts per edge to make. By default this is 1, cutting edges in half. A value of 2 will cut it into thirds, and so on.
- **Smooth**. Displaces subdivisions to maintain approximate curvature, The effect is similar to the way the Subdivision Surface Modifier might deform the mesh.
- **Fractal**. Displaces the vertices in random directions after the mesh is subdivided.
- **Along normal**. If set to 1, causes the vertices to move along the their normals, instead of random directions. Values between 0 and 1 lead to intermediate results.
- **Seed**. Random seed.

Outputs
-------

This node has the following outputs:

- **Vertices**. All vertices of resulting mesh.
- **Edges**. All edges of resulting mesh.
- **Faces**. All faces of resulting mesh.
- **NewVertices**. All vertices that were created by subdivision. This output is only visible when **Show New** parameter is checked.
- **NewEdges**. Edges that were created by subdividing faces. This output is only visible when **Show New** parameter is checked.
- **NewFaces**. Faces that were created by subdividing faces. This output is only visible when **Show New** parameter is checked.
- **OldVertices**. Only vertices that were created on previously existing edges. This output is only visible when **Show Old** parameter is checked.
- **OldEdges**. Only edges that were created by subdividing existing edges. This output is only visible when **Show Old** parameter is checked.
- **OldFaces**. Only faces that were created by subdividing existing faces. This output is only visible when **Show Old** parameter is checked.

**Note**: Indicies in **NewEdges**, **NewFaces**, **OldEdges**, **OldFaces** outputs relate to vertices in **Vertices** output.

Examples of usage
-----------------
.. image:: https://user-images.githubusercontent.com/22656834/36314797-ba6d502e-1357-11e8-9ce1-1e856f7e056f.png
