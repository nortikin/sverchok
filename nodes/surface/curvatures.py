
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

import sverchok
from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level, repeat_last_for_length
from sverchok.utils.logging import info, exception
from sverchok.utils.surface import SvSurface

class SvSurfaceCurvaturesNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Surface Curvature
    Tooltip: Calculate surface curvature values and directions
    """
    bl_idname = 'SvSurfaceCurvaturesNode'
    bl_label = 'Surface Curvature'
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

    order : BoolProperty(
            name = "Sort curvatures",
            description = "If enabled, make sure that Curvature1 is always less than Curvature2",
            default = True,
            update = updateNode)

    def draw_buttons(self, context, layout):
        layout.label(text="Input mode:")
        layout.prop(self, "input_mode", expand=True)
        if self.input_mode == 'VERTICES':
            layout.label(text="Input orientation:")
            layout.prop(self, "orientation", expand=True)
        layout.prop(self, 'clamp_mode', expand=True)
        layout.prop(self, 'order')

    def sv_init(self, context):
        self.inputs.new('SvSurfaceSocket', "Surface")
        self.inputs.new('SvVerticesSocket', "UVPoints")
        self.inputs.new('SvStringsSocket', "U").prop_name = 'u_value'
        self.inputs.new('SvStringsSocket', "V").prop_name = 'v_value'
        self.outputs.new('SvStringsSocket', "Curvature1")
        self.outputs.new('SvStringsSocket', "Curvature2")
        self.outputs.new('SvVerticesSocket', "Dir1")
        self.outputs.new('SvVerticesSocket', "Dir2")
        self.outputs.new('SvStringsSocket', "Gauss")
        self.outputs.new('SvStringsSocket', "Mean")
        self.outputs.new('SvMatrixSocket', "Matrix")
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

        need_values = self.outputs['Curvature1'].is_linked or self.outputs['Curvature2'].is_linked
        need_directions = self.outputs['Dir1'].is_linked or self.outputs['Dir2'].is_linked
        need_gauss = self.outputs['Gauss'].is_linked
        need_mean = self.outputs['Mean'].is_linked
        need_matrix = self.outputs['Matrix'].is_linked

        c1_out = []
        c2_out = []
        dir1_out = []
        dir2_out = []
        mean_out = []
        gauss_out = []
        matrix_out = []
        for surfaces, src_points_i, src_u_i, src_v_i in zip_long_repeat(surfaces_s, src_point_s, src_u_s, src_v_s):
            new_curvatures = []
            for surface, src_points, src_us, src_vs in zip_long_repeat(surfaces, src_points_i, src_u_i, src_v_i):
                if self.input_mode == 'VERTICES':
                    us, vs = self.parse_input(src_points)
                else:
                    maxlen = max(len(src_us), len(src_vs))
                    src_us = repeat_last_for_length(src_us, maxlen)
                    src_vs = repeat_last_for_length(src_vs, maxlen)
                    us, vs = np.array(src_us), np.array(src_vs)
                data = surface.curvature_calculator(us, vs, order=self.order).calc(need_values, need_directions, need_gauss, need_mean, need_matrix)
                if need_values:
                    c1_out.append(data.principal_value_1.tolist())
                    c2_out.append(data.principal_value_2.tolist())
                if need_directions:
                    dir1_out.append(data.principal_direction_1.tolist())
                    dir2_out.append(data.principal_direction_2.tolist())
                if need_mean:
                    mean_out.append(data.mean.tolist())
                if need_gauss:
                    gauss_out.append(data.gauss.tolist())
                if need_matrix:
                    matrix_out.extend(data.matrix)

        self.outputs['Curvature1'].sv_set(c1_out)
        self.outputs['Curvature2'].sv_set(c2_out)
        self.outputs['Dir1'].sv_set(dir1_out)
        self.outputs['Dir2'].sv_set(dir2_out)
        self.outputs['Mean'].sv_set(mean_out)
        self.outputs['Gauss'].sv_set(gauss_out)
        self.outputs['Matrix'].sv_set(matrix_out)

def register():
    bpy.utils.register_class(SvSurfaceCurvaturesNode)

def unregister():
    bpy.utils.unregister_class(SvSurfaceCurvaturesNode)

