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
from sverchok.utils.curve.catmull_rom import SvCatmullRomCurve, SvUniformCatmullRomCurve
from sverchok.utils.curve.primitives import SvPointCurve

class SvCatmullRomSplineNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Catmull-Rom Spline
    Tooltip: Generate Catmull-Rom spline curve through given points
    """
    bl_idname = 'SvCatmullRomSplineNode'
    bl_label = 'Catmull-Rom Spline'
    bl_icon = 'CON_SPLINEIK'
    sv_icon = 'SV_CATMULL_ROM'

    is_cyclic : BoolProperty(name = "Cyclic",
        description = "Whether the spline is cyclic. If checked, the node will generate a cyclic (closed) curve",
        default = False,
        update=updateNode)

    metric: EnumProperty(name='Metric',
        description = "Knot mode",
        default="DISTANCE", items=supported_metrics + xyz_metrics,
        update=updateNode)

    def update_sockets(self, context):
        self.inputs['Tension'].hide_safe = self.spline_mode != 'UNIFORM'
        updateNode(self, context)

    spline_modes = [
        ('NONUNIFORM', "Non-uniform", "Generate non-uniform spline with parametrization defined by some metric", 0),
        ('UNIFORM', "Uniform (with tension)", "Generate a uniform spline, allowing the user to specify tension value", 1)
    ]

    spline_mode : EnumProperty(name = "Spline type",
        description = "Whether to generate a uniform or non-uniform spline",
        items = spline_modes,
        default = 'NONUNIFORM',
        update = update_sockets)

    tension : FloatProperty(name = "Tension",
        description = "Tension value",
        min = 0.0,
        default = 1.0,
        update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, "is_cyclic")
        layout.prop(self, 'spline_mode', text='')
        if self.spline_mode == 'NONUNIFORM':
            layout.prop(self, 'metric')

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvStringsSocket', "Tension").prop_name = 'tension'
        self.outputs.new('SvCurveSocket', "Curve")
        self.update_sockets(context)

    def process(self):
        if not any(o.is_linked for o in self.outputs):
            return

        vertices_s = self.inputs['Vertices'].sv_get( default=[[]])
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
                if len(vertices)>1:
                    if self.spline_mode == 'UNIFORM':
                        tensions = repeat_last_for_length(tensions, len(vertices))
                        curve = SvUniformCatmullRomCurve.build(vertices,
                                    cyclic = self.is_cyclic,
                                    tensions = tensions)
                    else:
                        curve = SvCatmullRomCurve.build(vertices,
                                    metric = self.metric,
                                    cyclic = self.is_cyclic)
                    new_curves.append(curve)
                elif len(vertices)==1:
                    new_curves.append(SvPointCurve(vertices[0]))
                else:
                    raise TypeError(f"Cannot create curve of zero points")

            if nested_out:
                curve_out.append(new_curves)
            else:
                curve_out.extend(new_curves)

        self.outputs['Curve'].sv_set(curve_out)

def register():
    bpy.utils.register_class(SvCatmullRomSplineNode)

def unregister():
    bpy.utils.unregister_class(SvCatmullRomSplineNode)

