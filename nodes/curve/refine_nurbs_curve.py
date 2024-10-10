# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode, zip_long_repeat, ensure_nesting_level,
                                     get_data_nesting_level)
from sverchok.utils.curve import SvCurve
from sverchok.utils.curve.nurbs import SvNurbsCurve
from sverchok.utils.curve.nurbs_algorithms import refine_curve, REFINE_TRIVIAL, REFINE_DISTRIBUTE, REFINE_BISECT
from sverchok.utils.curve.algorithms import SvCurveLengthSolver

class SvRefineNurbsCurveNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Refine NURBS curve
    Tooltip: Add more control points to a NURBS curve
    """
    bl_idname = 'SvRefineNurbsCurveNode'
    bl_label = 'Refine NURBS Curve'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_SPLIT_CURVE'

    def update_sockets(self, context):
        self.inputs['Resolution'].hide_safe = self.distribution not in ['DISTRIBUTE_L', 'BISECT_L']
        self.inputs['TMin'].hide_safe = not self.specify_segment
        self.inputs['TMax'].hide_safe = not self.specify_segment
        updateNode(self, context)

    distributions = [
            ('EVEN_T', "Even T", "Insert knots evenly distributed in curve's parameter space", 0),
            ('DISTRIBUTE_T', "Distribute T", "Add more knots in segments of curve's parameter space where there knots are less dense", 1),
            ('DISTRIBUTE_L', "Distribute Length", "Add more knots in segments of curve's parameter space which correspond to segments of curve with greater length", 2),
            ('BISECT_T', "Bisect T", "Recursive bisection algorithm following curve parameter", 3),
            ('BISECT_L', "Bisect Length", "Recursive bisection algorithm following curve length", 4)
        ]

    distribution : EnumProperty(
            name = "Distribution",
            description = "How to decide where to place new knots",
            items = distributions,
            default = 'EVEN_T',
            update = update_sockets)

    max_modes = [
            ('ONE', "Once", "Insert each knot value only one time", 0),
            ('MAX', "As possible", "Insert each knot value as many times as it is possible", 1)
        ]

    max_mode : EnumProperty(
            name = "Insert each knot",
            description = "How many times to insert each new knot value",
            items = max_modes,
            default = 'MAX',
            update = updateNode)

    add_knots : IntProperty(
            name = "New Knots",
            description = "Number of knots to be inserted",
            default = 10,
            min = 0,
            update = updateNode)

    specify_segment : BoolProperty(
            name = "Specify Segment",
            description = "Provide segment of curve's T parameter space, which is to be refined",
            default = False,
            update = update_sockets)

    join : BoolProperty(
            name = "Join",
            description = "Output single list of curves for all provided curves",
            default = False,
            update = updateNode)

    resolution : IntProperty(
            name = 'Resolution',
            min = 1,
            default = 50,
            update = updateNode)

    t_min : FloatProperty(
            name = "T Min",
            default = 0.0,
            update = updateNode)

    t_max : FloatProperty(
            name = "T Max",
            default = 1.0,
            update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'distribution')
        layout.prop(self, 'max_mode')
        layout.prop(self, 'specify_segment')
        #layout.prop(self, 'join')

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', "Curve")
        self.inputs.new('SvStringsSocket', "NewKnots").prop_name = 'add_knots'
        self.inputs.new('SvStringsSocket', "Resolution").prop_name = 'resolution'
        self.inputs.new('SvStringsSocket', "TMin").prop_name = 't_min'
        self.inputs.new('SvStringsSocket', "TMax").prop_name = 't_max'
        self.outputs.new('SvCurveSocket', 'Curve')
        self.outputs.new('SvStringsSocket', 'NewKnots')
        self.update_sockets(context)

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        curve_s = self.inputs['Curve'].sv_get()
        new_knots_s = self.inputs['NewKnots'].sv_get()
        resolution_s = self.inputs['Resolution'].sv_get()
        t_min_s = self.inputs['TMin'].sv_get()
        t_max_s = self.inputs['TMax'].sv_get()

        curves_level = get_data_nesting_level(curve_s, data_types=(SvCurve,))
        curve_s = ensure_nesting_level(curve_s, 2, data_types=(SvCurve,))
        new_knots_s = ensure_nesting_level(new_knots_s, 2)
        resolution_s = ensure_nesting_level(resolution_s, 2)
        t_min_s = ensure_nesting_level(t_min_s, 2)
        t_max_s = ensure_nesting_level(t_max_s, 2)

        curves_out = []
        new_knots_out = []
        for params in zip_long_repeat(curve_s, new_knots_s, resolution_s, t_min_s, t_max_s):
            curves_list = []
            new_knots_list = []
            for curve, new_knots, resolution, t_min, t_max in zip_long_repeat(*params):
                curve = SvNurbsCurve.to_nurbs(curve)
                if curve is None:
                    raise Exception("Curve is not NURBS")
                if not self.specify_segment:
                    t_min = t_max = None

                if self.distribution == 'DISTRIBUTE_L':
                    solver = SvCurveLengthSolver(curve)
                    solver.prepare('SPL', resolution)
                    algorithm = REFINE_DISTRIBUTE
                elif self.distribution == 'DISTRIBUTE_T':
                    solver = None
                    algorithm = REFINE_DISTRIBUTE
                elif self.distribution == 'BISECT_L':
                    solver = SvCurveLengthSolver(curve)
                    solver.prepare('SPL', resolution)
                    algorithm = REFINE_BISECT
                elif self.distribution == 'BISECT_T':
                    solver = None
                    algorithm = REFINE_BISECT
                else:
                    solver = None
                    algorithm = REFINE_TRIVIAL

                new_knots, new_curve = refine_curve(curve, new_knots,
                                algorithm = algorithm,
                                t_min = t_min, t_max = t_max,
                                refine_max = self.max_mode == 'MAX',
                                solver = solver,
                                output_new_knots = True)

                curves_list.append(new_curve)
                new_knots_list.append(new_knots.tolist())

            if curves_level == 2:
                curves_out.append(curves_list)
                new_knots_out.append(new_knots_list)
            else:
                curves_out.extend(curves_list)
                new_knots_out.extend(new_knots_list)

        self.outputs['Curve'].sv_set(curves_out)
        self.outputs['NewKnots'].sv_set(new_knots_out)

def register():
    bpy.utils.register_class(SvRefineNurbsCurveNode)

def unregister():
    bpy.utils.unregister_class(SvRefineNurbsCurveNode)

