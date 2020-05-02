
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

import sverchok
from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok.utils.logging import info, exception
from sverchok.utils.surface import SvSurface

class SvSurfaceGaussCurvatureNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Surface Gauss Curvature
    Tooltip: Calculate Gauss curvature for the surface at the specified point
    """
    bl_idname = 'SvSurfaceGaussCurvatureNode'
    bl_label = 'Surface Gauss Curvature'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_EVAL_SURFACE'

    @throttled
    def update_sockets(self, context):
        self.inputs['U'].hide_safe = self.input_mode == 'VERTICES'
        self.inputs['V'].hide_safe = self.input_mode == 'VERTICES'
        self.inputs['UVPoints'].hide_safe = self.input_mode == 'PAIRS'

    input_modes = [
        ('PAIRS', "Separate", "Separate U V (or X Y) sockets", 0),
        ('VERTICES', "Vertices", "Single socket for vertices", 1)
    ]

    input_mode : EnumProperty(
        name = "Input mode",
        items = input_modes,
        default = 'PAIRS',
        update = update_sockets)

    clamp_modes = [
        ('NO', "As is", "Do not clamp input values - try to process them as is (you will get either error or extrapolation on out-of-bounds values, depending on specific surface type", 0),
        ('CLAMP', "Clamp", "Clamp input values into bounds - for example, turn -0.1 into 0", 1),
        ('WRAP', "Wrap", "Wrap input values into bounds - for example, turn -0.1 into 0.9", 2)
    ]

    clamp_mode : EnumProperty(
            name = "Clamp",
            items = clamp_modes,
            default = 'NO',
            update = updateNode)

    axes = [
        ('XY', "X Y", "XOY plane", 0),
        ('YZ', "Y Z", "YOZ plane", 1),
        ('XZ', "X Z", "XOZ plane", 2)
    ]

    orientation : EnumProperty(
            name = "Orientation",
            items = axes,
            default = 'XY',
            update = updateNode)

    u_value : FloatProperty(
            name = "U",
            description = "Surface U parameter",
            default = 0.5,
            update = updateNode)

    v_value : FloatProperty(
            name = "V",
            description = "Surface V parameter",
            default = 0.5,
            update = updateNode)

    def draw_buttons(self, context, layout):
        layout.label(text="Input mode:")
        layout.prop(self, "input_mode", expand=True)
        if self.input_mode == 'VERTICES':
            layout.label(text="Input orientation:")
            layout.prop(self, "orientation", expand=True)
        layout.prop(self, 'clamp_mode', expand=True)

    def sv_init(self, context):
        self.inputs.new('SvSurfaceSocket', "Surface")
        self.inputs.new('SvVerticesSocket', "UVPoints")
        self.inputs.new('SvStringsSocket', "U").prop_name = 'u_value'
        self.inputs.new('SvStringsSocket', "V").prop_name = 'v_value'
        self.outputs.new('SvStringsSocket', "Curvature")
        self.update_sockets(context)

    def parse_input(self, verts):
        verts = np.array(verts)
        if self.orientation == 'XY':
            us, vs = verts[:,0], verts[:,1]
        elif self.orientation == 'YZ':
            us, vs = verts[:,1], verts[:,2]
        else: # XZ
            us, vs = verts[:,0], verts[:,2]
        return us, vs

    def _clamp(self, surface, us, vs):
        u_min = surface.get_u_min()
        u_max = surface.get_u_max()
        v_min = surface.get_v_min()
        v_max = surface.get_v_max()
        us = np.clip(us, u_min, u_max)
        vs = np.clip(vs, v_min, v_max)
        return us, vs

    def _wrap(self, surface, us, vs):
        u_min = surface.get_u_min()
        u_max = surface.get_u_max()
        v_min = surface.get_v_min()
        v_max = surface.get_v_max()
        u_len = u_max - u_min
        v_len = v_max - u_min
        us = (us - u_min) % u_len + u_min
        vs = (vs - v_min) % v_len + v_min
        return us, vs

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        surfaces_s = self.inputs['Surface'].sv_get()
        surfaces_s = ensure_nesting_level(surfaces_s, 2, data_types=(SvSurface,))
        src_point_s = self.inputs['UVPoints'].sv_get(default=[[]])
        src_point_s = ensure_nesting_level(src_point_s, 4)
        src_u_s = self.inputs['U'].sv_get()
        src_u_s = ensure_nesting_level(src_u_s, 3)
        src_v_s = self.inputs['V'].sv_get()
        src_v_s = ensure_nesting_level(src_v_s, 3)

        curvature_out = []
        for surfaces, src_points_i, src_u_i, src_v_i in zip_long_repeat(surfaces_s, src_point_s, src_u_s, src_v_s):
            new_curvatures = []
            for surface, src_points, src_us, src_vs in zip_long_repeat(surfaces, src_points_i, src_u_i, src_v_i):
                if self.input_mode == 'VERTICES':
                    us, vs = self.parse_input(src_points)
                else:
                    us, vs = np.array(src_us), np.array(src_vs)
                curvatures = surface.gauss_curvature_array(us, vs).tolist()
                new_curvatures.append(curvatures)
            curvature_out.extend(new_curvatures)

        self.outputs['Curvature'].sv_set(curvature_out)

def register():
    bpy.utils.register_class(SvSurfaceGaussCurvatureNode)

def unregister():
    bpy.utils.unregister_class(SvSurfaceGaussCurvatureNode)

