# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from mathutils import Vector

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, repeat_last_for_length, ensure_nesting_level, get_data_nesting_level
from sverchok.utils.curve.core import SvCurve
from sverchok.utils.curve.nurbs_algorithms import remove_excessive_knots
from sverchok.utils.curve.nurbs_solver_applications import curve_to_nurbs, CURVE_PARAMETER, CURVE_LENGTH, CURVE_CURVATURE, CURVE_ARBITRARY

class SvCurveToNurbsNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Curve Rebuild NURBS
    Tooltip: Convert arbitrary curve to NURBS
    """
    bl_idname = 'SvCurveToNurbsNode'
    bl_label = 'Curve to NURBS'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_CURVE_TO_NURBS'

    degree :  IntProperty(
            name = "Degree",
            min = 1,
            default = 3,
            update = updateNode)

    samples : IntProperty(
            name = "Samples",
            min = 3,
            default = 50,
            update = updateNode)

    resolution : IntProperty(
            name = "Length Resolution",
            min = 10,
            default = 50,
            update = updateNode)

    parametrizations = [
            (CURVE_LENGTH, "Natural (Curve Length)", "Natural curve parametrization (according to curve length)", 0),
            #(CURVE_CURVATURE, "Curvature", "Parametrization according to curvature", 1),
            (CURVE_PARAMETER, "Keep Original", "Keep original curve parametrization", 2),
            (CURVE_ARBITRARY, "Arbitrary", "Specify arbitrary curve parametrization", 3)
        ]

    def update_sockets(self, context):
        self.inputs['LengthResolution'].hide_safe = self.parametrization not in {CURVE_LENGTH,CURVE_CURVATURE}
        self.inputs['Parametrization'].hide_safe = self.parametrization != CURVE_ARBITRARY
        self.inputs['Tolerance'].hide_safe = self.simplify != True
        updateNode(self, context)

    parametrization : EnumProperty(
            name = "Parametrization",
            items = parametrizations,
            update = update_sockets)

    simplify : BoolProperty(
            name = "Simplify",
            default = True,
            update = update_sockets)

    tolerance : FloatProperty(
            name = "Tolerance",
            default = 1e-6,
            min = 0.0,
            precision = 8,
            update = updateNode)

    def draw_buttons(self, context, layout):
        layout.label(text='Parametrization:')
        layout.prop(self, 'parametrization', text='')
        layout.prop(self, 'simplify')

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', "Curve")
        self.inputs.new('SvStringsSocket', "Degree").prop_name = 'degree'
        self.inputs.new('SvStringsSocket', "Samples").prop_name = 'samples'
        self.inputs.new('SvStringsSocket', "LengthResolution").prop_name = 'resolution'
        self.inputs.new('SvCurveSocket', "Parametrization")
        self.inputs.new('SvStringsSocket', "Tolerance").prop_name = 'tolerance'
        self.outputs.new('SvCurveSocket', "Curve")
        self.update_sockets(context)

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        curves_s = self.inputs['Curve'].sv_get()
        input_level = get_data_nesting_level(curves_s, data_types=(SvCurve,))
        curves_s = ensure_nesting_level(curves_s, 2, data_types=(SvCurve,))
        nested_output = input_level > 1
        degree_s = self.inputs['Degree'].sv_get()
        degree_s = ensure_nesting_level(degree_s, 2)
        samples_s = self.inputs['Samples'].sv_get()
        samples_s = ensure_nesting_level(samples_s, 2)
        resolution_s = self.inputs['LengthResolution'].sv_get()
        resolution_s = ensure_nesting_level(resolution_s, 2)
        tolerance_s = self.inputs['Tolerance'].sv_get()
        tolerance_s = ensure_nesting_level(tolerance_s, 2)
        if self.parametrization == CURVE_ARBITRARY:
            parametrization_s = self.inputs['Parametrization'].sv_get()
            parametrization_s = ensure_nesting_level(parametrization_s, 2, data_types=(SvCurve,))
        else:
            parametrization_s = [[None]]

        curves_out = []
        for params in zip_long_repeat(curves_s, degree_s, samples_s, resolution_s, tolerance_s, parametrization_s):
            new_curves = []
            for curve, degree, samples, resolution, tolerance, parametrization in zip_long_repeat(*params):
                curve = curve_to_nurbs(degree, curve, samples,
                                       method = self.parametrization,
                                       parametrization = parametrization,
                                       resolution = resolution,
                                       logger = self.sv_logger)
                if self.simplify:
                    curve = remove_excessive_knots(curve, tolerance = tolerance)
                new_curves.append(curve)
            if nested_output:
                curves_out.append(new_curves)
            else:
                curves_out.extend(new_curves)
        self.outputs['Curve'].sv_set(curves_out)

def register():
    bpy.utils.register_class(SvCurveToNurbsNode)

def unregister():
    bpy.utils.unregister_class(SvCurveToNurbsNode)

