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

class SvSteinerEllipseNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Steiner Ellipse
    Tooltip: Generate Steiner circumellipse or inner ellipse for triangular faces
    """
    bl_idname = 'SvSteinerEllipseNode'
    bl_label = 'Steiner Ellipse'
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
        default = 'SKIP',
        update = updateNode)

    modes = [
        ('INNER', "Inellipse", "Generate Steiner inellipse", 0),
        ('CIRCUM', "Circumellipse", "Generate Steiner circumellipse", 1)
    ]

    mode : EnumProperty(
        name = "Mode",
        description = "Which ellipse to generate",
        items = modes,
        default = 'INNER',
        update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'mode', expand=True)

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.label(text="On non-tri faces:")
        layout.prop(self, 'on_non_tri', text='')

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvStringsSocket', "Faces")
        self.outputs.new('SvVerticesSocket', "Center")
        self.outputs.new('SvVerticesSocket', "F1")
        self.outputs.new('SvVerticesSocket', "F2")
        self.outputs.new('SvStringsSocket', "SemiMajorAxis")
        self.outputs.new('SvStringsSocket', "SemiMinorAxis")
        self.outputs.new('SvStringsSocket', "C")
        self.outputs.new('SvStringsSocket', "Eccentricity")
        self.outputs.new('SvVerticesSocket', "Normal")
        self.outputs.new('SvMatrixSocket', "Matrix")
    
    def process(self):
        if not any(output.is_linked for output in self.outputs):
            return

        vertices_s = self.inputs['Vertices'].sv_get()
        faces_s = self.inputs['Faces'].sv_get()

        centers_out = []
        f1_out = []
        f2_out = []
        a_out = []
        b_out = []
        c_out = []
        e_out = []
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
                if self.mode == 'INNER':
                    ellipse = triangle.steiner_inellipse()
                else:
                    ellipse = triangle.steiner_circumellipse()

                centers_out.append(tuple(ellipse.center))
                f1_out.append(tuple(ellipse.f1))
                f2_out.append(tuple(ellipse.f2))
                a_out.append(ellipse.a)
                b_out.append(ellipse.b)
                c_out.append(ellipse.c)
                e_out.append(ellipse.eccentricity)
                normal_out.append(ellipse.normal())
                matrix_out.append(ellipse.get_matrix())

        self.outputs['Center'].sv_set([centers_out])
        self.outputs['F1'].sv_set([f1_out])
        self.outputs['F2'].sv_set([f2_out])
        self.outputs['SemiMajorAxis'].sv_set([a_out])
        self.outputs['SemiMinorAxis'].sv_set([b_out])
        self.outputs['C'].sv_set([c_out])
        self.outputs['Eccentricity'].sv_set([e_out])
        self.outputs['Normal'].sv_set([normal_out])
        self.outputs['Matrix'].sv_set(matrix_out)

def register():
    bpy.utils.register_class(SvSteinerEllipseNode)

def unregister():
    bpy.utils.unregister_class(SvSteinerEllipseNode)

