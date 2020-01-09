# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import bpy
from bpy.props import IntProperty, FloatProperty, BoolProperty, EnumProperty, FloatVectorProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, fullList, match_long_repeat
from sverchok.utils.modules.geom_utils import interp_v3_v3v3, normalize, add_v3_v3v3, sub_v3_v3v3

directionItems = [
    ("X", "X", "Along X axis", 0),
    ("Y", "Y", "Along Y axis", 1),
    ("Z", "Z", "Along Z axis", 2),
    ("AB", "AB", "Between 2 points", 3),
    ("OD", "OD", "Origin and Direction", 4),
]


def make_line(steps, center, direction, vert_a, vert_b):
    if direction == "X":
        vec = lambda l: (l, 0.0, 0.0)
    elif direction == "Y":
        vec = lambda l: (0.0, l, 0.0)
    elif direction == "Z":
        vec = lambda l: (0.0, 0.0, l)
    elif direction in ["AB", "OD"]:
        vec = lambda l: interp_v3_v3v3(vert_a, vert_b, l)

    verts = []
    add_vert = verts.append
    x = -sum(steps) / 2 if center else 0
    for s in [0.0] + steps:
        x = x + s
        add_vert(vec(x))
    edges = [[i, i + 1] for i in range(len(steps))]
    return verts, edges


class SvLineNodeMK3(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Line, segment.
    Tooltip: Generate line.
    """
    bl_idname = 'SvLineNodeMK3'
    bl_label = 'Line'
    bl_icon = 'GRIP'
    sv_icon = 'SV_LINE'

    def update_size_socket(self, context):
        """ need to do UX transformation before updating node"""
        size_socket = self.inputs["Size"]
        size_socket.hide_safe = not self.normalize

        updateNode(self, context)

    def update_vect_socket(self, context):
        """ need to do UX transformation before updating node"""
        si = self.inputs
        sd = self.direction
        if sd == "OD" and not si[3].name[0] == "O":
            si[3].name = "Origin"
            si[4].name = "Direction"
            si[3].prop_name = 'v3_origin'
            si[4].prop_name = 'v3_dir'
        elif sd == "AB" and not si[3].name[0] == "A":
            si[3].name = "A"
            si[4].name = "B"
            si[3].prop_name = 'v3_input_0'
            si[4].prop_name = 'v3_input_1'

        ortho = sd not in ["AB", "OD"]
        if (not ortho and si[3].hide_safe) or ortho:
            si[3].hide_safe = ortho
            si[4].hide_safe = ortho

        updateNode(self, context)

    direction: EnumProperty(
        name="Direction", items=directionItems,
        default="X", update=update_vect_socket)

    num: IntProperty(
        name='Num Verts', description='Number of Vertices',
        default=2, min=2, update=updateNode)

    step: FloatProperty(
        name='Step', description='Step length',
        default=1.0, update=updateNode)

    center: BoolProperty(
        name='Center', description='Center the line',
        default=False, update=updateNode)

    normalize: BoolProperty(
        name='Normalize', description='Normalize line to size',
        default=False, update=update_size_socket)

    size: FloatProperty(
        name='Size', description='Size of line',
        default=10.0, update=updateNode)

    v3_input_0: FloatVectorProperty(
        name='A', description='Starting point',
        size=3, default=(0, 0, 0),
        update=updateNode)

    v3_input_1: FloatVectorProperty(
        name='B', description='End point',
        size=3, default=(0.5, 0.5, 0.5),
        update=updateNode)

    v3_origin: FloatVectorProperty(
        name='Origin', description='Origin of line',
        size=3, default=(0, 0, 0),
        update=updateNode)

    v3_dir: FloatVectorProperty(
        name='Direction', description='Direction',
        size=3, default=(1, 1, 1),
        update=updateNode)

    def set_size_socket(self):
        size_socket = self.inputs.new('SvStringsSocket', "Size")
        size_socket.prop_name = 'size'
        size_socket.hide_safe = not self.normalize

    def set_vector_sockets(self):
        si = self.inputs
        si.new('SvVerticesSocket', "A").prop_name = 'v3_input_0'
        si.new('SvVerticesSocket', "B").prop_name = 'v3_input_1'
        si[3].hide_safe = self.direction not in ["AB", " OD"]
        si[4].hide_safe = self.direction not in ["AB", " OD"]

    def sv_init(self, context):
        si = self.inputs
        si.new('SvStringsSocket', "Num").prop_name = 'num'
        si.new('SvStringsSocket', "Step").prop_name = 'step'
        self.set_size_socket()
        self.set_vector_sockets()
        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket', "Edges")

    def draw_buttons(self, context, layout):
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, "direction", expand=True)
        row = col.row(align=True)
        row.prop(self, "center", toggle=True)
        row.prop(self, "normalize", toggle=True)

    def get_data(self):
        c, d = self.center, self.direction
        input_num = self.inputs["Num"].sv_get()
        input_step = self.inputs["Step"].sv_get()
        normal_size = [2.0 if c else 1.0]

        if self.normalize:
            normal_size = self.inputs["Size"].sv_get()[0]

        params = [input_num, input_step, normal_size]

        if d in ["AB", "OD"]:
            v_a = self.inputs[3].sv_get()[0]
            v_b = self.inputs[4].sv_get()[0]
            params.append(v_a)
            params.append(v_b)

        return match_long_repeat(params)

    def define_steplist(self, step_list, s, n, nor, normal):

        for num in n:
            num = max(2, num)
            s = s[:(num - 1)]  # shorten if needed
            fullList(s, num - 1)  # extend if needed
            step_list.append([S * nor / sum(s) for S in s] if normal else s)

    def process_vectors(self, pts_list, d, va, vb):
        if d == "AB" and self.normalize:
            vb = add_v3_v3v3(normalize(sub_v3_v3v3(vb, va)), va)
        elif d == "OD":
            vb = add_v3_v3v3(normalize(vb), va)
        pts_list.append((va, vb))

    def process(self):
        if not any(s.is_linked for s in self.outputs):
            return

        c, d = self.center, self.direction
        step_list = []
        pts_list = []
        verts_out, edges_out = [], []
        normal = self.normalize or d == "AB"
        advanced = d in ["AB", "OD"]
        params = self.get_data()
        if advanced:
            for p in zip(*params):
                n, s, nor, va, vb = p
                self.define_steplist(step_list, s, n, nor, normal)
                self.process_vectors(pts_list, d, va, vb)
            for s, vc in zip(step_list, pts_list):
                r1, r2 = make_line(s, c, d, vc[0], vc[1])
                verts_out.append(r1)
                edges_out.append(r2)
        else:
            for p in zip(*params):
                n, s, nor = p
                self.define_steplist(step_list, s, n, nor, normal)
            for s in step_list:
                r1, r2 = make_line(s, c, d, [], [])
                verts_out.append(r1)
                edges_out.append(r2)

        if self.outputs['Vertices'].is_linked:
            self.outputs['Vertices'].sv_set(verts_out)
        if self.outputs['Edges'].is_linked:
            self.outputs['Edges'].sv_set(edges_out)


def register():
    bpy.utils.register_class(SvLineNodeMK3)


def unregister():
    bpy.utils.unregister_class(SvLineNodeMK3)