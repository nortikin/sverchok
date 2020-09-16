# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.curve.freecad import make_helix
from sverchok.utils.dummy_nodes import add_dummy
from sverchok.dependencies import FreeCAD

if FreeCAD is None:
    add_dummy('SvFreeCadHelixNode', 'Helix (FreeCAD)', 'FreeCAD')
else:
    import Part
    from FreeCAD import Base

class SvFreeCadHelixNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Helix
    Tooltip: Generate a helix curve (as a NURBS)
    """
    bl_idname = 'SvFreeCadHelixNode'
    bl_label = 'Helix (FreeCAD)'
    bl_icon = 'MOD_SCREW'

    radius : FloatProperty(
        name = "Radius",
        default = 1.0,
        update = updateNode)

    height : FloatProperty(
        name = "Height",
        default = 4.0,
        update = updateNode)

    pitch : FloatProperty(
        name = "Pitch",
        description = "Helix step along it's axis for each full rotation",
        default = 1.0,
        update = updateNode)

    angle : FloatProperty(
        name = "Angle",
        description = "Apex angle for conic helixes, in degrees; 0 for cylindrical helixes",
        default = 0,
        min = 0,
        update = updateNode)

    join : BoolProperty(
        name = "Join",
        description = "If checked, output a single flat list of curves; otherwise, output a separate list of curves for each set of input parameters",
        default = False,
        update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'join', toggle=True)

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "Radius").prop_name = 'radius'
        self.inputs.new('SvStringsSocket', "Height").prop_name = 'height'
        self.inputs.new('SvStringsSocket', "Pitch").prop_name = 'pitch'
        self.inputs.new('SvStringsSocket', "Angle").prop_name = 'angle'
        self.outputs.new('SvCurveSocket', "Curve")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        radius_s = self.inputs['Radius'].sv_get()
        height_s = self.inputs['Height'].sv_get()
        pitch_s = self.inputs['Pitch'].sv_get()
        angle_s = self.inputs['Angle'].sv_get()
        
        curve_out = []
        for radiuses, heights, pitches, angles in zip_long_repeat(radius_s, height_s, pitch_s, angle_s):
            new_curves = []
            for radius, height, pitch, angle in zip_long_repeat(radiuses, heights, pitches, angles):
                curve = make_helix(pitch, height, radius, angle)
                new_curves.append(curve)
            if self.join:
                curve_out.extend(new_curves)
            else:
                curve_out.append(new_curves)

        self.outputs['Curve'].sv_set(curve_out)

def register():
    if FreeCAD is not None:
        bpy.utils.register_class(SvFreeCadHelixNode)

def unregister():
    if FreeCAD is not None:
        bpy.utils.unregister_class(SvFreeCadHelixNode)

