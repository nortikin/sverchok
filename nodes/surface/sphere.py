
import numpy as np
from math import pi

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, get_data_nesting_level
from sverchok.utils.surface import SvExLambertSphere, SvExEquirectSphere, SvExGallSphere

class SvExSphereNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Sphere
    Tooltip: Generate spherical surface (different projections are available)
    """
    bl_idname = 'SvExSphereNode'
    bl_label = 'Sphere (Surface)'
    bl_icon = 'MESH_UVSPHERE'

    projections = [
        ('EQUIRECT', "Equirectangular", "Equirectangular (geographic) projection", 0),
        ('LAMBERT', "Lambert", "Lambert cylindrical equal-area projection", 1),
        ('GALL', "Gall Stereographic", "Gall stereographic projection", 2)
    ]

    @throttled
    def update_sockets(self, context):
        self.inputs['Theta1'].hide_safe = self.projection != 'EQUIRECT'

    projection : EnumProperty(
        name = "Projection",
        items = projections,
        default = 'EQUIRECT',
        update = update_sockets)

    radius : FloatProperty(
        name = "Radius",
        default = 1.0,
        update = updateNode)

    theta1 : FloatProperty(
        name = "Theta1",
        description = "standard parallels (north and south of the equator) where the scale of the projection is true",
        default = pi/4,
        min = 0, max = pi/2,
        update = updateNode)

    def sv_init(self, context):
        p = self.inputs.new('SvVerticesSocket', "Center")
        p.use_prop = True
        p.prop = (0.0, 0.0, 0.0)
        self.inputs.new('SvStringsSocket', "Radius").prop_name = 'radius'
        self.inputs.new('SvStringsSocket', "Theta1").prop_name = 'theta1'
        self.outputs.new('SvExSurfaceSocket', "Surface")
        self.update_sockets(context)

    def draw_buttons(self, context, layout):
        layout.prop(self, "projection")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        center_s = self.inputs['Center'].sv_get()
        radius_s = self.inputs['Radius'].sv_get()
        theta1_s = self.inputs['Theta1'].sv_get()

        surfaces_out = []
        for center, radius, theta1 in zip_long_repeat(center_s, radius_s, theta1_s):
            if isinstance(radius, (list, tuple)):
                radius = radius[0]
            if isinstance(theta1, (list, tuple)):
                theta1 = theta1[0]

            if self.projection == 'EQUIRECT':
                surface = SvExEquirectSphere(np.array(center), radius, theta1)
            elif self.projection == 'LAMBERT':
                surface = SvExLambertSphere(np.array(center), radius)
            else:
                surface = SvExGallSphere(np.array(center), radius)
            surfaces_out.append(surface)
        self.outputs['Surface'].sv_set(surfaces_out)

def register():
    bpy.utils.register_class(SvExSphereNode)

def unregister():
    bpy.utils.unregister_class(SvExSphereNode)

