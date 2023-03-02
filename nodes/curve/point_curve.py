# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, get_data_nesting_level, ensure_nesting_level
from sverchok.utils.curve.primitives import SvPointCurve

class SvPointCurveNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Single-Point Curve
    Tooltip: Generate a Curve object consisting of a single point
    """
    bl_idname = 'SvPointCurveNode'
    bl_label = 'Single-Point Curve'
    bl_icon = 'DOT'
    
    def sv_init(self, context):
        p = self.inputs.new('SvVerticesSocket', "Point")
        p.use_prop = True
        p.default_property = (0.0, 0.0, 0.0)
        self.outputs.new('SvCurveSocket', 'Curve')

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return 

        points_s = self.inputs['Point'].sv_get()
        input_level = get_data_nesting_level(points_s)
        nested_output = input_level > 2
        points_s = ensure_nesting_level(points_s, 3)

        curves_out = []
        for points in points_s:
            new_curves = []
            for point in points:
                curve = SvPointCurve(point)
                new_curves.append(curve)
            if nested_output:
                curves_out.append(new_curves)
            else:
                curves_out.extend(new_curves)
        self.outputs['Curve'].sv_set(curves_out)

def register():
    bpy.utils.register_class(SvPointCurveNode)

def unregister():
    bpy.utils.unregister_class(SvPointCurveNode)

