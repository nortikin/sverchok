
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

from sverchok.utils.field.scalar import SvScalarFieldPointDistance
from sverchok.utils.math import falloff_types, falloff_array

class SvScalarFieldPointNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Scalar Field Point
    Tooltip: Generate scalar field by distance from a point
    """
    bl_idname = 'SvExScalarFieldPointNode'
    bl_label = 'Distance from a point'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_POINT_DISTANCE_FIELD'

    def update_type(self, context):
        self.inputs['Amplitude'].hide_safe = (self.falloff_type != 'NONE')
        self.inputs['Coefficient'].hide_safe = (self.falloff_type not in ['NONE', 'inverse_exp', 'gauss'])
        updateNode(self, context)

    falloff_type: EnumProperty(
        name="Falloff type", items=falloff_types, default='NONE', update=update_type)

    amplitude: FloatProperty(
        name="Amplitude", default=0.5, min=0.0, update=updateNode)

    coefficient: FloatProperty(
        name="Coefficient", default=0.5, update=updateNode)

    clamp: BoolProperty(
        name="Clamp", description="Restrict coefficient with R", default=False, update=updateNode)

    metrics = [
        ('EUCLIDEAN', "Euclidean", "Standard euclidean distance - sqrt(dx*dx + dy*dy + dz*dz)", 0),
        ('CHEBYSHEV', "Chebyshev", "Chebyshev distance - abs(dx, dy, dz)", 1),
        ('MANHATTAN', "Manhattan", "Manhattan distance - abs(dx) + abs(dy) + abs(dz)", 2),
        ('CUSTOM', "Custom", "Custom Minkowski metric defined by exponent factor", 3)
    ]

    metric : EnumProperty(
        name = "Metric",
        items = metrics,
        default = 'EUCLIDEAN',
        update = updateNode)

    power : FloatProperty(
            name = "Exponent",
            description = "Exponent for Minkowski metric",
            min = 1.0,
            default = 2,
            update = updateNode)

    def sv_init(self, context):
        d = self.inputs.new('SvVerticesSocket', "Center")
        d.use_prop = True
        d.default_property = (0.0, 0.0, 0.0)

        self.inputs.new('SvStringsSocket', 'Amplitude').prop_name = 'amplitude'
        self.inputs.new('SvStringsSocket', 'Coefficient').prop_name = 'coefficient'

        self.outputs.new('SvScalarFieldSocket', "Field")
        self.update_type(context)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'metric')
        if self.metric == 'CUSTOM':
            layout.prop(self, 'power')
        layout.prop(self, 'falloff_type')
        layout.prop(self, 'clamp')

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        center_s = self.inputs['Center'].sv_get()
        amplitudes_s = self.inputs['Amplitude'].sv_get(default=[0.5])
        coefficients_s = self.inputs['Coefficient'].sv_get(default=[0.5])

        fields_out = []
        for centers, amplitudes, coefficients in zip_long_repeat(center_s, amplitudes_s, coefficients_s):
            for center, amplitude, coefficient in zip_long_repeat(centers, amplitudes, coefficients):
                if self.falloff_type == 'NONE':
                    falloff_func = None
                else:
                    falloff_func = falloff_array(self.falloff_type, amplitude, coefficient, self.clamp)
                field = SvScalarFieldPointDistance(np.array(center), metric=self.metric, power=self.power, falloff=falloff_func)
                fields_out.append(field)

        self.outputs['Field'].sv_set(fields_out)

def register():
    bpy.utils.register_class(SvScalarFieldPointNode)

def unregister():
    bpy.utils.unregister_class(SvScalarFieldPointNode)

