# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

import bpy

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import zip_long_repeat, ensure_nesting_level, get_data_nesting_level, updateNode
from sverchok.utils.curve.core import SvCurve
from sverchok.utils.surface.freecad import curves_to_face
from sverchok.utils.dummy_nodes import add_dummy

from sverchok.dependencies import FreeCAD

if FreeCAD is None:
    add_dummy('SvSolidWireFaceNode', 'Extrude Face (Solid)', 'FreeCAD')
else:
    import Part
    from FreeCAD import Base

class SvSolidWireFaceNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Solid Face Wire
    Tooltip: Make a Face of a Solid from it's boundary edges (wire) defined by one or several Curves
    """
    bl_idname = 'SvSolidWireFaceNode'
    bl_label = "Face from Curves (Solid)"
    bl_icon = 'EDGESEL'
    sv_icon = 'SV_CURVES_FACE'
    solid_catergory = "Inputs"

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', "Edges")
        self.outputs.new('SvSurfaceSocket', "SolidFace")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        curve_s = self.inputs['Edges'].sv_get()
        #input_level = get_data_nesting_level(curve_s, data_types=(SvCurve,))
        curve_s = ensure_nesting_level(curve_s, 3, data_types=(SvCurve,))

        faces_out = []
        for curves_i in curve_s:
            new_faces = []
            for curves in curves_i:
                _, _, face = curves_to_face(curves)
                new_faces.append(face)
            faces_out.append(new_faces)

        self.outputs['SolidFace'].sv_set(faces_out)

def register():
    if FreeCAD is not None:
        bpy.utils.register_class(SvSolidWireFaceNode)

def unregister():
    if FreeCAD is not None:
        bpy.utils.unregister_class(SvSolidWireFaceNode)

