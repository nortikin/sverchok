
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.curve import SvExLine

class SvExLineCurveNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Line Segment
    Tooltip: Generate straight line curve object
    """
    bl_idname = 'SvExLineCurveNode'
    bl_label = 'Line (Curve)'
    bl_icon = 'GRIP'
    sv_icon = 'SV_LINE'

    modes = [
        ('DIR', "Point and direction", "Point and direction", 0),
        ('AB', "Two points", "Two points", 1)
    ]

    @throttled
    def update_sockets(self, context):
        self.inputs['Point2'].hide_safe = self.mode != 'AB'
        self.inputs['Direction'].hide_safe = self.mode != 'DIR'

    mode : EnumProperty(
        name = "Mode",
        items = modes,
        default = 'DIR',
        update = update_sockets)

    u_min : FloatProperty(
        name = "U Min",
        default = 0.0,
        update = updateNode)


    u_max : FloatProperty(
        name = "U Max",
        default = 1.0,
        update = updateNode)

    def sv_init(self, context):
        p = self.inputs.new('SvVerticesSocket', "Point1")
        p.use_prop = True
        p.prop = (0.0, 0.0, 0.0)
        p = self.inputs.new('SvVerticesSocket', "Point2")
        p.use_prop = True
        p.prop = (1.0, 0.0, 0.0)
        p = self.inputs.new('SvVerticesSocket', "Direction")
        p.use_prop = True
        p.prop = (1.0, 0.0, 0.0)
        self.inputs.new('SvStringsSocket', "UMin").prop_name = 'u_min'
        self.inputs.new('SvStringsSocket', "UMax").prop_name = 'u_max'
        self.outputs.new('SvExCurveSocket', "Curve")
        self.update_sockets(context)

    def draw_buttons(self, context, layout):
        layout.prop(self, "mode", text="")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        point1_s = self.inputs['Point1'].sv_get()
        point2_s = self.inputs['Point2'].sv_get()
        direction_s = self.inputs['Direction'].sv_get()
        u_min_s = self.inputs['UMin'].sv_get()
        u_max_s = self.inputs['UMax'].sv_get()

        point1_s = ensure_nesting_level(point1_s, 3)
        point2_s = ensure_nesting_level(point2_s, 3)
        direction_s = ensure_nesting_level(direction_s, 3)
        u_min_s = ensure_nesting_level(u_min_s, 2)
        u_max_s = ensure_nesting_level(u_max_s, 2)

        curves_out = []
        for point1s, point2s, directions, u_mins, u_maxs in zip_long_repeat(point1_s, point2_s, direction_s, u_min_s, u_max_s):
            for point1, point2, direction, u_min, u_max in zip_long_repeat(point1s, point2s, directions, u_mins, u_maxs):
                point1 = np.array(point1)
                if self.mode == 'AB':
                    direction = np.array(point2) - point1

                line = SvExLine(point1, direction)
                line.u_bounds = (u_min, u_max)
                curves_out.append(line)

        self.outputs['Curve'].sv_set(curves_out)

def register():
    bpy.utils.register_class(SvExLineCurveNode)

def unregister():
    bpy.utils.unregister_class(SvExLineCurveNode)

