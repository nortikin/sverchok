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
from math import pi
import bpy
from bpy.props import IntProperty, FloatProperty, EnumProperty, BoolProperty
import bmesh
from mathutils import Matrix


from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, list_match_func, list_match_modes
from sverchok.utils.sv_bmesh_utils import pydata_from_bmesh
from sverchok.utils.sv_mesh_utils import mesh_join

def extend_lists(data, result):
    for d, r in zip(data, result):
        r.extend(d)

def append_lists(data, result):
    for d, r in zip(data, result):
        r.append(d)

def simple_box(b):
    verts = [
        [b, b, -b], [b, -b, -b], [-b, -b, -b],
        [-b, b, -b], [b, b, b], [b, -b, b],
        [-b, -b, b], [-b, b, b]
    ]

    faces = [[0, 1, 2, 3], [4, 7, 6, 5],
             [0, 4, 5, 1], [1, 5, 6, 2],
             [2, 6, 7, 3], [4, 0, 3, 7]]

    edges = [[0, 4], [4, 5], [5, 1], [1, 0],
             [5, 6], [6, 2], [2, 1], [6, 7],
             [7, 3], [3, 2], [7, 4], [0, 3]]

    return verts, edges, faces


class SvBoxNodeMk2(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Box
    Tooltip: Generate a Box primitive.
    """

    bl_idname = 'SvBoxNodeMk2'
    bl_label = 'Box'
    bl_icon = 'MESH_CUBE'

    correct_output_modes = [
        ('NONE', 'None', 'Leave at multi-object level (Advanced)', 0),
        ('JOIN', 'Join', 'Join (mesh join) last level of boxes', 1),
        ('FLAT', 'Flat Output', 'Flat to object level', 2),
    ]
    origin_modes = [
        ('CENTER', 'Center', 'Origin at center of the box', 0),
        ('BOTTOM', 'Bottom', 'Origin at the bottom center of the box', 1),
        ('CORNER', 'Corner', 'Origin at the bottom left front corner of the box', 2),
    ]
    Divx: IntProperty(
        name='Divx', description='divisions x',
        default=1, min=1, options={'ANIMATABLE'},
        update=updateNode)

    Divy: IntProperty(
        name='Divy', description='divisions y',
        default=1, min=1, options={'ANIMATABLE'},
        update=updateNode)

    Divz: IntProperty(
        name='Divz', description='divisions z',
        default=1, min=1, options={'ANIMATABLE'},
        update=updateNode)

    Size: FloatProperty(
        name='Size', description='Size',
        default=1.0, options={'ANIMATABLE'},
        update=updateNode)

    origin: EnumProperty(
        name="Origin",
        description="Behavior on different list lengths, multiple objects level",
        items=origin_modes, default="CENTER",
        update=updateNode)
    list_match_global: EnumProperty(
        name="Match Global",
        description="Behavior on different list lengths, multiple objects level",
        items=list_match_modes, default="REPEAT",
        update=updateNode)
    list_match_local: EnumProperty(
        name="Match Local",
        description="Behavior on different list lengths, object level",
        items=list_match_modes, default="REPEAT",
        update=updateNode)
    correct_output: EnumProperty(
        name="Simplify Output",
        description="Behavior on different list lengths, object level",
        items=correct_output_modes, default="FLAT",
        update=updateNode)


    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "Size").prop_name = 'Size'
        self.inputs.new('SvStringsSocket', "Divx").prop_name = 'Divx'
        self.inputs.new('SvStringsSocket', "Divy").prop_name = 'Divy'
        self.inputs.new('SvStringsSocket', "Divz").prop_name = 'Divz'
        self.inputs.new('SvMatrixSocket', "Matrix")
        self.outputs.new('SvVerticesSocket', "Vers")
        self.outputs.new('SvStringsSocket', "Edgs")
        self.outputs.new('SvStringsSocket', "Pols")

    def draw_buttons(self, context, layout):
        layout.prop(self, "origin", expand=False)

    def draw_buttons_ext(self, context, layout):
        '''draw buttons on the N-panel'''
        layout.prop(self, "origin", expand=True)
        layout.label(text="Simplify Output:")
        layout.prop(self, "correct_output", expand=True)

        layout.separator()
        layout.label(text="List Match:")
        layout.prop(self, "list_match_global", text="Global Match", expand=False)
        layout.prop(self, "list_match_local", text="Local Match", expand=False)

    def rclick_menu(self, context, layout):
        '''right click sv_menu items'''
        layout.prop_menu_enum(self, "origin", text="Origin")
        layout.prop_menu_enum(self, "correct_output", text="Simplify Output")
        layout.prop_menu_enum(self, "list_match_global", text="List Match Global")
        layout.prop_menu_enum(self, "list_match_local", text="List Match Local")

    def makecube(self, params, origin):
        size, divx, divy, divz, matrix = params
        if 0 in (divx, divy, divz):
            return [], []

        b = size / 2.0
        null_matrix = matrix == Matrix()
        if (divx, divy, divz) == (1, 1, 1) and null_matrix and origin == 'CENTER':
            return simple_box(b)


        bm_box = bmesh.new()
        add_vert = bm_box.verts.new
        add_face = bm_box.faces.new

        pos = [
            [[0, 0, b], [0, 'X'], [divx + 1, divy + 1]],
            [[0, 0, -b], [pi, 'X'], [divx + 1, divy + 1]],
            [[0, -b, 0], [pi/2, 'X'], [divx + 1, divz + 1]],
            [[0, b, 0], [-pi/2, 'X'], [divx + 1, divz + 1]],
            [[b, 0, 0], [pi/2, 'Y'], [divz + 1, divy + 1]],
            [[-b, 0, 0], [-pi/2, 'Y'], [divz + 1, divy + 1]],
            ]


        if origin == 'CENTER':
            offset = [0, 0, 0]
        elif origin == 'BOTTOM':
            offset = [0, 0, b]
        else:
            offset = [b, b, b]

        v_len = 0

        for plane_props in pos:
            bm_plane = bmesh.new()
            pos = plane_props[0]
            rot = plane_props[1]
            p_divx = plane_props[2][0]
            p_divy = plane_props[2][1]
            mat_loc = Matrix.Translation((pos[0] + offset[0], pos[1] + offset[1], pos[2] + offset[2]))
            mat_rot = Matrix.Rotation(rot[0], 4, rot[1])
            mat_out = mat_loc @ mat_rot

            bmesh.ops.create_grid(
                bm_plane,
                x_segments=p_divx,
                y_segments=p_divy,
                size=b,
                matrix=mat_out)

            for vert in bm_plane.verts:
                add_vert(vert.co)

            bm_box.verts.index_update()
            bm_box.verts.ensure_lookup_table()

            for face in bm_plane.faces:
                add_face(tuple(bm_box.verts[v.index + v_len] for v in face.verts))
            v_len += len(bm_plane.verts)
            bm_plane.free()


        bmesh.ops.remove_doubles(bm_box, verts=bm_box.verts, dist=1e-6)

        if not null_matrix:
            bmesh.ops.transform(bm_box, matrix=matrix, verts=bm_box.verts)

        verts, edges, faces = pydata_from_bmesh(bm_box, face_data=None)

        return verts, edges, faces

    def process(self):
        inputs = self.inputs
        outputs = self.outputs

        if not any(s.is_linked for s in outputs):
            return

        params_p = [inputs['Size'].sv_get()]

        for s in inputs[1: 4]:
            params_p.append([[int(v) for v in l] for l in s.sv_get()])

        mat_input = inputs['Matrix'].sv_get(default=[[Matrix()]])
        if type(mat_input[0]) == Matrix:
            params_p.append([[m] for m in mat_input])
        else:
            params_p.append(mat_input)

        params = list_match_func[self.list_match_global](params_p)

        verts_out, edges_out, pols_out = [], [], []

        for pa in zip(*params):
            m_par = list_match_func[self.list_match_local](pa)
            v_obj, e_obj, p_obj = [], [], []

            for local_p in zip(*m_par):
                v, e, p = self.makecube(local_p, self.origin)
                append_lists([v,e,p], [v_obj, e_obj, p_obj])


            if self.correct_output == 'FLAT':
                extend_lists([v_obj, e_obj, p_obj], [verts_out, edges_out, pols_out])

            else:
                if self.correct_output == 'JOIN':
                    v_obj, e_obj, p_obj = mesh_join(v_obj, e_obj, p_obj)
                append_lists([v_obj, e_obj, p_obj], [verts_out, edges_out, pols_out])


        outputs['Vers'].sv_set(verts_out)
        outputs['Edgs'].sv_set(edges_out)
        outputs['Pols'].sv_set(pols_out)


def register():
    bpy.utils.register_class(SvBoxNodeMk2)


def unregister():
    bpy.utils.unregister_class(SvBoxNodeMk2)
