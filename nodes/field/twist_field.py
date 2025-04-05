# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
from math import pi

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat
from sverchok.utils.field.vector_primitives import SvTwistVectorField

class SvTwistFieldNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Twist Whirl Field
    Tooltip: Generate twisting / whirling vector field
    """
    bl_idname = 'SvTwistFieldNode'
    bl_label = 'Twist / Whirl Field'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_EX_ATTRACT'

    angle_along_axis : FloatProperty(
            name = "Twist Angle",
            description = "Angle for twisting around axis",
            default = pi/2,
            update = updateNode)

    angle_along_radius : FloatProperty(
            name = "Whirl Angle",
            description = "Angle for whirl force",
            default = 0.0,
            update = updateNode)

    flat_output : BoolProperty(
            name = "Flat Output",
            default = True,
            update = updateNode)

    def update_sockets(self, context):
        self.inputs['MinZ'].hide_safe = not self.use_min_z
        self.inputs['MaxZ'].hide_safe = not self.use_max_z
        self.inputs['MinR'].hide_safe = not self.use_min_r
        self.inputs['MaxR'].hide_safe = not self.use_max_r
        updateNode(self, context)

    use_min_z : BoolProperty(
            name = "Use Min Z",
            default = False,
            update = update_sockets)

    use_max_z : BoolProperty(
            name = "Use Max Z",
            default = False,
            update = update_sockets)

    use_min_r : BoolProperty(
            name = "Use Min Radius",
            default = False,
            update = update_sockets)

    use_max_r : BoolProperty(
            name = "Use Max Radius",
            default = False,
            update = update_sockets)

    min_z : FloatProperty(
            name = "Min Z",
            default = 0.0,
            update = updateNode)

    max_z : FloatProperty(
            name = "Max Z",
            default = 1.0,
            update = updateNode)

    min_r : FloatProperty(
            name = "Min Radius",
            min = 0.0,
            default = 0.0,
            update = updateNode)

    max_r : FloatProperty(
            name = "Max Radius",
            min = 0.0,
            default = 1.0,
            update = updateNode)

    def draw_buttons(self, context, layout):
        layout.label(text='Restrict Along Axis:')
        r = layout.row(align=True)
        r.prop(self, 'use_min_z', toggle=True)
        r.prop(self, 'use_max_z', toggle=True)
        layout.label(text='Restrict Along Radius:')
        r = layout.row(align=True)
        r.prop(self, 'use_min_r', toggle=True)
        r.prop(self, 'use_max_r', toggle=True)
        layout.prop(self, 'flat_output')

    def sv_init(self, context):
        d = self.inputs.new('SvVerticesSocket', "Center")
        d.use_prop = True
        d.default_property = (0.0, 0.0, 0.0)

        d = self.inputs.new('SvVerticesSocket', "Axis")
        d.use_prop = True
        d.default_property = (0.0, 0.0, 1.0)

        self.inputs.new('SvStringsSocket', 'TwistAngle').prop_name = 'angle_along_axis'
        self.inputs.new('SvStringsSocket', 'WhirlAngle').prop_name = 'angle_along_radius'

        self.inputs.new('SvStringsSocket', 'MinZ').prop_name = 'min_z'
        self.inputs.new('SvStringsSocket', 'MaxZ').prop_name = 'max_z'
        self.inputs.new('SvStringsSocket', 'MinR').prop_name = 'min_r'
        self.inputs.new('SvStringsSocket', 'MaxR').prop_name = 'max_r'

        self.outputs.new('SvVectorFieldSocket', "Field")
        self.update_sockets(context)

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        center_s = self.inputs['Center'].sv_get()
        axis_s = self.inputs['Axis'].sv_get()
        twist_angle_s = self.inputs['TwistAngle'].sv_get()
        whirl_angle_s = self.inputs['WhirlAngle'].sv_get()
        if self.use_min_z:
            min_z_s = self.inputs['MinZ'].sv_get()
        else:
            min_z_s = [[None]]
        if self.use_max_z:
            max_z_s = self.inputs['MaxZ'].sv_get()
        else:
            max_z_s = [[None]]
        if self.use_min_r:
            min_r_s = self.inputs['MinR'].sv_get()
        else:
            min_r_s = [[None]]
        if self.use_max_r:
            max_r_s = self.inputs['MaxR'].sv_get()
        else:
            max_r_s = [[None]]

        fields_out = []
        for params in zip_long_repeat(center_s, axis_s, twist_angle_s, whirl_angle_s, min_z_s, max_z_s, min_r_s, max_r_s):
            new_fields = []
            for center, axis, twist_angle, whirl_angle, min_z, max_z, min_r, max_r in zip_long_repeat(*params):
                field = SvTwistVectorField(center, axis, twist_angle, whirl_angle,
                                           min_z, max_z, min_r, max_r)
                new_fields.append(field)
            if self.flat_output:
                fields_out.extend(new_fields)
            else:
                fields_out.append(new_fields)

        self.outputs['Field'].sv_set(fields_out)

def register():
    bpy.utils.register_class(SvTwistFieldNode)

def unregister():
    bpy.utils.unregister_class(SvTwistFieldNode)


