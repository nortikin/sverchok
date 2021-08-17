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
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok.utils.logging import info, exception
from sverchok.utils.curve import SvCurve
from sverchok.utils.curve.algorithms import SvIsoUvCurve
from sverchok.utils.curve.nurbs import SvNurbsCurve
from sverchok.utils.curve.primitives import SvLine
from sverchok.utils.surface.bevel_curve import nurbs_bevel_curve, generic_bevel_curve, BEVEL_SIMPLE, BEVEL_REFINE, BEVEL_GORDON
from sverchok.utils.field.vector import SvBendAlongCurveField

class SvBendCurveSurfaceNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Bevel Curve Surface
    Tooltip: Bevel a Curve - Surface
    """
    bl_idname = 'SvBendCurveSurfaceNode'
    bl_label = 'Bevel a Curve (Surface)'
    bl_icon = 'MOD_CURVE'

    algorithms = [
            (SvBendAlongCurveField.HOUSEHOLDER, "Householder", "Use Householder reflection matrix", 1),
            (SvBendAlongCurveField.TRACK, "Tracking", "Use quaternion-based tracking", 2),
            (SvBendAlongCurveField.DIFF, "Rotation difference", "Use rotational difference calculation", 3),
            (SvBendAlongCurveField.FRENET, "Frenet", "Use Frenet frames", 4),
            (SvBendAlongCurveField.ZERO, "Zero-Twist", "Use zero-twist frames", 5),
            (SvBendAlongCurveField.TRACK_NORMAL, "Track Normal", "Track normal", 6)
        ]

    def update_sockets(self, context):
        self.inputs['Resolution'].hide_safe = not(self.algorithm == SvBendAlongCurveField.ZERO or self.algorithm == SvBendAlongCurveField.TRACK_NORMAL or self.length_mode == 'L')
        if self.algorithm in {SvBendAlongCurveField.ZERO, SvBendAlongCurveField.FRENET, SvBendAlongCurveField.TRACK_NORMAL}:
            self.orient_axis = 'Z'

        is_generic = self.curve_mode == 'GENERIC'
        is_simple = self.precision_method == BEVEL_SIMPLE
        is_gordon = self.precision_method == BEVEL_GORDON
        self.inputs['ProfileCopies'].hide_safe = is_generic or not is_gordon
        self.inputs['TaperRefine'].hide_safe = is_generic or is_simple
        self.inputs['TaperCopies'].hide_safe = is_generic or not is_gordon

        updateNode(self, context)

    algorithm: EnumProperty(name = "Algorithm",
        description = "Rotation calculation algorithm",
        default = SvBendAlongCurveField.HOUSEHOLDER,
        items = algorithms, update=update_sockets)

    axes = [
        ("X", "X", "X axis", 1),
        ("Y", "Y", "Y axis", 2),
        ("Z", "Z", "Z axis", 3)]

    orient_axis: EnumProperty(name = "Orientation axis",
        description = "Which axis of donor objects to align with recipient curve",
        default = "Z",
        items = axes, update=updateNode)

    up_axis: EnumProperty(name = "Up axis",
        description = "Which axis of donor objects should look up",
        default = 'X',
        items = axes, update=updateNode)

    curve_modes = [
            ('GENERIC', "Generic", "Process arbitrary curves and output generic surface", 0),
            ('NURBS', "NURBS", "Process NURBS curves and output a NURBS surface", 1)
        ]

    curve_mode : EnumProperty(
            name = "Mode",
            default = 'GENERIC',
            items = curve_modes,
            update = update_sockets)

    precision_methods = [
            (BEVEL_SIMPLE, "Simple", "Transform existing control points only", 0),
            (BEVEL_REFINE, "Refine", "Refine taper curve and transform control points", 1),
            (BEVEL_GORDON, "Gordon", "Refine taper curve and use Gordon surface algorithm", 2)
        ]

    precision_method : EnumProperty(
            name = "Precision method",
            description = "Algorithm to be used to calculate control points of the surface",
            items = precision_methods,
            default = BEVEL_REFINE,
            update = update_sockets)

    resolution : IntProperty(
        name = "Resolution",
        min = 10, default = 50,
        update = updateNode)

    taper_samples : IntProperty(
        name = "Profile copies",
        description = "Number of copies of profile curve to be used for Gordon surface",
        min = 3, default = 10,
        update = updateNode)

    taper_refine : IntProperty(
        name = "Taper refine",
        description = "Number of additional knots to be inserted in the taper curve",
        min = 5, default = 20,
        update = updateNode)

    profile_samples : IntProperty(
        name = "Taper copies",
        description = "Number of copies of taper curve to be used for Gordon surface",
        min = 3, default = 10,
        update = updateNode)

    length_modes = [
        ('T', "Curve parameter", "Scaling along curve is depending on curve parametrization", 0),
        ('L', "Curve length", "Scaling along curve is proportional to curve segment length", 1)
    ]

    length_mode : EnumProperty(
        name = "Samples distribution along path",
        items = length_modes,
        default = 'T',
        update = update_sockets)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'curve_mode', expand=True)
        if self.curve_mode == 'NURBS':
            layout.prop(self, 'precision_method', text='Precision')
        layout.prop(self, "algorithm")
        layout.label(text="Orientation:")
        row = layout.row()
        row.prop(self, "orient_axis", expand=True)
        row.enabled = self.algorithm not in {SvBendAlongCurveField.ZERO, SvBendAlongCurveField.FRENET, SvBendAlongCurveField.TRACK_NORMAL}

        if self.algorithm == 'track':
            layout.prop(self, "up_axis")
        layout.label(text="Samples distribution:")
        layout.prop(self, 'length_mode', text='')

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', "Path")
        self.inputs.new('SvCurveSocket', "Profile")
        self.inputs.new('SvCurveSocket', "Taper")
        self.inputs.new('SvStringsSocket', "Resolution").prop_name = 'resolution'
        self.inputs.new('SvStringsSocket', "ProfileCopies").prop_name = 'taper_samples'
        self.inputs.new('SvStringsSocket', "TaperRefine").prop_name = 'taper_refine'
        self.inputs.new('SvStringsSocket', "TaperCopies").prop_name = 'profile_samples'
        self.outputs.new('SvSurfaceSocket', "Surface")
        self.outputs.new('SvCurveSocket', "CapStart")
        self.outputs.new('SvCurveSocket', "CapEnd")
        self.update_sockets(context)

    def _make_unit_taper(self, path, profile):
        orient_axis = self._get_orient_axis_idx()
        x_axis = (orient_axis + 1) % 3

        if profile is not None:
            profile_u_min = profile.get_u_bounds()[0]
            profile_start = profile.evaluate(profile_u_min)
            profile_start[orient_axis] = 0.0
            radius = np.linalg.norm(profile_start)
            if self.curve_mode != 'GENERIC':
                profile_degree = profile.get_degree()
            else:
                profile_degree = 2
        else:
            radius = 1.0
            profile_degree = 2

        path_u_min, path_u_max = path.get_u_bounds()
        path_start = path.evaluate(path_u_min)
        path_end = path.evaluate(path_u_max)

        z_min = path_u_min #path_start[orient_axis]
        z_max = path_u_max #path_end[orient_axis]

        p1 = np.zeros((3,), dtype=np.float64)
        p1[x_axis] = radius
        p1[orient_axis] = z_min

        p2 = np.zeros((3,), dtype=np.float64)
        p2[x_axis] = radius
        p2[orient_axis] = z_max

        taper = SvLine.from_two_points(p1, p2).to_nurbs()
        taper = taper.elevate_degree(target = max(profile_degree, 2))
        return taper

    def _get_orient_axis_idx(self):
        return 'XYZ'.index(self.orient_axis)

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        path_s = self.inputs['Path'].sv_get()
        profile_s = self.inputs['Profile'].sv_get()
        if self.inputs['Taper'].is_linked:
            scale_base = 'TAPER'
            taper_s = self.inputs['Taper'].sv_get()
            taper_s = ensure_nesting_level(taper_s, 2, data_types=(SvCurve,))
        else:
            scale_base = 'PROFILE'
            taper_s = [[None]]

        resolution_s = self.inputs['Resolution'].sv_get()
        taper_samples_s = self.inputs['ProfileCopies'].sv_get()
        taper_refine_s = self.inputs['TaperRefine'].sv_get()
        profile_samples_s = self.inputs['TaperCopies'].sv_get()

        input_level = get_data_nesting_level(path_s, data_types=(SvCurve,))

        path_s = ensure_nesting_level(path_s, 2, data_types=(SvCurve,))
        profile_s = ensure_nesting_level(profile_s, 2, data_types=(SvCurve,))

        orient_axis = self._get_orient_axis_idx()

        surface_out = []
        cap_start_out = []
        cap_end_out = []
        for params in zip_long_repeat(path_s, profile_s, taper_s, resolution_s, taper_samples_s, taper_refine_s, profile_samples_s):
            new_surfaces = []
            new_cap_start = []
            new_cap_end = []
            for path, profile, taper, resolution, taper_samples, taper_refine, profile_samples in zip_long_repeat(*params):
                if taper is None:
                    taper = self._make_unit_taper(path, profile)
                if self.curve_mode == 'GENERIC':
                    surface = generic_bevel_curve(path, profile, taper,
                                algorithm = self.algorithm,
                                path_axis = orient_axis,
                                path_length_resolution = resolution,
                                up_axis = self.up_axis,
                                scale_base = scale_base)
                else:
                    path = SvNurbsCurve.to_nurbs(path)
                    profile = SvNurbsCurve.to_nurbs(profile)
                    taper = SvNurbsCurve.to_nurbs(taper)
                    if path is None:
                        raise Exception("One of paths is not a NURBS curve")
                    if profile is None:
                        raise Exception("One of profiles is not a NURBS curve")
                    if taper is None:
                        raise Exception("One of tapers is not a NURBS curve")
                    
                    surface = nurbs_bevel_curve(path, profile, taper,
                                algorithm = self.algorithm,
                                path_axis = 'XYZ'.index(self.orient_axis),
                                path_length_resolution = resolution,
                                up_axis = self.up_axis,
                                precision_method = self.precision_method,
                                taper_samples = taper_samples,
                                taper_refine = taper_refine,
                                profile_samples = profile_samples)

                v_min, v_max = surface.get_v_min(), surface.get_v_max()
                cap_start = SvIsoUvCurve.take(surface, 'V', v_min)
                cap_end = SvIsoUvCurve.take(surface, 'V', v_max)

                new_surfaces.append(surface)
                new_cap_start.append(cap_start)
                new_cap_end.append(cap_end)

            if input_level < 2:
                surface_out.extend(new_surfaces)
                cap_start_out.extend(new_cap_start)
                cap_end_out.extend(new_cap_end)
            else:
                surface_out.append(new_surfaces)
                cap_start_out.append(new_cap_start)
                cap_end_out.append(new_cap_end)

        self.outputs['Surface'].sv_set(surface_out)
        if 'CapStart' in self.outputs:
            self.outputs['CapStart'].sv_set(cap_start_out)
        if 'CapEnd' in self.outputs:
            self.outputs['CapEnd'].sv_set(cap_end_out)

def register():
    bpy.utils.register_class(SvBendCurveSurfaceNode)

def unregister():
    bpy.utils.unregister_class(SvBendCurveSurfaceNode)

