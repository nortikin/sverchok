
import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, fullList
from sverchok.utils.logging import info, exception
from sverchok.utils.curve.nurbs import SvExGeomdlCurve
from sverchok.dependencies import geomdl

if geomdl is not None:
    from geomdl import NURBS, BSpline, knotvector
    
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

        surface_modes = [
            ('NURBS', "NURBS", "NURBS Surface", 0),
            ('BSPLINE', "BSpline", "BSpline Surface", 1)
        ]

        surface_mode : EnumProperty(
                name = "Surface mode",
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

                # Create a 3-dimensional B-spline Curve
                if self.surface_mode == 'NURBS':
                    curve = NURBS.Curve(normalize_kv = self.normalize_knots)
                else:
                    curve = BSpline.Curve(normalize_kv = self.normalize_knots)

                # Set degree
                curve.degree = degree

                # Set control points (weights vector will be 1 by default)
                # Use curve.ctrlptsw is if you are using homogeneous points as Pw
                curve.ctrlpts = vertices
                if has_weights and self.surface_mode == 'NURBS':
                    curve.weights = weights

                # Set knot vector
                if self.knot_mode == 'AUTO':
                    if self.is_cyclic:
                        self.debug("N: %s, degree: %s", n_total, degree)
                        knots = list(range(n_total + degree + 1))
                    else:
                        knots = knotvector.generate(curve.degree, n_total)
                    self.debug('Auto knots: %s', knots)
                    curve.knotvector = knots
                else:
                    self.debug('Manual knots: %s', knots)
                    #if not knotvector.check(curve.degree, knots, len(curve.ctrlpts)):
                    #    raise Exception("Explicitly provided knot vector is incorrect!")
                    curve.knotvector = knots

                new_curve = SvExGeomdlCurve(curve)
                if self.is_cyclic:
                    u_min = curve.knotvector[degree]
                    u_max = curve.knotvector[-degree-2]
                    new_curve.u_bounds = u_min, u_max
                else:
                    u_min = min(curve.knotvector)
                    u_max = max(curve.knotvector)
                    new_curve.u_bounds = (u_min, u_max)
                curves_out.append(new_curve)
                knots_out.append(curve.knotvector)

            self.outputs['Curve'].sv_set(curves_out)
            self.outputs['Knots'].sv_set(knots_out)

def register():
    if geomdl is not None:
        bpy.utils.register_class(SvExNurbsCurveNode)

def unregister():
    if geomdl is not None:
        bpy.utils.unregister_class(SvExNurbsCurveNode)

