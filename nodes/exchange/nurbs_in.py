
import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, StringProperty
from mathutils import Vector

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.utils.nodes_mixins.sv_animatable_nodes import SvAnimatableNode
from sverchok.data_structure import updateNode, zip_long_repeat, split_by_count
from sverchok.utils.curve import knotvector as sv_knotvector
from sverchok.utils.curve.nurbs import SvNurbsCurve
from sverchok.utils.surface.nurbs import SvNurbsSurface
from sverchok.utils.dummy_nodes import add_dummy
from sverchok.dependencies import geomdl

if geomdl is not None:
    from geomdl import NURBS

class SvExNurbsInCallbackOp(bpy.types.Operator):

    bl_idname = "node.sv_ex_nurbs_in_callback"
    bl_label = "Nurbs In Callback"
    bl_options = {'INTERNAL'}

    fn_name: StringProperty(default='')
    node_name: StringProperty(default='')
    tree_name: StringProperty(default='')

    def execute(self, context):
        """
        returns the operator's 'self' too to allow the code being called to
        print from self.report.
        """
        if self.tree_name and self.node_name:
            ng = bpy.data.node_groups[self.tree_name]
            node = ng.nodes[self.node_name]
        else:
            node = context.node

        getattr(node, self.fn_name)(self)
        return {'FINISHED'}

