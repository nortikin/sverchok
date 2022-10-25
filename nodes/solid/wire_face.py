# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

import bpy
from bpy.props import BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import ensure_nesting_level, updateNode
from sverchok.utils.curve.core import SvCurve
from sverchok.utils.curve.primitives import SvLine
from sverchok.utils.surface.freecad import curves_to_face


class SvSolidWireFaceNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Solid Face Wire Curve
    Tooltip: Make a Face of a Solid from it's boundary edges (wire) defined by one or several Curves
    """
    bl_idname = 'SvSolidWireFaceNode'
    bl_label = "Face from Curves (Solid)"
    bl_icon = 'EDGESEL'
    sv_icon = 'SV_CURVES_FACE'
    sv_category = "Solid Inputs"
    sv_dependencies = {'FreeCAD'}

    planar : BoolProperty(
            name = "Planar",
            description = "Make a planar (flat) face; all curves must lie exactly in one plane in this case",
            default = True,
            update = updateNode)

    close_wire : BoolProperty(
            name = "Close wire",
            description = "Add a linear segment to make the wire closed",
            default = False,
            update = updateNode)

    accuracy : IntProperty(
            name = "Accuracy",
            description = "Tolerance parameter for checking if ends of edges coincide",
            default = 8,
            min = 1,
            update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'planar')
        layout.prop(self, 'close_wire')

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, 'accuracy')

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', "Edges")
        self.outputs.new('SvSurfaceSocket', "SolidFace")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        tolerance = 10 ** (-self.accuracy)

        curve_s = self.inputs['Edges'].sv_get()
        #input_level = get_data_nesting_level(curve_s, data_types=(SvCurve,))
        curve_s = ensure_nesting_level(curve_s, 3, data_types=(SvCurve,))

        faces_out = []
        for curves_i in curve_s:
            new_faces = []
            for curves in curves_i:
                if self.close_wire:
                    t1 = curves[0].get_u_bounds()[0]
                    t2 = curves[-1].get_u_bounds()[-1]
                    p1 = curves[0].evaluate(t1)
                    p2 = curves[-1].evaluate(t2)
                    if np.linalg.norm(p1 - p2) > tolerance:
                        line = SvLine.from_two_points(p2, p1)
                        curves = curves + [line]
                face = curves_to_face(curves, planar=self.planar, force_nurbs=False, tolerance=tolerance)
                new_faces.append(face)
            faces_out.append(new_faces)

        self.outputs['SolidFace'].sv_set(faces_out)


def register():
    bpy.utils.register_class(SvSolidWireFaceNode)


def unregister():
    bpy.utils.unregister_class(SvSolidWireFaceNode)
