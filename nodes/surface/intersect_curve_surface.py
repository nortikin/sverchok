
import bpy
from bpy.props import EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.curve import SvCurve
from sverchok.utils.surface import SvSurface
from sverchok.utils.manifolds import intersect_curve_surface


class SvExCrossCurveSurfaceNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Intersect Curve Surface
    Tooltip: Intersect Curve Surface
    """
    bl_idname = 'SvExCrossCurveSurfaceNode'
    bl_label = 'Intersect Curve with Surface'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_CROSS_CURVE_SURFACE'
    sv_dependencies = {'scipy'}

    raycast_samples : IntProperty(
        name = "Init Surface Samples",
        default = 10,
        min = 3,
        update = updateNode)

    curve_samples : IntProperty(
        name = "Init Curve Samples",
        default = 10,
        min = 1,
        update = updateNode)

    methods = [
        ('hybr', "Hybrd & Hybrj", "Use MINPACK’s hybrd and hybrj routines (modified Powell method)", 0),
        ('lm', "Levenberg-Marquardt", "Levenberg-Marquardt algorithm", 1),
        ('krylov', "Krylov", "Krylov algorithm", 2),
        ('broyden1', "Broyden 1", "Broyden1 algorithm", 3),
        ('broyden2', "Broyden 2", "Broyden2 algorithm", 4),
        ('anderson', 'Anderson', "Anderson algorithm", 5),
        ('df-sane', 'DF-SANE', "DF-SANE method", 6)
    ]

    raycast_method : EnumProperty(
        name = "Method",
        items = methods,
        default = 'hybr',
        update = updateNode)

    accuracy : IntProperty(
        name = "Accuracy",
        description = "Accuracy level - number of exact digits after decimal points.",
        default = 4,
        min = 1,
        update = updateNode)

    use_nurbs : BoolProperty(
        name = "NURBS",
        description = "Use special algorithm for NURBS curves",
        default = False,
        update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'raycast_samples')
        layout.prop(self, 'curve_samples')
        layout.prop(self, 'use_nurbs')

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, 'raycast_method')
        layout.prop(self, 'accuracy')

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', "Curve")
        self.inputs.new('SvSurfaceSocket', "Surface")
        self.outputs.new('SvVerticesSocket', "Point")
        self.outputs.new('SvStringsSocket', "T")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        surfaces_s = self.inputs['Surface'].sv_get()
        surfaces_s = ensure_nesting_level(surfaces_s, 2, data_types=(SvSurface,))
        curves_s = self.inputs['Curve'].sv_get()
        curves_s = ensure_nesting_level(curves_s, 2, data_types=(SvCurve,))

        tolerance = 10**(-self.accuracy)

        points_out = []
        u_out = []
        for surfaces, curves in zip_long_repeat(surfaces_s, curves_s):
            for surface, curve in zip_long_repeat(surfaces, curves):
                result = intersect_curve_surface(curve, surface,
                            init_samples = self.curve_samples,
                            raycast_samples = self.raycast_samples,
                            tolerance = tolerance,
                            raycast_method = self.raycast_method,
                            support_nurbs = self.use_nurbs
                        )
                new_points = [p[1] for p in result]
                new_u = [p[0] for p in result]
                points_out.append(new_points)
                u_out.append(new_u)

        self.outputs['Point'].sv_set(points_out)
        self.outputs['T'].sv_set(u_out)


def register():
    bpy.utils.register_class(SvExCrossCurveSurfaceNode)


def unregister():
    bpy.utils.unregister_class(SvExCrossCurveSurfaceNode)
