
import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.logging import info, exception
from sverchok.utils.math import supported_metrics
from sverchok.utils.curve.core import SvCurve
from sverchok.utils.curve.nurbs import SvNurbsCurve
from sverchok.utils.surface.nurbs import simple_loft
from sverchok.dependencies import geomdl

class SvNurbsLoftNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: NURBS Loft / Skin
    Tooltip: Generate a NURBS surface by lofting (skinning) through several NURBS-like curves
    """
    bl_idname = 'SvNurbsLoftNode'
    bl_label = 'NURBS Loft'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_SURFACE_FROM_CURVES'

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
        return items

    nurbs_implementation : EnumProperty(
            name = "Implementation",
            items = get_implementations,
            update = updateNode)

    degree_v : IntProperty(
            name = "Degree V",
            min = 1, max = 7,
            default = 3,
            update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'nurbs_implementation', text='')

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, 'u_knots_mode')
        layout.prop(self, 'metric')

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', "Curves")
        self.inputs.new('SvStringsSocket', "DegreeV").prop_name = 'degree_v'
        self.outputs.new('SvSurfaceSocket', "Surface")
        self.outputs.new('SvCurveSocket', "UnifiedCurves")
        self.outputs.new('SvCurveSocket', "VCurves")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        curves_s = self.inputs['Curves'].sv_get()
        degrees_s = self.inputs['DegreeV'].sv_get()

        curves_s = ensure_nesting_level(curves_s, 3, data_types=(SvCurve,))
        degrees_s = ensure_nesting_level(degrees_s, 2)

        surface_out = []
        curves_out = []
        v_curves_out = []
        for curves_i, degrees in zip_long_repeat(curves_s, degrees_s):
            new_surfaces = []
            new_curves = []
            new_v_curves = []
            for curves, degree_v in zip_long_repeat(curves_i, degrees):
                unified_curves, v_curves, new_surface = simple_loft(curves, 
                                    degree_v = degree_v,
                                    knots_u = self.u_knots_mode,
                                    metric = self.metric,
                                    implementation = self.nurbs_implementation)
                new_surfaces.append(new_surface)
                new_curves.extend(unified_curves)
                new_v_curves.extend(v_curves)
            surface_out.append(new_surfaces)
            curves_out.append(new_curves)
            v_curves_out.append(new_v_curves)

        self.outputs['Surface'].sv_set(surface_out)
        self.outputs['UnifiedCurves'].sv_set(curves_out)
        self.outputs['VCurves'].sv_set(v_curves_out)

def register():
    bpy.utils.register_class(SvNurbsLoftNode)

def unregister():
    bpy.utils.unregister_class(SvNurbsLoftNode)

