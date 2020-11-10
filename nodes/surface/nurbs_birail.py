# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, throttle_and_update_node
from sverchok.utils.logging import info, exception
from sverchok.utils.math import supported_metrics
from sverchok.utils.nurbs_common import SvNurbsMaths
from sverchok.utils.curve.core import SvCurve
from sverchok.utils.curve.nurbs import SvNurbsCurve
from sverchok.utils.surface.nurbs import nurbs_birail
from sverchok.dependencies import geomdl
from sverchok.dependencies import FreeCAD

class SvNurbsBirailNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: NURBS Birail
    Tooltip: Generate a NURBS surface by sweeping one curve along two other curves (a.k.a. birail)
    """
    bl_idname = 'SvNurbsBirailNode'
    bl_label = 'NURBS Birail'
    bl_icon = 'GP_MULTIFRAME_EDITING'

    u_knots_modes = [
            ('UNIFY', "Unify", "Unify knot vectors of curves by inserting knots into curves where needed", 0),
            ('AVERAGE', "Average", "Use average knot vector from curves; this will work only when curves have same number of control points!", 1)
        ]

    u_knots_mode : EnumProperty(
            name = "U Knots",
            description = "How to make slice curves knot vectors equal",
            items = u_knots_modes,
            default = 'UNIFY',
            update = updateNode)

    metric : EnumProperty(
            name = "Metric",
            description = "Metric to be used for interpolation",
            items = supported_metrics,
            default = 'DISTANCE',
            update = updateNode)

    def get_implementations(self, context):
        items = []
        i = 0
        if geomdl is not None:
            item = (SvNurbsCurve.GEOMDL, "Geomdl", "Geomdl (NURBS-Python) package implementation",i)
            i += 1
            items.append(item)
        item = (SvNurbsCurve.NATIVE, "Sverchok", "Sverchok built-in implementation", i)
        items.append(item)
        i += 1
        if FreeCAD is not None:
            item = (SvNurbsMaths.FREECAD, "FreeCAD", "FreeCAD implementation",i)
            i += 1
            items.append(item)
        return items

    nurbs_implementation : EnumProperty(
            name = "Implementation",
            items = get_implementations,
            update = updateNode)

    @throttle_and_update_node
    def update_sockets(self, context):
        self.inputs['V1'].hide_safe = not self.explicit_v
        self.inputs['V2'].hide_safe = not self.explicit_v

    profiles_count : IntProperty(
        name = "V Sections",
        description = "Number of profile curve instances to be placed along the path curve",
        min = 2,
        default = 10,
        update = updateNode)

    degree_v : IntProperty(
        name = "Degree V",
        description = "Degree of the surface along V direction",
        min = 1,
        default = 3,
        update = updateNode)

    explicit_v : BoolProperty(
        name = "Explicit V values",
        description = "Provide values of V parameter (along path curve) for profile curves explicitly",
        default = False,
        update = update_sockets)

    scale_uniform : BoolProperty(
        name = "Scale all axes",
        description = "If not checked, profile curves will be scaled along one axis only, in order to fill the space between two paths. If checked, profile curves will be scaled along all axes uniformly.",
        default = True,
        update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'nurbs_implementation', text='')
        layout.prop(self, "scale_uniform")
        layout.prop(self, "explicit_v")

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, 'u_knots_mode')
        layout.prop(self, 'metric')

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', "Path1")
        self.inputs.new('SvCurveSocket', "Path2")
        self.inputs.new('SvCurveSocket', "Profile")
        self.inputs.new('SvStringsSocket', "VSections").prop_name = 'profiles_count'
        self.inputs.new('SvStringsSocket', "V1")
        self.inputs.new('SvStringsSocket', "V2")
        self.inputs.new('SvStringsSocket', "DegreeV").prop_name = 'degree_v'
        self.outputs.new('SvSurfaceSocket', "Surface")
        self.outputs.new('SvCurveSocket', "AllProfiles")
        self.outputs.new('SvCurveSocket', "VCurves")
        self.update_sockets(context)

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        path1_s = self.inputs['Path1'].sv_get()
        path2_s = self.inputs['Path2'].sv_get()
        profile_s = self.inputs['Profile'].sv_get()
        if self.explicit_v:
            v1_s = self.inputs['V1'].sv_get()
            v1_s = ensure_nesting_level(v1_s, 3)
            v2_s = self.inputs['V2'].sv_get()
            v2_s = ensure_nesting_level(v2_s, 3)
        else:
            v1_s = [[[]]]
            v2_s = [[[]]]
        profiles_count_s = self.inputs['VSections'].sv_get()
        degree_v_s = self.inputs['DegreeV'].sv_get()

        path1_s = ensure_nesting_level(path1_s, 2, data_types=(SvCurve,))
        path2_s = ensure_nesting_level(path2_s, 2, data_types=(SvCurve,))
        profile_s = ensure_nesting_level(profile_s, 3, data_types=(SvCurve,))
        profiles_count_s = ensure_nesting_level(profiles_count_s, 2)
        degree_v_s = ensure_nesting_level(degree_v_s, 2)

        surfaces_out = []
        curves_out = []
        v_curves_out = []
        for params in zip_long_repeat(path1_s, path2_s, profile_s, v1_s, v2_s, profiles_count_s, degree_v_s):
            new_surfaces = []
            new_curves = []
            new_v_curves = []
            new_profiles = []
            for path1, path2, profiles, vs1, vs2, profiles_count, degree_v in zip_long_repeat(*params):
                path1 = SvNurbsCurve.to_nurbs(path1)
                if path1 is None:
                    raise Exception("Path #1 is not a NURBS curve!")
                path2 = SvNurbsCurve.to_nurbs(path2)
                if path2 is None:
                    raise Exception("Path #2 is not a NURBS curve!")
                profiles = [SvNurbsCurve.to_nurbs(profile) for profile in profiles]
                if any(p is None for p in profiles):
                    raise Exception("Some of profiles are not NURBS curves!")
                if self.explicit_v:
                    ts1 = np.array(vs1)
                    ts2 = np.array(vs2)
                else:
                    ts1 = None
                    ts2 = None
                _, unified_curves, v_curves, surface = nurbs_birail(path1, path2,
                                    profiles,
                                    ts1 = ts1, ts2 = ts2,
                                    min_profiles = profiles_count,
                                    knots_u = self.u_knots_mode,
                                    degree_v = degree_v,
                                    metric = self.metric,
                                    scale_uniform = self.scale_uniform,
                                    implementation = self.nurbs_implementation
                                )
                new_surfaces.append(surface)
                new_curves.extend(unified_curves)
                new_v_curves.extend(v_curves)
            surfaces_out.append(new_surfaces)
            curves_out.append(new_curves)
            v_curves_out.append(new_v_curves)

        self.outputs['Surface'].sv_set(surfaces_out)
        self.outputs['AllProfiles'].sv_set(curves_out)
        self.outputs['VCurves'].sv_set(v_curves_out)

def register():
    bpy.utils.register_class(SvNurbsBirailNode)

def unregister():
    bpy.utils.unregister_class(SvNurbsBirailNode)

