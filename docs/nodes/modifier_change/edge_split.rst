Split Edges
===========

Functionality
-------------

This node splits each edge of the input mesh. It supports two modes of operation:

* Split each edge in two. Place of split is defined by linear interpolation
  between two vertices of the edge with user-provided factor value.
* Split each edge in three. The edge is split in two places. Each vertex is
  offset from one of vertices of the edge by user-provided factor value.

Inputs
------

This node has the following inputs:

- **Vertices**. Vertices of the input mesh. This input is mandatory.
- **Edges**. Edges of the input mesh. This input is mandatory.
- **Faces**. Faces of the input mesh. This input is optional.
- **EdgeMask**. The mask defining which edges must be split. By default, the
  node splits all edges of the mesh.
- **Factor**. This defines where each edge must be split. The default value is 0.5.

   * If **Mirror** parameter is not checked, then place of split is defined by
     linear interpolation between two vertices of the edge. Values of Factor
     near 0 mean the split point will be near first vertex of the edge, and
     values near 1 mean the split point will be near the second vertex of the
     edge.
   * If **Mirror** parameter is checked, then each edge will be split in two
     places. Each place is defined by linear interpolation between one of
     vertices of the edge and the middle point of the edge. Values of factor
     near 0 will mean split points will be near vertices of the edge. Values of
     factor near 1 will mean split points will be near the middle of the edge.

Parameters
----------

This node has the following parameter:

- **Mirror**. If not checked, each edge will be split in one place. If checked,
  each edge will be split in two places, symmetrical with respect to the middle
  of the edge. Unchecked by default.

Outputs
-------

This node has the following outputs:

* **Vertices**. Vertices of the output mesh.
* **Edges**. Edges of the output mesh.
* **Faces**. Faces of the output mesh. This output is empty if **Faces** input
  is not connected.

