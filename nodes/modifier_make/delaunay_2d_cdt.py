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


def get_delaunay(verts, edges=None, faces=None, face_data=None, mode=0, epsilon=1e-5):
    """
    Crete delaunay triangulation from given mesh, can cut by given faces and closed edge loops in mode=1
    :param verts: list of Sv vertices
    :param edges: list of (int, int)
    :param faces: list of list int
    :param face_data: any data related with given faces
    :param mode: 0 or 1, when 1 it does not consider mesh outside given faces and closed edges loops
    :param epsilon: int > 0; For nearness tests; should not be zero
    :return: list of Sv vertices, edges, faces, filtered related with faces data if given
    or indexes of old given faces per new face
    """
    if edges is None:
        edges = []
    if faces is None:
        faces = []
    bl_verts = [Vector(co[:2]) for co in verts]
    new_verts, new_edges, new_faces, orig_v, orig_e, orig_f = bl_delaunay(bl_verts, edges, faces, mode, epsilon)
    if face_data:
        face_data_out = [face_data[li[0] if li else -1] for li in orig_f]
    else:
        face_data_out = [li[0] if li else -1 for li in orig_f]
    return [v.to_3d()[:] for v in new_verts], new_edges, new_faces, face_data_out


class SvDelaunay2DCdt(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Delaunay triangulation 2D
    Tooltip: Can crete triangulation inside given faces or closed edge loops

    Also it finds intersection of given edges
    """
    bl_idname = 'SvDelaunay2DCdt'
    bl_label = 'Delaunay 2D Cdt'
    bl_icon = 'MOD_BOOLEAN'
    sv_icon = 'SV_DELAUNAY'

    mode_list = ['convex', 'inside']
    mode_items = [(v, v.title(), "", i) for i, v in enumerate(mode_list)]

    mode: bpy.props.EnumProperty(items=mode_items, update=updateNode, description="What output looks like")
    epsilon: bpy.props.IntProperty(name='Epsilon', update=updateNode, default=5, min=3, max=12,
                                    description='For nearness tests; should not be zero')

    def draw_buttons(self, context, layout):
        if not bl_delaunay:
            layout.label(text="For 2.81+ only")
        else:
            layout.prop(self, 'mode', expand=True)

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, 'epsilon')

    def sv_init(self, context):
        if bl_delaunay:
            self.inputs.new('SvVerticesSocket', 'Verts')
            self.inputs.new('SvStringsSocket', "Edges")
            self.inputs.new('SvStringsSocket', "Faces")
            self.inputs.new('SvStringsSocket', "Face data")
            self.outputs.new('SvVerticesSocket', 'Verts')
            self.outputs.new('SvStringsSocket', "Edges")
            self.outputs.new('SvStringsSocket', "Faces")
            self.outputs.new('SvStringsSocket', "Face data")

    def process(self):
        if not self.inputs['Verts'].is_linked:
            return

        out = []
        for v, e, f, fd in zip(self.inputs['Verts'].sv_get(),
                           self.inputs['Edges'].sv_get() if self.inputs['Edges'].is_linked else cycle([None]),
                           self.inputs['Faces'].sv_get() if self.inputs['Faces'].is_linked else cycle([None]),
                           self.inputs['Face data'].sv_get() if self.inputs['Face data'].is_linked else cycle([None])):
            out.append(get_delaunay(v, e, f, fd, self.mode_list.index(self.mode), 1 / 10 ** self.epsilon))
        out_v, out_e, out_f, out_fd = zip(*out)
        self.outputs['Verts'].sv_set(out_v)
        self.outputs['Edges'].sv_set(out_e)
        self.outputs['Faces'].sv_set(out_f)
        self.outputs['Face data'].sv_set(out_fd)


def register():
    bpy.utils.register_class(SvDelaunay2DCdt)


def unregister():
    bpy.utils.unregister_class(SvDelaunay2DCdt)
