import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.surface import SvExSurface

class SvExSurfaceDomainNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Surface Domain / Range
    Tooltip: Output minimum and maximum values of U / V parameters allowed by the surface
    """
    bl_idname = 'SvExSurfaceDomainNode'
    bl_label = 'Surface Domain'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_SURFACE_DOMAIN'

    def sv_init(self, context):
        self.inputs.new('SvExSurfaceSocket', "Surface")
        self.outputs.new('SvStringsSocket', "UMin")
        self.outputs.new('SvStringsSocket', "UMax")
        self.outputs.new('SvStringsSocket', "URange")
        self.outputs.new('SvStringsSocket', "VMin")
        self.outputs.new('SvStringsSocket', "VMax")
        self.outputs.new('SvStringsSocket', "VRange")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        surface_s = self.inputs['Surface'].sv_get()
        if isinstance(surface_s[0], SvExSurface):
            surface_s = [surface_s]

        u_min_out = []
        u_max_out = []
        u_range_out = []
        v_min_out = []
        v_max_out = []
        v_range_out = []
        for surfaces in surface_s:
            new_u_min, new_u_max = [], []
            new_v_min, new_v_max = [], []
            new_u_range, new_v_range = [], []
            for surface in surfaces:
                u_min, u_max = surface.get_u_min(), surface.get_u_max()
                v_min, v_max = surface.get_v_min(), surface.get_v_max()
                u_range = u_max - u_min
                v_range = v_max - v_min

                new_u_min.append(u_min)
                new_u_max.append(u_max)
                new_u_range.append(u_range)

                new_v_min.append(v_min)
                new_v_max.append(v_max)
                new_v_range.append(v_range)

            u_min_out.append(new_u_min)
            u_max_out.append(new_u_max)
            u_range_out.append(new_u_range)

            v_min_out.append(new_v_min)
            v_max_out.append(new_v_max)
            v_range_out.append(new_v_range)

        self.outputs['UMin'].sv_set(u_min_out)
        self.outputs['UMax'].sv_set(u_max_out)
        self.outputs['URange'].sv_set(u_range_out)
        self.outputs['VMin'].sv_set(v_min_out)
        self.outputs['VMax'].sv_set(v_max_out)
        self.outputs['VRange'].sv_set(v_range_out)

def register():
    bpy.utils.register_class(SvExSurfaceDomainNode)

def unregister():
    bpy.utils.unregister_class(SvExSurfaceDomainNode)

