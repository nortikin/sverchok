triangle fill scanline
======================

This node's primary purpose is to provide a Node version of *bmesh.ops.triangle_fill*. The essence of this node is
similar to `Edges To Faces` node, with the exception that when no edges are connected, the node will assume that the input
consists of closed rings, and it will internally generate the correct Edge indices for the provided Vertex lists.

- this is useful for fill complex islands/rings of polylines, as you might find in GIS content or Typography Glyph outlines.
- has built in option to Merge the incoming meshes.
- for complex and irregular Ngons this node will generate superior Polygons compared with UVConnection node.