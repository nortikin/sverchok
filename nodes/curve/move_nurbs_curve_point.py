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
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level, repeat_last_for_length
from sverchok.utils.curve import SvCurve
from sverchok.utils.curve.nurbs import SvNurbsCurve
from sverchok.utils.curve.nurbs_algorithms import (
            move_curve_point_by_moving_control_point,
            move_curve_point_by_adjusting_one_weight,
            move_curve_point_by_adjusting_two_weights,
            move_curve_point_by_moving_control_points, TANGENT_PRESERVE,
            move_curve_point_by_inserting_knot)

class SvNurbsCurveMovePointNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Move NURBS curve point
    Tooltip: Adjust NURBS curve to move it's point to another location
    """
    bl_idname = 'SvNurbsCurveMovePointNode'
    bl_label = 'Move NURBS Curve Point'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_MOVE_CURVE_POINT'

    methods = [
            ('ONE_CPT', "Move one control point", "Move single control point", 0),
            ('ONE_WEIGHT', "Adjust one weight", "Change single weight", 1),
            ('TWO_WEIGHTS', "Adjust two weights", "Change two weights", 2),
            ('MOVE_CPTS', "Move control points", "Move several control points", 3),
            ('INSERT_KNOT', "Insert knot", "Insert additional knot and move several control points", 4)
        ]

    modes = [
            ('REL', "Relative", "Specify vector by which the point is to be moved", 0),
            ('ABS', "Absolute", "Specify target place where to place the point", 2)
        ]

    def update_sockets(self, context):
        self.inputs['Index'].hide_safe = self.method not in ['ONE_CPT', 'ONE_WEIGHT', 'TWO_WEIGHTS']
        self.inputs['Distance'].hide_safe = self.method not in ['ONE_WEIGHT', 'TWO_WEIGHTS']
        self.inputs['Vector'].hide_safe = self.method not in ['ONE_CPT', 'MOVE_CPTS', 'INSERT_KNOT']
        self.inputs['Vector'].label = 'Vector' if self.vector_mode == 'REL' else 'Point'
        updateNode(self, context)

    method : EnumProperty(
            name = "Method",
            description = "How should we modify the curve control points or weights",
            items = methods,
            default = 'ONE_CPT',
            update = update_sockets)

    vector_mode : EnumProperty(
            name = "Mode",
            items = modes,
            default = 'REL',
            update = update_sockets)

    t_value : FloatProperty(
            name = "T",
            description = "Curve parameter value",
            default = 0.5,
            update = updateNode)

    idx : IntProperty(
            name = "Index",
            description = "Control point or weight index to be adjusted",
            default = 1,
            min = 0,
            update = updateNode)

    distance : FloatProperty(
            name = "Distance",
            description = "How far to move the point; negative value mean move in the opposite direction",
            default = 1.0,
            update = updateNode)

    preserve_tangent : BoolProperty(
            name = "Preserve tangent",
            default = False,
            update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'method')
        if self.method in ['ONE_CPT', 'MOVE_CPTS', 'INSERT_KNOT']:
            layout.prop(self, 'vector_mode')
        if self.method == 'MOVE_CPTS':
            layout.prop(self, 'preserve_tangent')

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', "Curve")
        self.inputs.new('SvStringsSocket', "T").prop_name = 't_value'
        self.inputs.new('SvStringsSocket', "Index").prop_name = 'idx'
        self.inputs.new('SvStringsSocket', "Distance").prop_name = 'distance'
        p = self.inputs.new('SvVerticesSocket', "Vector")
        p.use_prop = True
        p.default_property = (1.0, 0.0, 0.0)
        self.outputs.new('SvCurveSocket', "Curve")
        self.update_sockets(context)

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        curve_s = self.inputs['Curve'].sv_get()
        t_value_s = self.inputs['T'].sv_get()
        index_s = self.inputs['Index'].sv_get()
        distance_s = self.inputs['Distance'].sv_get()
        vector_s = self.inputs['Vector'].sv_get()

        input_level = get_data_nesting_level(curve_s, data_types=(SvCurve,))
        flat_output = input_level < 2

        curve_s = ensure_nesting_level(curve_s, 2, data_types=(SvCurve,))
        t_value_s = ensure_nesting_level(t_value_s, 2)
        index_s = ensure_nesting_level(index_s, 2)
        distance_s = ensure_nesting_level(distance_s, 2)
        vector_s = ensure_nesting_level(vector_s, 3)

        relative = self.vector_mode == 'REL'

        curves_out = []
        for params in zip_long_repeat(curve_s, t_value_s, index_s, distance_s, vector_s):
            new_curves = []
            for curve, t_value, index, distance, vector in zip_long_repeat(*params):
                curve = SvNurbsCurve.to_nurbs(curve)
                if curve is None:
                    raise Exception("One of curves is not NURBS")

                vector = np.array(vector)
                if self.method == 'ONE_CPT':
                    new_curve = move_curve_point_by_moving_control_point(curve, t_value, index, vector, relative=relative)
                elif self.method == 'ONE_WEIGHT':
                    new_curve = move_curve_point_by_adjusting_one_weight(curve, t_value, index, distance)
                elif self.method == 'TWO_WEIGHTS':
                    new_curve = move_curve_point_by_adjusting_two_weights(curve, t_value, index, distance=distance)
                elif self.method == 'MOVE_CPTS':
                    if self.preserve_tangent:
                        tangent = TANGENT_PRESERVE
                    else:
                        tangent = None
                    new_curve = move_curve_point_by_moving_control_points(curve, t_value, vector, tangent=tangent, relative=relative)
                elif self.method == 'INSERT_KNOT':
                    new_curve = move_curve_point_by_inserting_knot(curve, t_value, vector, relative=relative)
                else:
                    raise Exception("Unsupported method")

                new_curves.append(new_curve)

            if flat_output:
                curves_out.extend(new_curves)
            else:
                curves_out.append(new_curves)

        self.outputs['Curve'].sv_set(curves_out)

def register():
    bpy.utils.register_class(SvNurbsCurveMovePointNode)

def unregister():
    bpy.utils.unregister_class(SvNurbsCurveMovePointNode)

