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

import math

import numpy as np
from numpy.linalg import norm as np_margnitude
import bpy

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat, has_element
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata, pydata_from_bmesh
from sverchok.utils.math import np_normalize_vectors
from sverchok.utils.nodes_mixins.recursive_nodes import SvRecursiveNode
from sverchok.utils.modules.polygon_utils import np_faces_normals
from sverchok.utils.sv_mesh_utils import calc_mesh_normals_bmesh, calc_mesh_normals_np

class SvGetNormalsNodeMk2(bpy.types.Node, SverchCustomTreeNode, SvRecursiveNode):
    '''
    Triggers: Face & Vertex Normals
    Tooltip: Calculate normals of faces and vertices
    '''
    bl_idname = 'SvGetNormalsNodeMk2'
    bl_label = 'Calculate normals'
    bl_icon = 'SNAP_NORMAL'

    implementation_items = [
        ('BMESH', 'Bmesh', 'Slower', 0),
        ('MWE', 'Mean Weighted Equally', 'Faster', 1),
        ('MWA', 'Mean Weighted by Angle','',2),
        ('MWS', 'Mean Weighted by Sine','',3),
        ('MWSELR', 'Mean Weighted by Sine/Edge Length','',4),
        ('MWAT', 'Mean Weighted Area','',5),
        ('MWAAT', 'Mean Weighted Angle*Area','',6),
        ('MWSAT', 'Mean Weighted Sine*Area', '', 7),
        ('MWEL', 'Mean Weighted Edge Length' , '', 8),
        ('MWELR','Mean Weighted 1/Edge Length', '', 9),
        ('MWRELR', 'Mean Weighted 1/sqrt(Edge Length)', '',10)]

    implementation: bpy.props.EnumProperty(
        name='Implementation',
        items=implementation_items,
        default='MWE',
        update=updateNode)
    planar_faces: bpy.props.BoolProperty(
        name='Planar Faces',
        description='Check if all the incoming faces are tris or flat (makes node faster)',
        default=False,
        update=updateNode)
    output_numpy: bpy.props.BoolProperty(
        name='Output NumPy',
        description='output NumPy arrays (makes node faster)',
        default=False,
        update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices").is_mandatory=True
        self.inputs.new('SvStringsSocket', "Polygons").nesting_level =3

        self.outputs.new('SvVerticesSocket', "Face Normals")
        self.outputs.new('SvVerticesSocket', "Vertex Normals")

    def draw_buttons(self, context, layout):
        layout.prop(self, 'implementation')

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, 'list_match')
        layout.prop(self, 'implementation')
        layout.prop(self, 'planar_faces')
        layout.prop(self, 'output_numpy')

    def rclick_menu(self, context, layout):
        layout.prop_menu_enum(self, "list_match", text="List Match")

    def process_data(self, params):
        vertices, faces = params
        get_f_normals = self.outputs['Face Normals'].is_linked
        get_v_normals = self.outputs['Vertex Normals'].is_linked
        verts_normal, faces_normal = [], []
        for v, p in zip(vertices, faces):
            if self.implementation == 'BMESH':
                f_nor, v_nor = calc_mesh_normals_bmesh(v, p,
                                                 get_f_normals=get_f_normals,
                                                 get_v_normals=get_v_normals)
            else:
                f_nor, v_nor = calc_mesh_normals_np(v, p,
                                               get_f_normals=get_f_normals,
                                               get_v_normals=get_v_normals,
                                               non_planar=not self.planar_faces,
                                               v_normal_alg=self.implementation,
                                               output_numpy=self.output_numpy)
            verts_normal.append(v_nor)
            faces_normal.append(f_nor)
        return faces_normal, verts_normal

def register():
    bpy.utils.register_class(SvGetNormalsNodeMk2)


def unregister():
    bpy.utils.unregister_class(SvGetNormalsNodeMk2)
