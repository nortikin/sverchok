# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from bpy.props import EnumProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import ensure_nesting_level, get_data_nesting_level, updateNode, zip_long_repeat
from sverchok.utils.curve.splines import SvMonotoneSpline

class SvMonotoneSplineNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Monotone Spline
    Tooltip: Generate monotone interpolation curve
    """
    bl_idname = 'SvMonotoneSplineNode'
    bl_label = 'Monotone Spline'
    bl_icon = 'CON_SPLINEIK'
    sv_dependencies = {'scipy'}

    planes = [
        ('XY', "XY", "XY plane", 0),
        ('XZ', "XZ", "XZ plane", 1),
        ('YZ', "YZ", "YZ plane", 2)
    ]

    def update_sockets(self, context):
        if self.plane == 'XY':
            x_label, y_label = "X", "Y"
        elif self.plane == 'XZ':
            x_label, y_label = "X", "Z"
        else: # YZ
            x_label, y_label = "Y", "Z"
        self.inputs['X'].label = x_label
        self.inputs['Y'].label = y_label
        updateNode(self, context)

    plane : EnumProperty(
        name = "Plane",
        description = "Coordinate plane",
        items = planes,
        default = 'XY',
        update = update_sockets)

    def draw_buttons(self, context, layout):
        layout.prop(self, "plane", expand=True)

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "X")
        self.inputs.new('SvStringsSocket', "Y")
        self.outputs.new('SvCurveSocket', "Curve")

    def process(self):
        if not any(o.is_linked for o in self.outputs):
            return

        xs_s = self.inputs['X'].sv_get()
        ys_s = self.inputs['Y'].sv_get()
        input_level = get_data_nesting_level(xs_s)
        flat_output = input_level < 3
        xs_s = ensure_nesting_level(xs_s, 3)
        ys_s = ensure_nesting_level(ys_s, 3)

        if self.plane == 'XY':
            x_axis = 0
            y_axis = 1
        elif self.plane == 'XZ':
            x_axis = 0
            y_axis = 2
        else: # YZ
            x_axis = 1
            y_axis = 2

        curve_out = []
        for params in zip_long_repeat(xs_s, ys_s):
            new_curves = []
            for xs, ys in zip_long_repeat(*params):
                curve = SvMonotoneSpline(xs, ys,
                                         x_axis = x_axis,
                                         y_axis = y_axis)
                new_curves.append(curve)
            if flat_output:
                curve_out.extend(new_curves)
            else:
                curve_out.append(new_curves)

        self.outputs['Curve'].sv_set(curve_out)

def register():
    bpy.utils.register_class(SvMonotoneSplineNode)

def unregister():
    bpy.utils.unregister_class(SvMonotoneSplineNode)

