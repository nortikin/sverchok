"""
in verts_in v .=[] n=0
out verts_out v
draw curve_draw
"""
import bpy

evaluate2 = bpy.data.materials['Material'].node_tree.nodes['RGB Curves'].mapping.curves[3].evaluate

def curve_draw(self, context, layout):
    m = bpy.data.materials.get('Material')
    if not m:
        return
    tnode = m.node_tree.nodes['RGB Curves']
    layout.template_curve_mapping(tnode, "mapping", type="NONE")


verts_out = []
for vlist in verts_in:
    verts_out.append([(v[0], v[1], evaluate2(v[2])) for v in vlist])
