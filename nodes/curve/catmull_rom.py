# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, get_data_nesting_level, ensure_nesting_level, repeat_last_for_length
from sverchok.utils.math import supported_metrics, xyz_metrics
from sverchok.utils.curve.catmull_rom import SvCatmullRomCurve, uniform_catmull_rom_interpolate

class SvCatmullRomSplineNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Catmull-Rom Spline
    Tooltip: Generate Catmull-Rom spline curve through given points
    """
    bl_idname = 'SvCatmullRomSplineNode'
    bl_label = 'Catmull-Rom Spline'
    bl_icon = 'CON_SPLINEIK'

    is_cyclic : BoolProperty(name = "Cyclic",
        description = "Whether the spline is cyclic. If checked, the node will generate a cyclic (closed) curve",
        default = False,
        update=updateNode)

    metric: EnumProperty(name='Metric',
        description = "Knot mode",
        default="DISTANCE", items=supported_metrics + xyz_metrics,
        update=updateNode)

    def update_sockets(self, context):
        self.inputs['Tension'].hide_safe = not self.use_tension
        updateNode(self, context)

    use_tension : BoolProperty(name = "Specify tension",
        description = "If checked, the node will generate uniform Catmull-Rom spline, but will allow you to specify tension",
        default = False,
        update = update_sockets)

    tension : FloatProperty(name = "Tension",
        description = "Tension value",
        min = 0.0,
        default = 1.0,
        update = updateNode)

    concatenate : BoolProperty(name = "Concatenate",
        description = "Generate a single concatenated curve. If not checked, generate a separate Bezier spline for each segment",
        default = True,
        update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, "is_cyclic")
        layout.prop(self, 'use_tension')
        if self.use_tension:
            layout.prop(self, 'concatenate')
        else:
            layout.prop(self, 'metric')

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvStringsSocket', "Tension").prop_name = 'tension'
        self.outputs.new('SvCurveSocket', "Curve")
        self.update_sockets(context)

    def process(self):
        if not any(o.is_linked for o in self.outputs):
            return

        vertices_s = self.inputs['Vertices'].sv_get()
        tension_s = self.inputs['Tension'].sv_get()
        in_level = get_data_nesting_level(vertices_s)
        if in_level < 2 or in_level > 4:
            raise TypeError(f"Required nesting level is 2 to 4, provided data nesting level is {in_level}")
        nested_out = in_level > 3

        vertices_s = ensure_nesting_level(vertices_s, 4) # will produce a list of lists of curves
        tension_s = ensure_nesting_level(tension_s, 3) # a list of values for each curve
        
        curve_out = []
        for params in zip_long_repeat(vertices_s, tension_s):
            new_curves = []
            for vertices, tensions in zip_long_repeat(*params):
                if self.use_tension:
                    tensions = repeat_last_for_length(tensions, len(vertices))
                    curve = uniform_catmull_rom_interpolate(vertices,
                                concatenate = self.concatenate,
                                cyclic = self.is_cyclic,
                                tension = tensions)
                else:
                    curve = SvCatmullRomCurve.build(vertices,
                                metric = self.metric,
                                cyclic = self.is_cyclic)
                new_curves.append(curve)
            if nested_out:
                curve_out.append(new_curves)
            else:
                curve_out.extend(new_curves)

        self.outputs['Curve'].sv_set(curve_out)

def register():
    bpy.utils.register_class(SvCatmullRomSplineNode)

def unregister():
    bpy.utils.unregister_class(SvCatmullRomSplineNode)

