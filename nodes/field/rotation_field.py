
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, throttle_and_update_node

from sverchok.utils.field.vector import (SvAverageVectorField, SvRotationVectorField, SvSelectVectorField)
from sverchok.utils.math import all_falloff_types, falloff_array

class SvRotationFieldNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Spin Field
    Tooltip: Generate vector rotation field
    """
    bl_idname = 'SvRotationFieldNode'
    bl_label = 'Rotation Field'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_ROTATION_FIELD'

    @throttle_and_update_node
    def update_type(self, context):
        self.inputs['Amplitude'].hide_safe = (self.falloff_type == 'NONE')
        coeff_types = ['inverse_exp', 'gauss', 'smooth', 'sphere', 'root', 'invsquare', 'sharp', 'linear', 'const']
        self.inputs['Coefficient'].hide_safe = (self.falloff_type not in coeff_types)

    falloff_type: EnumProperty(
        name="Falloff type", items=all_falloff_types, default='NONE', update=update_type)

    amplitude: FloatProperty(
        name="Amplitude", default=0.5, min=0.0, update=updateNode)

    coefficient: FloatProperty(
        name="Coefficient", default=0.5, update=updateNode)

    clamp: BoolProperty(
        name="Clamp", description="Restrict coefficient with R", default=False, update=updateNode)

    point_modes = [
        ('AVG', "Average", "Use average distance to all attraction centers", 0),
        ('MIN', "Nearest", "Use minimum distance to any of attraction centers", 1),
        ('SEP', "Separate", "Generate a separate field for each attraction center", 2)
    ]

    merge_mode: EnumProperty(
        name="Join mode",
        description="How to define the distance when multiple attraction centers are used",
        items=point_modes,
        default='AVG',
        update=updateNode)

    def sv_init(self, context):
        d = self.inputs.new('SvVerticesSocket', "Center")
        d.use_prop = True
        d.default_property = (0.0, 0.0, 0.0)

        d = self.inputs.new('SvVerticesSocket', "Direction")
        d.use_prop = True
        d.default_property = (0.0, 0.0, 1.0)


        self.inputs.new('SvStringsSocket', 'Amplitude').prop_name = 'amplitude'
        self.inputs.new('SvStringsSocket', 'Coefficient').prop_name = 'coefficient'

        self.outputs.new('SvVectorFieldSocket', "VField")

        self.update_type(context)

    def draw_buttons(self, context, layout):

        layout.prop(self, 'merge_mode')
        layout.prop(self, 'falloff_type')
        layout.prop(self, 'clamp')

    def merge_fields(self, vfields):
        if len(vfields) == 1:
            return vfields[0]
        elif self.merge_mode == 'AVG':
            vfield = SvAverageVectorField(vfields)
            return vfield
        elif self.merge_mode == 'MIN':
            if self.falloff_type == 'NONE':
                vfield = SvSelectVectorField(vfields, 'MIN')
            else:
                vfield = SvSelectVectorField(vfields, 'MAX')
            return vfield
        else: # SEP:
            return vfields

    def rotation_fields(self, centers, directions, falloff):
        vfields = []
        for center, direction in zip_long_repeat(centers, directions):
            vfield = SvRotationVectorField(np.array(center), np.array(direction), falloff=falloff)
            vfields.append(vfield)

        return self.merge_fields(vfields)

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        center_s = self.inputs['Center'].sv_get()
        directions_s = self.inputs['Direction'].sv_get()
        amplitudes_s = self.inputs['Amplitude'].sv_get()
        coefficients_s = self.inputs['Coefficient'].sv_get()

        vfields_out = []

        objects = zip_long_repeat(center_s, directions_s, amplitudes_s, coefficients_s)
        for centers, direction, amplitude, coefficient in objects:
            if isinstance(amplitude, (list, tuple)):
                amplitude = amplitude[0]
            if isinstance(coefficient, (list, tuple)):
                coefficient = coefficient[0]

            if self.falloff_type == 'NONE':
                falloff_func = None
            else:
                falloff_func = falloff_array(self.falloff_type, amplitude, coefficient, self.clamp)

            vfields_out.append(self.rotation_fields(centers, direction, falloff_func))


        self.outputs['VField'].sv_set(vfields_out)

def register():
    bpy.utils.register_class(SvRotationFieldNode)

def unregister():
    bpy.utils.unregister_class(SvRotationFieldNode)
