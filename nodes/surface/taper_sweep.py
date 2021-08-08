
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok.utils.logging import info, exception
from sverchok.utils.curve import SvCurve
from sverchok.utils.curve.nurbs import SvNurbsCurve
from sverchok.utils.surface.algorithms import SvTaperSweepSurface
from sverchok.utils.surface.bevel_curve import nurbs_taper_sweep

class SvTaperSweepSurfaceNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Taper Sweep Curve
    Tooltip: Generate a taper surface along a line
    """
    bl_idname = 'SvExTaperSweepSurfaceNode'
    bl_label = 'Taper Sweep'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_TAPER_SWEEP'

    scale_options = [
            ('UNIT', "Unit", "Unit", 0),
            ('PROFILE', "Profile", "Profile", 1),
            ('TAPER', "Taper", "Taper", 2)
        ]
    
    scale_mode : EnumProperty(
            name = "Scale",
            items = scale_options,
            default = 'UNIT',
            update = updateNode)

    use_nurbs : BoolProperty(
        name = "NURBS",
        description = "Process NURBS curves and output a NURBS surface",
        default = False,
        update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'use_nurbs')
        layout.prop(self, 'scale_mode')

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', "Profile")
        self.inputs.new('SvCurveSocket', "Taper")
        p = self.inputs.new('SvVerticesSocket', "Point")
        p.use_prop = True
        p.default_property = (0.0, 0.0, 0.0)
        p = self.inputs.new('SvVerticesSocket', "Direction")
        p.use_prop = True
        p.default_property = (0.0, 0.0, 1.0)
        self.outputs.new('SvSurfaceSocket', "Surface")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        profile_s = self.inputs['Profile'].sv_get()
        taper_s = self.inputs['Taper'].sv_get()
        point_s = self.inputs['Point'].sv_get()
        direction_s = self.inputs['Direction'].sv_get()

        input_level = get_data_nesting_level(profile_s, data_types=(SvCurve,))

        profile_s = ensure_nesting_level(profile_s, 2, data_types=(SvCurve,))
        taper_s = ensure_nesting_level(taper_s, 2, data_types=(SvCurve,))

        point_s = ensure_nesting_level(point_s, 3)
        direction_s = ensure_nesting_level(direction_s, 3)

        def check_nurbs(*curves):
            return [SvNurbsCurve.to_nurbs(c) for c in curves]

        surface_out = []
        for params in zip_long_repeat(profile_s, taper_s, point_s, direction_s):
            new_surfaces = []
            for profile, taper, point, direction in zip_long_repeat(*params):
                if self.use_nurbs:
                    profile_nurbs, taper_nurbs = check_nurbs(profile, taper)
                    if profile_nurbs is None:
                        raise Exception("One of profiles is not NURBS")
                    if taper_nurbs is None:
                        raise Exception("One of tapers is not NURBS")

                    surface = nurbs_taper_sweep(profile_nurbs, taper_nurbs, np.array(point), np.array(direction),
                                scale_base = self.scale_mode)
                else:
                    surface = SvTaperSweepSurface(profile, taper, np.array(point), np.array(direction),
                                    scale_base = self.scale_mode)

                new_surfaces.append(surface)

            if input_level < 2:
                surface_out.extend(new_surfaces)
            else:
                surface_out.append(new_surfaces)

        self.outputs['Surface'].sv_set(surface_out)

def register():
    bpy.utils.register_class(SvTaperSweepSurfaceNode)

def unregister():
    bpy.utils.unregister_class(SvTaperSweepSurfaceNode)

