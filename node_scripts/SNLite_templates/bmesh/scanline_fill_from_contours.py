"""
>in verts_in v
>in edges_in s
out verts_out v
out edges_out s
out faces_out s
"""

import bmesh
bool_parameters = dict(
    use_beauty=True, 
    use_dissolve=True
)

# pass input into this node from Component Analyzer (in Edges mode and is_boundary)
# (geom) -> Component Analyzer -> Snlite -> VD

for verts, edges in zip(verts_in, edges_in):
    bm = bmesh_from_pydata(verts, edges, [])
    bmesh.ops.triangle_fill(bm, edges=bm.edges[:], **bool_parameters)
    v, e, f = pydata_from_bmesh(bm)
    _ = [verts_out.append(v), edges_out.append(e), faces_out.append(f)]
