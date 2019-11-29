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
from bpy.props import IntProperty, EnumProperty, BoolProperty, FloatProperty
from bmesh.ops import dissolve_limit

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat, fullList
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata, pydata_from_bmesh


class SvLimitedDissolve(bpy.types.Node, SverchCustomTreeNode):
    ''' Limited Dissolve '''
    bl_idname = 'SvLimitedDissolve'
    bl_label = 'Limited Dissolve'
    bl_icon = 'MOD_DECIM'

    angle: FloatProperty(default=5.0, min=0.0, update=updateNode)
    use_dissolve_boundaries: BoolProperty(update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Verts')
        self.inputs.new('SvStringsSocket', 'Edges')
        self.inputs.new('SvStringsSocket', 'Polys')

        self.outputs.new('SvVerticesSocket', 'Verts')
        self.outputs.new('SvStringsSocket', 'Edges')
        self.outputs.new('SvStringsSocket', 'Polys')

    def draw_buttons(self, context, layout):
        layout.prop(self, "angle")
        layout.prop(self, "use_dissolve_boundaries")

    def process(self):
        if not self.outputs['Verts'].is_linked:
            return

        verts = self.inputs['Verts'].sv_get()
        edges = self.inputs['Edges'].sv_get(default=[[]])
        faces = self.inputs['Polys'].sv_get(default=[[]])
        meshes = match_long_repeat([verts, edges, faces])

        r_verts = []
        r_edges = []
        r_faces = []

        for verts, edges, faces in zip(*meshes):
            bm = bmesh_from_pydata(verts, edges, faces, normal_update=True)
            ret = dissolve_limit(
                bm, angle_limit=self.angle,
                use_dissolve_boundaries=self.use_dissolve_boundaries,
                verts=bm.verts, edges=bm.edges)
            new_verts, new_edges, new_faces = pydata_from_bmesh(bm)
            bm.free()

            r_verts.append(new_verts)
            r_edges.append(new_edges)
            r_faces.append(new_faces)

        self.outputs['Verts'].sv_set(r_verts)
        self.outputs['Edges'].sv_set(r_edges)
        self.outputs['Polys'].sv_set(r_faces)


def register():
    bpy.utils.register_class(SvLimitedDissolve)


def unregister():
    bpy.utils.unregister_class(SvLimitedDissolve)
