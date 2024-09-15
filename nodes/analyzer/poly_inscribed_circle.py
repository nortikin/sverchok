# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
import bpy
from bpy.props import BoolProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.inscribed_circle import calc_inscribed_circle, ERROR, RETURN_NONE, ASIS
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level

class SvSemiInscribedCircleNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Polygon Inscribed Circle
    Tooltip: Inscribed circle for an arbitrary convex polygon
    """
    bl_idname = 'SvSemiInscribedCircleNode'
    bl_label = 'Polygon Inscribed Circle'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_POLY_INSCRIBED_CIRCLE'
    sv_dependencies = {'scipy'}

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvStringsSocket', "Faces")
        self.outputs.new('SvMatrixSocket', "Center")
        self.outputs.new('SvStringsSocket', "Radius")

    flat_output : BoolProperty(
            name = "Flat Matrix output",
            description = "Output single flat list of matrices",
            default = True,
            update = updateNode)

    concave_modes = [
            (RETURN_NONE, "Skip", "Skip concave faces - do not generate output for them", 0),
            (ERROR, "Error", "Generate an error if encounter a concave face", 1),
            (ASIS, "As Is", "Try to calculate inscribed circle anyway (it probably will be incorrect)", 2)
        ]

    on_concave : EnumProperty(
            name = "On concave face",
            description = "What to do if encounter a concave face",
            default = RETURN_NONE,
            items = concave_modes,
            update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'flat_output')

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.label(text = "On concave faces:")
        layout.prop(self, 'on_concave', text='')

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        vertices_s = self.inputs['Vertices'].sv_get()
        vertices_s = ensure_nesting_level(vertices_s, 4)
        faces_s = self.inputs['Faces'].sv_get()
        faces_s = ensure_nesting_level(faces_s, 4)

        matrix_out = []
        radius_out = []
        for params in zip_long_repeat(vertices_s, faces_s):
            new_matrix = []
            new_radius = []
            for vertices, faces in zip_long_repeat(*params):
                vertices = np.array(vertices)
                for face in faces:
                    face = np.array(face)
                    circle = calc_inscribed_circle(vertices[face],
                                    on_concave = self.on_concave)
                    if circle is not None:
                        new_matrix.append(circle.get_matrix())
                        new_radius.append(circle.radius)
            if self.flat_output:
                matrix_out.extend(new_matrix)
            else:
                matrix_out.append(new_matrix)
            radius_out.append(new_radius)

        self.outputs['Center'].sv_set(matrix_out)
        self.outputs['Radius'].sv_set(radius_out)

def register():
    bpy.utils.register_class(SvSemiInscribedCircleNode)

def unregister():
    bpy.utils.unregister_class(SvSemiInscribedCircleNode)

