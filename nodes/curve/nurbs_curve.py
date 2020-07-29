
import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, fullList
from sverchok.utils.logging import info, exception
from sverchok.utils.curve.nurbs import SvNurbsCurve
from sverchok.utils.curve import knotvector as sv_knotvector
from sverchok.utils.dummy_nodes import add_dummy
from sverchok.dependencies import geomdl

class SvExNurbsCurveNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: NURBS Curve
    Tooltip: Generate NURBS Curve
    """
    bl_idname = 'SvExNurbsCurveNode'
    bl_label = 'Build NURBS Curve'
    bl_icon = 'CURVE_NCURVE'

    @throttled
    def update_sockets(self, context):
        self.inputs['Weights'].hide_safe = self.surface_mode == 'BSPLINE'
        self.inputs['Knots'].hide_safe = self.knot_mode == 'AUTO'

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

    implementation : EnumProperty(
            name = "Implementation",
            items = get_implementations,
            update = updateNode)

    surface_modes = [
        ('NURBS', "NURBS", "NURBS Surface", 0),
        ('BSPLINE', "BSpline", "BSpline Surface", 1)
    ]

    surface_mode : EnumProperty(
            name = "Curve mode",
            items = surface_modes,
            default = 'NURBS',
            update = update_sockets)

    knot_modes = [
        ('AUTO', "Auto", "Generate knotvector automatically", 0),
        ('EXPLICIT', "Explicit", "Specify knotvector explicitly", 1)
    ]

    knot_mode : EnumProperty(
            name = "Knotvector",
            items = knot_modes,
            default = 'AUTO',
            update = update_sockets)

    normalize_knots : BoolProperty(
            name = "Normalize Knots",
            default = True,
            update = updateNode)

    is_cyclic : BoolProperty(
            name = "Cyclic",
            default = False,
            update = updateNode)

    degree : IntProperty(
            name = "Degree",
            min = 2, max = 6,
            default = 3,
            update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'implementation', text='')
        layout.prop(self, "surface_mode", expand=True)
        col = layout.column(align=True)
        col.label(text='Knots:')
        row = col.row()
        row.prop(self, "knot_mode", expand=True)
        col.prop(self, 'normalize_knots', toggle=True)
        if self.knot_mode == 'AUTO':
            layout.prop(self, 'is_cyclic', toggle=True)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "ControlPoints")
        self.inputs.new('SvStringsSocket', "Weights")
        self.inputs.new('SvStringsSocket', "Knots")
        self.inputs.new('SvStringsSocket', "Degree").prop_name = 'degree'
        self.outputs.new('SvCurveSocket', "Curve")
        self.outputs.new('SvStringsSocket', "Knots")
        self.update_sockets(context)

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        vertices_s = self.inputs['ControlPoints'].sv_get()
        has_weights = self.inputs['Weights'].is_linked
        weights_s = self.inputs['Weights'].sv_get(default = [[1.0]])
        knots_s = self.inputs['Knots'].sv_get(default = [[]])
        degree_s = self.inputs['Degree'].sv_get()

        curves_out = []
        knots_out = []
        for vertices, weights, knots, degree in zip_long_repeat(vertices_s, weights_s, knots_s, degree_s):
            if isinstance(degree, (tuple, list)):
                degree = degree[0]

            n_source = len(vertices)
            fullList(weights, n_source)
            if self.knot_mode == 'AUTO' and self.is_cyclic:
                vertices = vertices + vertices[:degree+1]
                weights = weights + weights[:degree+1]
            n_total = len(vertices)

            # Set degree
            curve_degree = degree

            if has_weights and self.surface_mode == 'NURBS':
                curve_weights = weights
            else:
                curve_weights = None

            # Set knot vector
            if self.knot_mode == 'AUTO':
                if self.is_cyclic:
                    self.debug("N: %s, degree: %s", n_total, degree)
                    knots = list(range(n_total + degree + 1))
                else:
                    knots = sv_knotvector.generate(curve_degree, n_total)
                self.debug('Auto knots: %s', knots)
                curve_knotvector = knots
            else:
                self.debug('Manual knots: %s', knots)
                curve_knotvector = knots

            new_curve = SvNurbsCurve.build(self.implementation, degree, curve_knotvector, vertices, curve_weights)
            if self.is_cyclic:
                u_min = curve_knotvector[degree]
                u_max = curve_knotvector[-degree-2]
                new_curve.u_bounds = u_min, u_max
            else:
                u_min = min(curve_knotvector)
                u_max = max(curve_knotvector)
                new_curve.u_bounds = (u_min, u_max)
            curves_out.append(new_curve)
            knots_out.append(curve_knotvector)

        self.outputs['Curve'].sv_set(curves_out)
        self.outputs['Knots'].sv_set(knots_out)

def register():
    bpy.utils.register_class(SvExNurbsCurveNode)

def unregister():
    bpy.utils.unregister_class(SvExNurbsCurveNode)

