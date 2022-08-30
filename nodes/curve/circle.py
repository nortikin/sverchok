
import numpy as np
from math import pi

from mathutils import Matrix
import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.sv_transform_helper import AngleUnits, SvAngleHelper
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level

from sverchok.utils.curve import SvCircle

class SvCircleCurveMk2Node(bpy.types.Node, SverchCustomTreeNode, SvAngleHelper):
    """
    Triggers: Circle
    Tooltip: Generate circular curve
    """
    bl_idname = 'SvCircleCurveMk2Node'
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

    n_points : IntProperty(
        name = "N Points",
        description = "Number of corners in curve's control polygon",
        min = 3,
        default = 4,
        update = updateNode)

    def update_sockets(self, context):
        #self.inputs['TMin'].hide_safe = self.curve_mode != 'GENERIC'
        #self.inputs['TMax'].hide_safe = self.curve_mode != 'GENERIC'
        self.inputs['NPoints'].hide_safe = self.curve_mode != 'NURBS'
        updateNode(self, context)

    modes = [
            ('GENERIC', "Generic", "Create a generic Circle curve with standard angle-based parametrization", 0),
            ('NURBS', "NURBS", "Create a NURBS curve", 1)
        ]

    curve_mode : EnumProperty(
            name = "Mode",
            description = "Type of generated curve",
            items = modes,
            default = 'GENERIC',
            update = update_sockets)

    def update_angles(self, context, au):
        ''' Update all the angles to preserve their values in the new units '''
        self.t_min = self.t_min * au
        self.t_max = self.t_max * au

    def draw_buttons(self, context, layout):
        layout.prop(self, 'curve_mode', expand=True)
        self.draw_angle_units_buttons(context, layout)
        
    def sv_init(self, context):
        self.inputs.new('SvMatrixSocket', "Center")
        self.inputs.new('SvStringsSocket', "Radius").prop_name = 'radius'
        self.inputs.new('SvStringsSocket', "TMin").prop_name = 't_min'
        self.inputs.new('SvStringsSocket', "TMax").prop_name = 't_max'
        self.inputs.new('SvStringsSocket', "NPoints").prop_name = 'n_points'
        self.outputs.new('SvCurveSocket', "Curve")
        self.update_sockets(context)

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        center_s = self.inputs['Center'].sv_get(default=[Matrix()])
        radius_s = self.inputs['Radius'].sv_get()
        t_min_s = self.inputs['TMin'].sv_get()
        t_max_s = self.inputs['TMax'].sv_get()
        n_points_s = self.inputs['NPoints'].sv_get()

        radius_s = ensure_nesting_level(radius_s, 2)
        t_min_s = ensure_nesting_level(t_min_s, 2)
        t_max_s = ensure_nesting_level(t_max_s, 2)
        n_points_s = ensure_nesting_level(n_points_s, 2)
        center_s = ensure_nesting_level(center_s, 2, data_types=(Matrix,))

        curves_out = []
        for params in zip_long_repeat(center_s, radius_s, t_min_s, t_max_s, n_points_s):
            for center, radius, t_min, t_max, n_points in zip_long_repeat(*params):
                au = self.radians_conversion_factor()
                t_min, t_max = t_min*au, t_max*au
                curve = SvCircle(matrix=center, radius=radius)
                if self.curve_mode == 'GENERIC':
                    curve.u_bounds = (t_min, t_max)
                else:
                    curve = curve.to_nurbs_arc(n = n_points, t_min=t_min, t_max=t_max)
                curves_out.append(curve)

        self.outputs['Curve'].sv_set(curves_out)

def register():
    bpy.utils.register_class(SvCircleCurveMk2Node)

def unregister():
    bpy.utils.unregister_class(SvCircleCurveMk2Node)

