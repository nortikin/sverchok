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
from bpy.props import IntProperty, FloatProperty
import bmesh
from mathutils import Vector, Matrix


from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata, pydata_from_bmesh

class SvBoxNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Box
    Tooltip: Generate a Box primitive.
    """

    bl_idname = 'SvBoxNode'
    bl_label = 'Box'
    bl_icon = 'MESH_CUBE'

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

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "Size").prop_name = 'Size'
        self.inputs.new('SvStringsSocket', "Divx").prop_name = 'Divx'
        self.inputs.new('SvStringsSocket', "Divy").prop_name = 'Divy'
        self.inputs.new('SvStringsSocket', "Divz").prop_name = 'Divz'
        self.outputs.new('SvVerticesSocket', "Vers")
        self.outputs.new('SvStringsSocket', "Edgs")
        self.outputs.new('SvStringsSocket', "Pols")

    def draw_buttons(self, context, layout):
        pass

    def makecube(self, size, divx, divy, divz):
        if 0 in (divx, divy, divz):
            return [], []

        b = size / 2.0

        if (divx, divy, divz) == (1, 1, 1):
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

        v_len = 0

        for plane_props in pos:
            bm = bmesh.new()
            pos = plane_props[0]
            rot = plane_props[1]
            p_divx = plane_props[2][0]
            p_divy = plane_props[2][1]
            mat_loc = Matrix.Translation((pos[0], pos[1], pos[2]))
            mat_rot = Matrix.Rotation(rot[0], 4, rot[1])
            mat_out = mat_loc @ mat_rot

            bmesh.ops.create_grid(bm,
                x_segments=p_divx ,
                y_segments=p_divy,
                size=b,
                matrix=mat_out)

            for v in bm.verts:
                add_vert(v.co)

            bm_box.verts.index_update()
            bm_box.verts.ensure_lookup_table()

            for f in bm.faces:
                add_face(tuple(bm_box.verts[v.index + v_len] for v in f.verts))
            v_len += len(bm.verts)
            bm.free()


        bmesh.ops.remove_doubles(bm_box, verts=bm_box.verts, dist=1e-6)
        # bmesh.ops.recalc_face_normals(bm_box, faces=bm_box.faces)
        verts, edges, faces = pydata_from_bmesh(bm_box, face_data=None)

        return verts, edges, faces

    def process(self):
        inputs = self.inputs
        outputs = self.outputs

        # I think this is analoge to preexisting code, please verify.
        size = inputs['Size'].sv_get()[0]
        divx = int(inputs['Divx'].sv_get()[0][0])
        divy = int(inputs['Divy'].sv_get()[0][0])
        divz = int(inputs['Divz'].sv_get()[0][0])

        out = [a for a in (zip(*[self.makecube(s, divx, divy, divz) for s in size]))]

        # outputs, blindly using sv_set produces many print statements.
        outputs['Vers'].sv_set(out[0])
        outputs['Edgs'].sv_set(out[1])
        outputs['Pols'].sv_set(out[2])


def register():
    bpy.utils.register_class(SvBoxNode)


def unregister():
    bpy.utils.unregister_class(SvBoxNode)
