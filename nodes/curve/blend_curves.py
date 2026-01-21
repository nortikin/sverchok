
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode, zip_long_repeat, ensure_nesting_level,
                                     repeat_last_for_length)
from sverchok.utils.curve.core import SvCurve
from sverchok.utils.curve.algorithms import concatenate_curves
from sverchok.utils.curve.blend_curves import blend_curves, BlendCurveSmoothness

class SvBlendCurvesMk2Node(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Blend curves
    Tooltip: Blend two or more curves by use of Bezier curve segment
    """
    bl_idname = 'SvExBlendCurvesMk2Node'
    bl_label = 'Blend Curves'
    bl_icon = 'CURVE_NCURVE'
    sv_icon = 'SV_BLEND_CURVE'

    factor1 : FloatProperty(
        name = "Factor 1",
        description = "Bulge factor for the first curve",
        default = 1.0,
        update = updateNode)

    factor2 : FloatProperty(
        name = "Factor 2",
        description = "Bulge factor for the second curve",
        default = 1.0,
        update = updateNode)

    parameter : FloatProperty(
        name = "Parameter",
        description = "P parameter for the family of biarcs",
        default = 1.0,
        update = updateNode)

    def update_sockets(self, context):
        self.inputs['Curve1'].hide_safe = self.mode != 'TWO'
        self.inputs['Curve2'].hide_safe = self.mode != 'TWO'
        self.inputs['Curves'].hide_safe = self.mode != 'N'
        self.inputs['Factor1'].hide_safe = self.smooth_mode not in ['1', 'G2']
        self.inputs['Factor2'].hide_safe = self.smooth_mode not in ['1', 'G2']
        self.inputs['Parameter'].hide_safe = self.smooth_mode != '1b'
        updateNode(self, context)

    modes = [
        ('TWO', "Two curves", "Blend two curves", 0),
        ('N', "List of curves", "Blend several curves", 1)
    ]

    mode : EnumProperty(
        name = "Blend",
        items = modes,
        default = 'TWO',
        update = update_sockets)

    smooth_modes = [
            (BlendCurveSmoothness.C0, "C0 - Position", "Connect ends of curves with straight line segment", 0),
            (BlendCurveSmoothness.C1, "G1 - Tangency", "Connect curves such that their tangents are continuosly joined", 1),
            (BlendCurveSmoothness.C1_BIARC, "G1 - Bi Arc", "Connect curves with Bi Arc, such that tangents are continuosly joined", 2),
            (BlendCurveSmoothness.C2_BEZIER, "C2 - Smooth Normals (Bezier)", "Connect curves such that their second derivatives are continuosly joined", 3),
            (BlendCurveSmoothness.C3_BEZIER, "C3 - Smooth Curvature (Bezier)", "Connect curves such that their third derivatives are continuosly joined", 4),
            (BlendCurveSmoothness.G2_BEZIER, "G2 - Curvature (Bezier)", "Connect curves such that their tangents, normals and curvatures are continuosly joined", 5),
            (BlendCurveSmoothness.C2_NURBS, "C2 - Smooth Normals (NURBS)", "Connect curves such that their second derivatives are continuosly joined", 6),
            (BlendCurveSmoothness.G2_NURBS, "G2 - Curvature (NURBS)", "Connect curves such that their tangents, normals and curvatures are continuosly joined", 7)
        ]

    smooth_mode : EnumProperty(
        name = "Continuity",
        description = "How smooth should be the blending; bigger value give more smooth curves",
        items = smooth_modes,
        default = '1',
        update = update_sockets)

    cyclic : BoolProperty(
        name = "Cyclic",
        description = "If checked, then the node will connect the end of last curve to the beginning of the first curve",
        default = False,
        update = updateNode)

    output_src : BoolProperty(
        name = "Output source curves",
        default = True,
        update = updateNode)

    join : BoolProperty(
            name = "Join",
            description = "Output single flat list of curves",
            default = True,
            update = updateNode)

    concat : BoolProperty(
        name = "Concatenate",
        description = "Concatenate source curves and blending curves into one curve",
        default = True,
        update = updateNode)

    planar_tolerance : FloatProperty(
            name = "Planar Tolerance",
            description = "Tolerance value for checking if the curve is planar",
            default = 1e-6,
            precision = 8,
            update = updateNode)

    def draw_buttons(self, context, layout):
        layout.label(text="Continuity:")
        layout.prop(self, 'smooth_mode', text='')
        layout.prop(self, "mode", text='')
        layout.prop(self, 'join')
        layout.prop(self, 'cyclic')
        layout.prop(self, 'output_src')
        row = layout.row()
        row.prop(self, 'concat')
        if self.output_src==False:
            row.enabled = False

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, 'planar_tolerance')

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', 'Curve1')
        self.inputs.new('SvCurveSocket', 'Curve2')
        self.inputs.new('SvCurveSocket', 'Curves')
        self.inputs.new('SvStringsSocket', "Factor1").prop_name = 'factor1'
        self.inputs.new('SvStringsSocket', "Factor2").prop_name = 'factor2'
        self.inputs.new('SvStringsSocket', "Parameter").prop_name = 'parameter'
        self.outputs.new('SvCurveSocket', 'Curve')
        self.outputs.new('SvVerticesSocket', "ControlPoints")
        self.update_sockets(context)

    def get_inputs(self):
        factor1_s = self.inputs['Factor1'].sv_get()
        factor2_s = self.inputs['Factor2'].sv_get()
        params_s = self.inputs['Parameter'].sv_get()

        factor1_s = ensure_nesting_level(factor1_s, 2)
        factor2_s = ensure_nesting_level(factor2_s, 2)
        params_s = ensure_nesting_level(params_s, 2)

        curves_s = []
        # unify curves's data for any self.mode
        if self.mode == 'TWO':
            curve1_s = self.inputs['Curve1'].sv_get()
            curve2_s = self.inputs['Curve2'].sv_get()
            curve1_s = ensure_nesting_level(curve1_s, 2, data_types=(SvCurve,))
            curve2_s = ensure_nesting_level(curve2_s, 2, data_types=(SvCurve,))

            for inputs in zip_long_repeat(curve1_s, curve2_s):
                curves_s.append( list( *zip_long_repeat(*inputs) ) )
        else:
            curves_s = self.inputs['Curves'].sv_get()

        curves_s = ensure_nesting_level(curves_s, 2, data_types=(SvCurve,))
        results = []
        for curves, factor1s, factor2s, params in zip_long_repeat(curves_s, factor1_s, factor2_s, params_s):
            factor1s = repeat_last_for_length(factor1s, len(curves))
            factor2s = repeat_last_for_length(factor2s, len(curves))
            params = repeat_last_for_length(params, len(curves))

            if len(curves)==1:
                item = list(zip(curves, curves, factor1s, factor2s, params))
            else:
                item = list(zip(curves, curves[1:], factor1s, factor2s, params))
                if self.cyclic:
                    item.append((curves[-1], curves[0], factor1s[-1], factor2s[-1], params[-1]))

            results.append(item)

        return results

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        curves_out = []
        controls_out = []

        for params in self.get_inputs():
            new_curves = []
            new_controls = []
            for curve1, curve2, factor1, factor2, parameter in params:
                if len(params)==1 and curve1==curve2 and self.cyclic==False:
                    if self.output_src:
                        new_curves.append(curve1)
                else:
                    new_curve, controls = blend_curves(curve1, curve2,
                                                       smoothness = self.smooth_mode,
                                                       factor1 = factor1, factor2 = factor2,
                                                       parameter = parameter,
                                                       planar_tolerance = self.planar_tolerance)
                    # There is two templates of result:
                    # 1. curve1 new_curve1 curve2 new_curve2 curve3 [new_curve3 curve4]/cyclic->curve1
                    # 2. curve1 cyclic->curve1
                    # 
                    #  I : cyclic==False and output_src==False then:
                    #    1. new_curve1 new_curve2
                    #    2. empty
                    # II : cyclic==False and output_src==True then:
                    #    1. curve1 new_curve1 curve2 new_curve2 curve3
                    #    2. curve1
                    # III: cyclic==True and output_src==True then:
                    #    1. curve1 new_curve1 curve2 new_curve2 curve3 cyclic
                    #    2. curve1 cyclic->curve1
                    # IV : cyclic==True and output_src==False then:
                    #    1. new_curve1 new_curve2 cyclic
                    #    2. cyclic

                    if self.cyclic==True:
                        # if self.cyclic==True then append a curve1 and a new curve
                        if self.output_src:
                            new_curves.append(curve1)
                        new_curves.append(new_curve)
                    else:
                        # if self.cyclic==False then append curve1 on first for iteration then
                        # append new_curve and curve2 on next iterations
                        if not new_curves and self.output_src:
                            new_curves.append(curve1)
                        new_curves.append(new_curve)
                        if curve1!=curve2 and self.output_src:
                            new_curves.append(curve2)
                    
                    new_controls.append(controls)

                pass # for params

            # One cannot concat of curves if no output_src (gaps)
            if self.output_src and self.concat:
                new_curves = [concatenate_curves(new_curves)]

            # With some params no new_curves (ex.: One curve with uncheck Cyclic)
            if new_curves:
                if self.join:
                    curves_out.extend(new_curves)
                    controls_out.extend(new_controls)
                else:
                    curves_out.append(new_curves)
                    controls_out.append(new_controls)

        self.outputs['Curve'].sv_set(curves_out)
        self.outputs['ControlPoints'].sv_set(controls_out)

def register():
    bpy.utils.register_class(SvBlendCurvesMk2Node)

def unregister():
    bpy.utils.unregister_class(SvBlendCurvesMk2Node)

