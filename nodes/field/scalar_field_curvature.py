
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, StringProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, match_long_repeat, ensure_nesting_level
from sverchok.utils.logging import info, exception

from sverchok.utils.field.scalar import SvScalarField, SvScalarFieldGaussCurvature, SvScalarFieldMeanCurvature, SvScalarFieldPrincipalCurvature, ScalarFieldCurvatureCalculator

class SvScalarFieldCurvatureNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Scalar Field Curvature
    Tooltip: Scalar Field Curvature
    """
    bl_idname = 'SvScalarFieldCurvatureNode'
    bl_label = 'Scalar Field Curvature'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_SCALAR_FIELD_MATH'

    def sv_init(self, context):
        self.inputs.new('SvScalarFieldSocket', "Field")
        self.outputs.new('SvScalarFieldSocket', "Gauss")
        self.outputs.new('SvScalarFieldSocket', "Mean")
        self.outputs.new('SvScalarFieldSocket', "Curvature1")
        self.outputs.new('SvScalarFieldSocket', "Curvature2")

    step : FloatProperty(
            name = "Step",
            default = 0.001,
            precision = 4,
            update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'step')

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        field_s = self.inputs['Field'].sv_get()
        field_s = ensure_nesting_level(field_s, 2, data_types=(SvScalarField,))
        step = self.step

        gauss_out = []
        mean_out = []
        k1_out = []
        k2_out = []
        for fields in field_s:
            for field in fields:
                calculator = ScalarFieldCurvatureCalculator(field, step)
                new_gauss = SvScalarFieldGaussCurvature(field, calculator)
                new_mean = SvScalarFieldMeanCurvature(field, calculator)
                new_k1 = SvScalarFieldPrincipalCurvature(field, calculator, 1)
                new_k2 = SvScalarFieldPrincipalCurvature(field, calculator, 2)

                gauss_out.append(new_gauss)
                mean_out.append(new_mean)
                k1_out.append(new_k1)
                k2_out.append(new_k2)

        self.outputs['Gauss'].sv_set(gauss_out)
        self.outputs['Mean'].sv_set(mean_out)
        self.outputs['Curvature1'].sv_set(k1_out)
        self.outputs['Curvature2'].sv_set(k2_out)

def register():
    bpy.utils.register_class(SvScalarFieldCurvatureNode)

def unregister():
    bpy.utils.unregister_class(SvScalarFieldCurvatureNode)

