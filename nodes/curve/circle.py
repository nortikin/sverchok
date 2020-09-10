
import numpy as np
from math import pi

from mathutils import Matrix
import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.utils.sv_transform_helper import AngleUnits, SvAngleHelper
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level

from sverchok.utils.curve import SvCircle

class SvCircleNode(bpy.types.Node, SverchCustomTreeNode, SvAngleHelper):
    """
    Triggers: Circle
    Tooltip: Generate circular curve
    """
    bl_idname = 'SvExCircleNode'
    bl_label = 'Circle (Curve)'
    bl_icon = 'MESH_CIRCLE'

    radius : FloatProperty(
        name = "Radius",
        default = 1.0,
        update = updateNode)

    t_min : FloatProperty(
        name = "T Min",
        default = 0.0,
        update = SvAngleHelper.update_angle)

    t_max : FloatProperty(
        name = "T Max",
        default = 2*pi,
        update = SvAngleHelper.update_angle)

    # Override properties from SvAngleHelper to set radians as default
    angle_units: EnumProperty(
        name="Angle Units", description="Angle units (Radians/Degrees/Unities)",
        default=AngleUnits.RADIANS, items=AngleUnits.get_blender_enum(),
        update=SvAngleHelper.update_angle_units)

    last_angle_units: EnumProperty(
        name="Last Angle Units", description="Angle units (Radians/Degrees/Unities)",
        default=AngleUnits.RADIANS, items=AngleUnits.get_blender_enum())

    def update_angles(self, context, au):
        ''' Update all the angles to preserve their values in the new units '''
        self.t_min = self.t_min * au
        self.t_max = self.t_max * au

    def draw_buttons(self, context, layout):
        self.draw_angle_units_buttons(context, layout)

    def sv_init(self, context):
        self.inputs.new('SvMatrixSocket', "Center")
        self.inputs.new('SvStringsSocket', "Radius").prop_name = 'radius'
        self.inputs.new('SvStringsSocket', "TMin").prop_name = 't_min'
        self.inputs.new('SvStringsSocket', "TMax").prop_name = 't_max'
        self.outputs.new('SvCurveSocket', "Curve")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        center_s = self.inputs['Center'].sv_get(default=[Matrix()])
        radius_s = self.inputs['Radius'].sv_get()
        t_min_s = self.inputs['TMin'].sv_get()
        t_max_s = self.inputs['TMax'].sv_get()
        radius_s = ensure_nesting_level(radius_s, 2)
        t_min_s = ensure_nesting_level(t_min_s, 2)
        t_max_s = ensure_nesting_level(t_max_s, 2)
        center_s = ensure_nesting_level(center_s, 2, data_types=(Matrix,))

        curves_out = []
        for centers, radiuses, t_mins, t_maxs in zip_long_repeat(center_s, radius_s, t_min_s, t_max_s):
            for center, radius, t_min, t_max in zip_long_repeat(centers, radiuses, t_mins, t_maxs):
                au = self.radians_conversion_factor()
                t_min, t_max = t_min*au, t_max*au
                curve = SvCircle(matrix=center, radius=radius)
                curve.u_bounds = (t_min, t_max)
                curves_out.append(curve)

        self.outputs['Curve'].sv_set(curves_out)

def register():
    bpy.utils.register_class(SvCircleNode)

def unregister():
    bpy.utils.unregister_class(SvCircleNode)

