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
import numpy as np
from bpy.props import EnumProperty
from mathutils import Vector

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat
from sverchok.utils.geom import Triangle
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata

class SvInscribedCircleNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Inscribed Circle
    Tooltip: Generate inscribed circles for triangular faces
    """
    bl_idname = 'SvInscribedCircleNode'
    bl_label = 'Inscribed Circle'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_INSCRIBED_CIRCLE'

    error_modes = [
        ('SKIP', "Skip", "Skip non-triangular faces - do not generate output for them", 0),
        ('ERROR', "Error", "Generate an error if encounter non-triangular face", 1)
    ]

    on_non_tri : EnumProperty(
        name = "On non-tri face",
        description = "What to do if encounter a non-triangular face",
        items = error_modes,
        update = updateNode)

    def draw_buttons_ext(self, context, layout):
        layout.label(text="On non-tri faces:")
        layout.prop(self, 'on_non_tri', text='')

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvStringsSocket', "Faces")
        self.outputs.new('SvVerticesSocket', "Center")
        self.outputs.new('SvStringsSocket', "Radius")
        self.outputs.new('SvVerticesSocket', "Normal")
        self.outputs.new('SvMatrixSocket', "Matrix")

    def process(self):
        if not any(output.is_linked for output in self.outputs):
            return

        vertices_s = self.inputs['Vertices'].sv_get()
        faces_s = self.inputs['Faces'].sv_get()

        centers_out = []
        radius_out = []
        normal_out = []
        matrix_out = []
        for vertices, faces in zip_long_repeat(vertices_s, faces_s):
            bm = bmesh_from_pydata(vertices, [], faces)
            for face in bm.faces:
                if len(face.verts) != 3:
                    if self.on_non_tri == 'SKIP':
                        continue
                    else:
                        raise Exception("Non-triangular face #%s encountered!" % face.index)
                v1, v2, v3 = [v.co for v in face.verts]
                triangle = Triangle(v1, v2, v3)
                circle = triangle.inscribed_circle()
                centers_out.append(circle.center.tolist())
                radius_out.append(circle.radius)
                normal_out.append(circle.normal.tolist())
                matrix_out.append(circle.get_matrix())

        self.outputs['Center'].sv_set([centers_out])
        self.outputs['Radius'].sv_set([radius_out])
        self.outputs['Normal'].sv_set([normal_out])
        self.outputs['Matrix'].sv_set(matrix_out)

def register():
    bpy.utils.register_class(SvInscribedCircleNode)

def unregister():
    bpy.utils.unregister_class(SvInscribedCircleNode)