class SvExNurbsInNode(bpy.types.Node, SverchCustomTreeNode, SvAnimatableNode):
    """
    Triggers: Input NURBS
    Tooltip: Get NURBS curve or surface objects from scene
    """
    bl_idname = 'SvExNurbsInNode'
    bl_label = 'NURBS In'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_OBJECTS_IN'

    object_names: bpy.props.CollectionProperty(type=bpy.types.PropertyGroup)

    sort: BoolProperty(
        name='sort by name',
        description='sorting inserted objects by names',
        default=True, update=updateNode)

    apply_matrix : BoolProperty(
        name = "Apply matrices",
        description = "Apply object matrices to control points",
        default = True,
        update = updateNode)

    def sv_init(self, context):
        self.outputs.new('SvCurveSocket', 'Curves')
        self.outputs.new('SvSurfaceSocket', 'Surfaces')
        self.outputs.new('SvMatrixSocket', 'Matrices')

    def get_objects_from_scene(self, ops):
        """
        Collect selected objects
        """
        self.object_names.clear()

        names = [obj.name for obj in bpy.data.objects if (obj.select_get() and len(obj.users_scene) > 0 and len(obj.users_collection) > 0)]

        if self.sort:
            names.sort()

        for name in names:
            self.object_names.add().name = name

        if not self.object_names:
            ops.report({'WARNING'}, "Warning, no selected objects in the scene")
            return

        self.process_node(None)

    def draw_obj_names(self, layout):
        # display names currently being tracked, stop at the first 5..
        if self.object_names:
            remain = len(self.object_names) - 5

            for i, obj_ref in enumerate(self.object_names):
                layout.label(text=obj_ref.name)
                if i > 4 and remain > 0:
                    postfix = ('' if remain == 1 else 's')
                    more_items = '... {0} more item' + postfix
                    layout.label(text=more_items.format(remain))
                    break
        else:
            layout.label(text='--None--')

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

    def draw_buttons(self, context, layout):
        self.draw_animatable_buttons(layout, icon_only=True)
        layout.prop(self, 'implementation', text='')

        col = layout.column(align=True)
        row = col.row(align=True)

        row = col.row()
        op_text = "Get selection"  # fallback

        try:
            addon = context.preferences.addons.get(sverchok.__name__)
            if addon.preferences.over_sized_buttons:
                row.scale_y = 4.0
                op_text = "G E T"
        except:
            pass

        callback = 'node.sv_ex_nurbs_in_callback'
        row.operator(callback, text=op_text).fn_name = 'get_objects_from_scene'

        layout.prop(self, 'sort', text='Sort', toggle=True)
        layout.prop(self, 'apply_matrix', toggle=True)

        self.draw_obj_names(layout)

    def get_surface(self, spline, matrix):
        surface_degree_u = spline.order_u - 1
        surface_degree_v = spline.order_v - 1

        spline_points = split_by_count(spline.points, spline.point_count_u)
        if self.apply_matrix:
            control_points = [[list(matrix @ Vector(p.co[:3])) for p in row] for row in spline_points]
        else:
            control_points = [[tuple(p.co) for p in row] for row in spline_points]
        surface_weights = [[p.co[3] for p in row] for row in spline_points]
        if spline.use_cyclic_v:
            for row_idx in range(len(control_points)):
                control_points[row_idx].extend(control_points[row_idx][:spline.order_v])
        if spline.use_cyclic_u:
            control_points.extend(control_points[:spline.order_u])

        # Control points
        n_u_total = len(control_points)
        n_v_total= len(control_points[0])
        if spline.use_cyclic_u:
            knots_u = list(range(n_u_total + spline.order_u))
        else:
            knots_u = sv_knotvector.generate(surface_degree_u, n_u_total, clamped=spline.use_endpoint_u)
        self.debug("Auto knots U: %s", knots_u)

        if spline.use_cyclic_v:
            knots_v = list(range(n_v_total + spline.order_v))
        else:
            knots_v = sv_knotvector.generate(surface_degree_v, n_v_total, clamped=spline.use_endpoint_v)
        self.debug("Auto knots V: %s", knots_v)

        surface_knotvector_u = knots_u
        surface_knotvector_v = knots_v

        new_surf = SvNurbsSurface.build(self.implementation,
                        surface_degree_u, surface_degree_v,
                        surface_knotvector_u, surface_knotvector_v,
                        control_points, surface_weights,
                        normalize_knots = True)

        if spline.use_cyclic_u:
            u_min = surface_knotvector_u[surface_degree_u]
            u_max = surface_knotvector_u[-surface_degree_u - 2]
        else:
            if spline.use_endpoint_u:
                u_min = min(surface_knotvector_u)
                u_max = max(surface_knotvector_u)
            else:
                u_min = surface_knotvector_u[surface_degree_u]
                u_max = surface_knotvector_u[-surface_degree_u - 1]
        if spline.use_cyclic_v:
            v_min = surface_knotvector_v[surface_degree_v]
            v_max = surface_knotvector_v[-surface_degree_v - 2]
        else:
            if spline.use_endpoint_v:
                v_min = min(surface_knotvector_v)
                v_max = max(surface_knotvector_v)
            else:
                v_min = surface_knotvector_v[surface_degree_v]
                v_max = surface_knotvector_v[-surface_degree_v - 1]

        new_surf.u_bounds = u_min, u_max
        new_surf.v_bounds = v_min, v_max

        return new_surf

    def get_curve(self, spline, matrix):
        curve_degree = spline.order_u - 1
        if self.apply_matrix:
            vertices = [tuple(matrix @ Vector(p.co[:3])) for p in spline.points]
        else:
            vertices = [tuple(p.co)[:3] for p in spline.points]
        weights = [tuple(p.co)[3] for p in spline.points]
        if spline.use_cyclic_u:
            vertices = vertices + vertices[:curve_degree+1]
            weights = weights + weights[:curve_degree+1]
        n_total = len(vertices)
        curve_ctrlpts = vertices
        curve_weights = weights
        if spline.use_cyclic_u:
            knots = list(range(n_total + curve_degree + 1))
        else:
            knots = sv_knotvector.generate(curve_degree, n_total, clamped=spline.use_endpoint_u)
        self.debug('Auto knots: %s', knots)
        curve_knotvector = knots

        new_curve = SvNurbsCurve.build(self.implementation,
                        curve_degree, curve_knotvector,
                        curve_ctrlpts, curve_weights)
        if spline.use_cyclic_u:
            u_min = curve_knotvector[curve_degree]
            u_max = curve_knotvector[-curve_degree-2]
            new_curve = new_curve.cut_segment(u_min, u_max)
            #new_curve.u_bounds = u_min, u_max
        else:
            if spline.use_endpoint_u:
                u_min = min(curve_knotvector)
                u_max = max(curve_knotvector)
            else:
                u_min = curve_knotvector[curve_degree]
                u_max = curve_knotvector[-curve_degree-1]
            new_curve.u_bounds = (u_min, u_max)

        return new_curve

    def process(self):

        if not self.object_names:
            return

        curves_out = []
        surfaces_out = []
        matrices_out = []
        for item in self.object_names:
            object_name = item.name
            obj = bpy.data.objects.get(object_name)
            if not obj:
                continue
            with self.sv_throttle_tree_update():
                matrix = obj.matrix_world
                if obj.type not in {'SURFACE', 'CURVE'}:
                    self.warning("%s: not supported object type: %s", object_name, obj.type)
                    continue
                for spline in obj.data.splines:
                    if spline.type != 'NURBS':
                        self.warning("%s: not supported spline type: %s", spline, spline.type)
                        continue
                    if obj.type == 'SURFACE':
                        surface = self.get_surface(spline, matrix)
                        surfaces_out.append(surface)
                        matrices_out.append(matrix)
                    elif obj.type == 'CURVE':
                        curve = self.get_curve(spline, matrix)
                        curves_out.append(curve)
                        matrices_out.append(matrix)

        self.outputs['Curves'].sv_set(curves_out)
        self.outputs['Surfaces'].sv_set(surfaces_out)
        self.outputs['Matrices'].sv_set(matrices_out)


def register():
    bpy.utils.register_class(SvExNurbsInCallbackOp)
    bpy.utils.register_class(SvExNurbsInNode)

def unregister():
    bpy.utils.unregister_class(SvExNurbsInNode)
    bpy.utils.unregister_class(SvExNurbsInCallbackOp)
