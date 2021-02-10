
from sverchok.utils.logging import info, exception

import numpy as np
from math import sqrt

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.geom import diameter

from sverchok.utils.field.vector import SvBendAlongSurfaceField

class SvBendAlongSurfaceFieldNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Bend surface
    Tooltip: Generate a vector field which bends the space along the given surface.
    """
    bl_idname = 'SvExBendAlongSurfaceFieldNode'
    bl_label = 'Bend Along Surface Field'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_BEND_SURFACE_FIELD'

    axes = [
            ("X", "X", "X axis", 1),
            ("Y", "Y", "Y axis", 2),
            ("Z", "Z", "Z axis", 3)
        ]

    orient_axis_: EnumProperty(
        name="Orientation axis", description="Which axis of object to put along path",
        default="Z", items=axes, update=updateNode)

    def get_axis_idx(self, letter):
        return 'XYZ'.index(letter)

    def get_orient_axis_idx(self):
        return self.get_axis_idx(self.orient_axis_)

    orient_axis = property(get_orient_axis_idx)

    autoscale: BoolProperty(
        name="Auto scale", description="Scale object along orientation axis automatically",
        default=False, update=updateNode)

    flip: BoolProperty(
        name="Flip surface",
        description="Flip the surface orientation",
        default=False, update=updateNode)

    u_min : FloatProperty(
        name = "Src U Min",
        default = -1.0,
        update = updateNode)

    u_max : FloatProperty(
        name = "Src U Max",
        default = 1.0,
        update = updateNode)

    v_min : FloatProperty(
        name = "Src V Min",
        default = -1.0,
        update = updateNode)

    v_max : FloatProperty(
        name = "Src V Max",
        default = 1.0,
        update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvSurfaceSocket', "Surface")
        self.inputs.new('SvStringsSocket', 'UMin').prop_name = 'u_min'
        self.inputs.new('SvStringsSocket', 'UMax').prop_name = 'u_max'
        self.inputs.new('SvStringsSocket', 'VMin').prop_name = 'v_min'
        self.inputs.new('SvStringsSocket', 'VMax').prop_name = 'v_max'
        self.outputs.new('SvVectorFieldSocket', 'Field')

    def draw_buttons(self, context, layout):
        layout.label(text="Object vertical axis:")
        layout.prop(self, "orient_axis_", expand=True)
        layout.prop(self, "autoscale", toggle=True)

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, 'flip')

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        surfaces_s = self.inputs['Surface'].sv_get()
        u_min_s = self.inputs['UMin'].sv_get()
        u_max_s = self.inputs['UMax'].sv_get()
        v_min_s = self.inputs['VMin'].sv_get()
        v_max_s = self.inputs['VMax'].sv_get()

        fields_out = []
        for surface, u_min, u_max, v_min, v_max in zip_long_repeat(surfaces_s, u_min_s, u_max_s, v_min_s, v_max_s):
            if isinstance(u_min, (list, int)):
                u_min = u_min[0]
            if isinstance(u_max, (list, int)):
                u_max = u_max[0]
            if isinstance(v_min, (list, int)):
                v_min = v_min[0]
            if isinstance(v_max, (list, int)):
                v_max = v_max[0]

            field = SvBendAlongSurfaceField(surface, self.orient_axis,
                        self.autoscale, self.flip)
            field.u_bounds = (u_min, u_max)
            field.v_bounds = (v_min, v_max)
            fields_out.append(field)

        self.outputs['Field'].sv_set(fields_out)

def register():
    bpy.utils.register_class(SvBendAlongSurfaceFieldNode)

def unregister():
    bpy.utils.unregister_class(SvBendAlongSurfaceFieldNode)

