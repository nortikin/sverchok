# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


from itertools import cycle

import bpy
from mathutils import Vector

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

try:
    from mathutils.geometry import delaunay_2d_cdt as bl_delaunay
except ImportError:
    print("Sv: The 'Delaunay 2D Cdt' node is not available in your Blender version. Blender 2.81+ is required")
    bl_delaunay = None


def get_delaunay(verts, edges=None, faces=None, mode=0, epsilon=1e-5):
    if edges is None:
        edges = []
    if faces is None:
        faces = []
    bl_verts = [Vector(co[:2]) for co in verts]
    new_verts, new_edges, new_faces, _, _, _ = bl_delaunay(bl_verts, edges, faces, mode, epsilon)
    return [v.to_3d()[:] for v in new_verts], new_edges, new_faces


class SvDelaunay2DCdt(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: ...
    Tooltip: ...

    ...
    """
    bl_idname = 'SvDelaunay2DCdt'
    bl_label = 'Delaunay 2D Cdt'
    bl_icon = 'MOD_BOOLEAN'

    mode_list = ['convex', 'inside', 'intersected', 'extra edges']
    mode_items = [(v, v.title(), "", i) for i, v in enumerate(mode_list)]

    mode: bpy.props.EnumProperty(items=mode_items, update=updateNode, description="What output looks like")
    epsilon: bpy.props.IntProperty(name='Epsilon', update=updateNode, default=5, min=3, max=12,
                                    description='For nearness tests; should not be zero')

    def draw_buttons(self, context, layout):
        if not bl_delaunay:
            layout.label(text="For 2.81+ only")
        else:
            layout.prop(self, 'mode', text="")

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, 'epsilon')

    def sv_init(self, context):
        if bl_delaunay:
            self.inputs.new('SvVerticesSocket', 'Verts')
            self.inputs.new('SvStringsSocket', "Edges")
            self.inputs.new('SvStringsSocket', "Faces")
            self.outputs.new('SvVerticesSocket', 'Verts')
            self.outputs.new('SvStringsSocket', "Edges")
            self.outputs.new('SvStringsSocket', "Faces")

    def process(self):
        if not self.inputs['Verts'].is_linked:
            return

        out = []
        for v, e, f in zip(self.inputs['Verts'].sv_get(),
                           self.inputs['Edges'].sv_get() if self.inputs['Edges'].is_linked else cycle([None]),
                           self.inputs['Faces'].sv_get() if self.inputs['Faces'].is_linked else cycle([None])):
            out.append(get_delaunay(v, e, f, self.mode_list.index(self.mode), 1 / 10 ** self.epsilon))
        out_v, out_e, out_f = zip(*out)
        self.outputs['Verts'].sv_set(out_v)
        self.outputs['Edges'].sv_set(out_e)
        self.outputs['Faces'].sv_set(out_f)


def register():
    bpy.utils.register_class(SvDelaunay2DCdt)


def unregister():
    bpy.utils.unregister_class(SvDelaunay2DCdt)
