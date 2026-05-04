# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
import bpy
from bpy.props import EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.math import supported_metrics
from sverchok.utils.nurbs_common import SvNurbsMaths
from sverchok.utils.curve.core import SvCurve, UnsupportedCurveTypeException
from sverchok.utils.curve.nurbs import SvNurbsCurve
from sverchok.utils.surface.nurbs_algorithms import nurbs_birail, nurbs_birail_by_tensor_product, SWEEP_GREVILLE
from sverchok.utils.surface.gordon import nurbs_birail_by_gordon, MonotoneReparametrizer, SegmentsReparametrizer
from sverchok.dependencies import geomdl
from sverchok.dependencies import FreeCAD
from sverchok.dependencies import scipy

class SvNurbsBirailMk2Node(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: NURBS Birail
    Tooltip: Generate a NURBS surface by sweeping one curve along two other curves (a.k.a. birail)
    """
    bl_idname = 'SvNurbsBirailMk2Node'
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

    v_modes = [
            ('PARAM', "Path parameter uniform", "Distribute profile curves uniformly according to path curve parametrization", 0),
            ('LEN', "Path length uniform", "Distribute profile curves uniformly according to path curve length segments (natural parametrization)", 1),
            ('EXPLICIT', "Explicit values", "Provide values of V parameter (along path curve) for profile curves explicitly", 2),
            ('GREVILLE', "Greville abscissae", "Use Greville abscissae", 3)
        ]

    knotvector_accuracy : IntProperty(
            name = "Knotvector accuracy",
            min = 1,
            default = 6,
            update = updateNode)

    metric : EnumProperty(
            name = "Metric",
            description = "Metric to be used for interpolation",
            items = supported_metrics,
            default = 'DISTANCE',
            update = updateNode)

    implementations = []
    if geomdl is not None:
        implementations.append(
            (SvNurbsCurve.GEOMDL, "Geomdl", "Geomdl (NURBS-Python) package implementation", 0))
    implementations.append(
        (SvNurbsCurve.NATIVE, "Sverchok", "Sverchok built-in implementation", 1))
    if FreeCAD is not None:
        implementations.append(
            (SvNurbsMaths.FREECAD, "FreeCAD", "FreeCAD implementation", 2))

    nurbs_implementation : EnumProperty(
            name = "Implementation",
            items=implementations,
            update = updateNode)

    def update_sockets(self, context):
        self.inputs['V1'].hide_safe = self.v_mode != 'EXPLICIT'
        self.inputs['V2'].hide_safe = self.v_mode != 'EXPLICIT'
        self.inputs['VSections'].hide_safe = self.algorithm == 'CTRLPTS' or self.v_mode == 'GREVILLE'
        self.inputs['DegreeV'].hide_safe = self.algorithm != 'LOFT'
        self.inputs['Normal'].hide_safe = self.profile_rotation != 'CUSTOM'
        self.inputs['LengthResolution'].hide_safe = self.v_mode != 'LEN'
        updateNode(self, context)

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

    v_mode : EnumProperty(
        name = "Key V values",
        description = "How to place copies of profile curves along the path curves",
        items = v_modes,
        default = 'PARAM',
        update = update_sockets)

    length_resolution : IntProperty(
            name = "Length Resolution",
            min = 10,
            default = 50,
            update = updateNode)

    scale_uniform : BoolProperty(
        name = "Scale all axes",
        description = "If not checked, profile curves will be scaled along one axis only, in order to fill the space between two paths. If checked, profile curves will be scaled along all axes uniformly.",
        default = True,
        update = updateNode)

    auto_rotate_profiles : BoolProperty(
        name = "Auto rotate profiles",
        description = "If checked, then the node will try to rotate provided profile curves appropriately. Otherwise, the node expects provided profile curves to lie in XOY plane.",
        default = False,
        update = updateNode)

    rotate_options = [
            ('PATHS_AVG', "Paths Normal Average", "Rotate profile(s), trying to make it perpendicular to both paths", 0),
            ('FROM_PATH1', "Path 1 Normal", "Rotate profile(s), trying to make it perpendicular to the first path", 1),
            ('FROM_PATH2', "Path 2 Normal", "Rotate profile(s), trying to make it perpendicular to the second path", 2),
            ('FROM_PROFILE', "By profile", "Try to use initial rotation of profile curve(s)", 3),
            ('CUSTOM', "Custom", "Specify custom orientation by providing additional axis vector", 4)
        ]

    profile_rotation : EnumProperty(
            name = "Profile rotation",
            description = "Defines how profile curves should be rotated",
            items = rotate_options,
            default = 'PATHS_AVG',
            update = update_sockets)

    algorithms = [
            ('GORDON', "Gordon Surface", "Use Gordon Surface algorithm to follow path curves precisely", 0),
            ('LOFT', "Lofting", "Use legacy Loft algorithm; the surface can follow path curves not quite exactly; but this generates less control points", 1),
            ('CTRLPTS', "Tensor Product", "Tensor Product algorithm", 2)
        ]

    algorithm : EnumProperty(
            name = "Algorithm",
            items = algorithms,
            default = 'CTRLPTS',
            update = update_sockets)

    reparametrize_methods = [
            ('SEGMENTS', "Picewise Linear", "Simpler algorithm based on picewise linear reparametrization", 0)
        ]

    if scipy is not None:
        reparametrize_methods.append(
            ('MONOTONE', "Monotone Spline", "Reparametrization algorithm using monotone spline", 1)
        )

    reparametrize_method : EnumProperty(
        name = "Reparametrization",
        items = reparametrize_methods,
        update = updateNode)

    reparametrize_remove_knots : BoolProperty(
        name = "Remove knots",
        description = "Remove some of additional knots during reparametrization",
        default = False,
        update = updateNode)

    reparametrize_accuracy : IntProperty(
        name = "Reparametrization accuracy",
        default = 6,
        min = 1, max = 10,
        update = updateNode)

    reparametrize_samples_u : IntProperty(
        name = "Samples U",
        description = "Reparametrization samples along U direction",
        default = 20,
        min = 3,
        update = updateNode)

    reparametrize_samples_v : IntProperty(
        name = "Samples V",
        description = "Reparametrization samples along V direction",
        default = 20,
        min = 3,
        update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'nurbs_implementation', text='')
        layout.label(text='Algorithm:')
        layout.prop(self, 'algorithm', text='')
        layout.prop(self, "scale_uniform")
        layout.prop(self, "auto_rotate_profiles")
        layout.label(text="Profile rotation:")
        layout.prop(self, "profile_rotation", text='')
        if self.algorithm != 'CTRLPTS':
            layout.label(text="Profile V values:")
            layout.prop(self, "v_mode", text='')

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, 'u_knots_mode')
        layout.prop(self, 'knotvector_accuracy')
        if self.algorithm == 'LOFT':
            layout.prop(self, 'metric')
        if self.algorithm != 'CTRLPTS':
            layout.prop(self, 'reparametrize_method')
            if self.reparametrize_method == 'MONOTONE':
                row = layout.row()
                row.prop(self, 'reparametrize_samples_u')
                row.prop(self, 'reparametrize_samples_v')
            layout.prop(self, 'reparametrize_remove_knots')
            if self.reparametrize_remove_knots:
                layout.prop(self, 'reparametrize_accuracy')

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', "Path1")
        self.inputs.new('SvCurveSocket', "Path2")
        self.inputs.new('SvCurveSocket', "Profile")
        self.inputs.new('SvStringsSocket', "VSections").prop_name = 'profiles_count'
        self.inputs.new('SvStringsSocket', "V1")
        self.inputs.new('SvStringsSocket', "V2")
        self.inputs.new('SvStringsSocket', "DegreeV").prop_name = 'degree_v'
        self.inputs.new('SvStringsSocket', "LengthResolution").prop_name = 'length_resolution'
        p = self.inputs.new('SvVerticesSocket', "Normal")
        p.use_prop = True
        p.default_property = (0.0, 0.0, 1.0)
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
        if self.v_mode == 'EXPLICIT':
            v1_s = self.inputs['V1'].sv_get()
            v1_s = ensure_nesting_level(v1_s, 3)
            v2_s = self.inputs['V2'].sv_get()
            v2_s = ensure_nesting_level(v2_s, 3)
        else:
            v1_s = [[[]]]
            v2_s = [[[]]]
        profiles_count_s = self.inputs['VSections'].sv_get()
        degree_v_s = self.inputs['DegreeV'].sv_get()
        y_axis_s = self.inputs['Normal'].sv_get()
        resolution_s = self.inputs['LengthResolution'].sv_get()

        path1_s = ensure_nesting_level(path1_s, 2, data_types=(SvCurve,))
        path2_s = ensure_nesting_level(path2_s, 2, data_types=(SvCurve,))
        profile_s = ensure_nesting_level(profile_s, 3, data_types=(SvCurve,))
        profiles_count_s = ensure_nesting_level(profiles_count_s, 2)
        degree_v_s = ensure_nesting_level(degree_v_s, 2)
        y_axis_s = ensure_nesting_level(y_axis_s, 3)
        resolution_s = ensure_nesting_level(resolution_s, 2)

        reparametrize_tolerance = 10**(-self.reparametrize_accuracy)

        if scipy is None or self.reparametrize_method == 'SEGMENTS':
            reparametrizer = SegmentsReparametrizer(
                                remove_knots = self.reparametrize_remove_knots,
                                tolerance = reparametrize_tolerance)
        else:
            reparametrizer = MonotoneReparametrizer(
                                n_samples_u = self.reparametrize_samples_u,
                                n_samples_v = self.reparametrize_samples_v,
                                remove_knots = self.reparametrize_remove_knots,
                                tolerance = reparametrize_tolerance,
                                logger = self.sv_logger)

        surfaces_out = []
        curves_out = []
        v_curves_out = []
        for params in zip_long_repeat(path1_s, path2_s, profile_s, v1_s, v2_s, profiles_count_s, degree_v_s, y_axis_s, resolution_s):
            new_surfaces = []
            new_curves = []
            new_v_curves = []
            new_profiles = []
            for path1, path2, profiles, vs1, vs2, profiles_count, degree_v, y_axis, resolution in zip_long_repeat(*params):
                path1 = SvNurbsCurve.to_nurbs(path1)
                if path1 is None:
                    raise UnsupportedCurveTypeException("Path #1 is not a NURBS curve!")
                path2 = SvNurbsCurve.to_nurbs(path2)
                if path2 is None:
                    raise UnsupportedCurveTypeException("Path #2 is not a NURBS curve!")
                profiles = [SvNurbsCurve.to_nurbs(profile) for profile in profiles]
                if any(p is None for p in profiles):
                    raise UnsupportedCurveTypeException("Some of profiles are not NURBS curves!")
                if self.v_mode == 'EXPLICIT':
                    ts1 = np.array(vs1)
                    ts2 = np.array(vs2)
                elif self.v_mode == 'GREVILLE':
                    ts1 = SWEEP_GREVILLE
                    ts2 = SWEEP_GREVILLE
                else:
                    ts1 = None
                    ts2 = None
                if self.v_mode != 'LEN':
                    resolution = None
                if self.algorithm == 'GORDON':
                    unified_curves = []
                    v_curves = []
                    unified_curves, v_curves, surface = nurbs_birail_by_gordon(path1, path2, profiles,
                            ts1 = ts1, ts2 = ts2,
                            length_resolution = resolution,
                            min_profiles = profiles_count,
                            degree_v = degree_v,
                            metric = 'POINTS',
                            scale_uniform = self.scale_uniform,
                            auto_rotate = self.auto_rotate_profiles,
                            use_tangents = self.profile_rotation,
                            y_axis = np.array(y_axis),
                            implementation = self.nurbs_implementation,
                            knots_unification_method = self.u_knots_mode,
                            reparametrizer = reparametrizer,
                            knotvector_accuracy = self.knotvector_accuracy,
                            logger = self.sv_logger
                        )
                elif self.algorithm == 'CTRLPTS':
                    unified_curves = []
                    v_curves = []
                    surface = nurbs_birail_by_tensor_product(path1, path2, profiles,
                                    knots_u = self.u_knots_mode,
                                    knotvector_accuracy = self.knotvector_accuracy,
                                    scale_uniform = self.scale_uniform,
                                    auto_rotate = self.auto_rotate_profiles,
                                    use_tangents = self.profile_rotation,
                                    y_axis = np.array(y_axis),
                                    implementation = self.nurbs_implementation,
                                    logger = self.sv_logger)

                else: # LOFT
                    _, unified_curves, v_curves, surface = nurbs_birail(path1, path2,
                                        profiles,
                                        ts1 = ts1, ts2 = ts2,
                                        length_resolution = resolution,
                                        min_profiles = profiles_count,
                                        knots_u = self.u_knots_mode,
                                        knotvector_accuracy = self.knotvector_accuracy,
                                        degree_v = degree_v,
                                        metric = self.metric,
                                        scale_uniform = self.scale_uniform,
                                        auto_rotate = self.auto_rotate_profiles,
                                        use_tangents = self.profile_rotation,
                                        y_axis = np.array(y_axis),
                                        implementation = self.nurbs_implementation,
                                        logger = self.sv_logger
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
    bpy.utils.register_class(SvNurbsBirailMk2Node)

def unregister():
    bpy.utils.unregister_class(SvNurbsBirailMk2Node)

