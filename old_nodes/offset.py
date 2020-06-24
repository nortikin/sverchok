
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.curve import SvCurve, SvOffsetCurve
from sverchok.utils.math import ZERO, FRENET, HOUSEHOLDER, TRACK, DIFF, TRACK_NORMAL

class SvOffsetCurveNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Offset Curve
    Tooltip: Offset a Curve along it's normal, binormal or custom vector
    """
    bl_idname = 'SvOffsetCurveNode'
    bl_label = 'Offset Curve'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_CURVE_OFFSET'

    replacement_nodes = [('SvOffsetCurveMk2Node', None, None)]

    modes = [
            ('X', "X (Normal)", "Offset along curve frame's X axis - curve normal in case of Frenet frame", 0),
            ('Y', "Y (Binormal)", "Offset along curve frame's Y axis - curve binormal in case of Frenet frame", 1),
            ('C', "Custom (N / B / T)", "Offset along custom vector in curve frame coordinates - normal, binormal, tangent", 2)
        ]

    algorithms = [
        (FRENET, "Frenet", "Frenet / native rotation", 0),
        (ZERO, "Zero-twist", "Zero-twist rotation", 1),
        (HOUSEHOLDER, "Householder", "Use Householder reflection matrix", 2),
        (TRACK, "Tracking", "Use quaternion-based tracking", 3),
        (DIFF, "Rotation difference", "Use rotational difference calculation", 4),
        (TRACK_NORMAL, "Track normal", "Try to maintain constant normal direction by tracking along curve", 5)
    ]

    @throttled
    def update_sockets(self, context):
        self.inputs['Offset'].hide_safe = self.mode == 'C'
        self.inputs['Vector'].hide_safe = self.mode != 'C'
        self.inputs['Resolution'].hide_safe = self.algorithm not in {ZERO, TRACK_NORMAL}

    mode : EnumProperty(
            name = "Direction",
            items = modes,
            default = 'X',
            update = update_sockets)

    algorithm : EnumProperty(
            name = "Algorithm",
            items = algorithms,
            default = HOUSEHOLDER,
            update = update_sockets)

    resolution : IntProperty(
        name = "Resolution",
        min = 10, default = 50,
        update = updateNode)

    offset : FloatProperty(
            name = "Offset",
            default = 0.1,
            update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, "mode")
        layout.prop(self, "algorithm")

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', "Curve")
        self.inputs.new('SvStringsSocket', "Offset").prop_name = 'offset'
        p = self.inputs.new('SvVerticesSocket', "Vector")
        p.use_prop = True
        p.prop = (0.1, 0.0, 0.0)
        self.inputs.new('SvStringsSocket', "Resolution").prop_name = 'resolution'
        self.outputs.new('SvCurveSocket', "Curve")
        self.update_sockets(context)

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        curve_s = self.inputs['Curve'].sv_get()
        offset_s = self.inputs['Offset'].sv_get()
        vector_s = self.inputs['Vector'].sv_get()
        resolution_s = self.inputs['Resolution'].sv_get()

        curve_s = ensure_nesting_level(curve_s, 2, data_types=(SvCurve,))
        offset_s = ensure_nesting_level(offset_s, 2)
        vector_s = ensure_nesting_level(vector_s, 3)
        resolution_s = ensure_nesting_level(resolution_s, 2)

        curve_out = []
        for curves, offsets, vectors, resolutions in zip_long_repeat(curve_s, offset_s, vector_s, resolution_s):
            new_curves = []
            for curve, offset, vector, resolution in zip_long_repeat(curves, offsets, vectors, resolutions):
                if self.mode == 'X':
                    vector = [offset, 0, 0]
                elif self.mode == 'Y':
                    vector = [0, offset, 0]
                vector = np.array(vector)

                new_curve = SvOffsetCurve(curve, vector, algorithm=self.algorithm, resolution=resolution)
                new_curves.append(new_curve)
            curve_out.append(new_curves)

        self.outputs['Curve'].sv_set(curve_out)

def register():
    bpy.utils.register_class(SvOffsetCurveNode)

def unregister():
    bpy.utils.unregister_class(SvOffsetCurveNode)

