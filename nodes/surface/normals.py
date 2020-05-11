
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

import sverchok
from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level, repeat_last_for_length
from sverchok.utils.logging import info, exception
from sverchok.utils.surface import SvSurface

class SvSurfaceNormalsNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Surface Normals Tangents
    Tooltip: Calculate surface normals and tangents
    """
    bl_idname = 'SvSurfaceNormalsNode'
    bl_label = 'Surface Frame'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_SURFACE_FRAME'

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
        self.outputs.new('SvVerticesSocket', "Normal")
        self.outputs.new('SvVerticesSocket', "TangentU")
        self.outputs.new('SvVerticesSocket', "TangentV")
        self.outputs.new('SvStringsSocket', "AreaStretch")
        self.outputs.new('SvStringsSocket', "StretchU")
        self.outputs.new('SvStringsSocket', "StretchV")
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

        normal_out = []
        tangent_u_out = []
        tangent_v_out = []
        matrix_out = []
        area_out = []
        du_out = []
        dv_out = []

        for surfaces, src_points_i, src_u_i, src_v_i in zip_long_repeat(surfaces_s, src_point_s, src_u_s, src_v_s):
            new_normals = []
            new_tangent_u = []
            new_tangent_v = []
            new_area = []
            new_du = []
            new_dv = []
            for surface, src_points, src_us, src_vs in zip_long_repeat(surfaces, src_points_i, src_u_i, src_v_i):
                if self.input_mode == 'VERTICES':
                    us, vs = self.parse_input(src_points)
                else:
                    maxlen = max(len(src_us), len(src_vs))
                    src_us = repeat_last_for_length(src_us, maxlen)
                    src_vs = repeat_last_for_length(src_vs, maxlen)
                    us, vs = np.array(src_us), np.array(src_vs)

                data = surface.derivatives_data_array(us, vs)

                new_normals.append(data.unit_normals().tolist())
                du, dv = data.unit_tangents()
                new_tangent_u.append(du.tolist())
                new_tangent_v.append(dv.tolist())

                normals_len = [n[0] for n in data.normals_len().tolist()]
                new_area.append(normals_len)

                du_len, dv_len = data.tangent_lens()
                du_len = [n[0] for n in du_len.tolist()]
                dv_len = [n[0] for n in dv_len.tolist()]
                new_du.append(du_len)
                new_dv.append(dv_len)

                matrix_out.extend(data.matrices(as_mathutils = True))

            normal_out.append(new_normals)
            tangent_u_out.append(new_tangent_u)
            tangent_v_out.append(new_tangent_v)
            area_out.append(new_area)
            du_out.append(new_du)
            dv_out.append(new_dv)

        self.outputs['Normal'].sv_set(normal_out)
        self.outputs['TangentU'].sv_set(tangent_u_out)
        self.outputs['TangentV'].sv_set(tangent_v_out)
        self.outputs['Matrix'].sv_set(matrix_out)
        self.outputs['AreaStretch'].sv_set(area_out)
        self.outputs['StretchU'].sv_set(du_out)
        self.outputs['StretchV'].sv_set(dv_out)

def register():
    bpy.utils.register_class(SvSurfaceNormalsNode)

def unregister():
    bpy.utils.unregister_class(SvSurfaceNormalsNode)

