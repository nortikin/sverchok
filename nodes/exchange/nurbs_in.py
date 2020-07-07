
import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, StringProperty
from mathutils import Vector

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, split_by_count
from sverchok.utils.logging import info, exception
from sverchok.utils.curve import SvCurve
from sverchok.utils.surface import SvSurface
from sverchok.utils.curve.nurbs import SvExGeomdlCurve
from sverchok.utils.surface.nurbs import SvExGeomdlSurface
from sverchok.utils.dummy_nodes import add_dummy
from sverchok.dependencies import geomdl

if geomdl is None:
    add_dummy('SvExNurbsInNode', "NURBS In", 'geomdl')
else:
    from geomdl import NURBS, knotvector

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

    class SvExNurbsInNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Input NURBS
        Tooltip: Get NURBS curves
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

        def draw_buttons(self, context, layout):

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
            surface = NURBS.Surface()
            surface.degree_u = spline.order_u - 1
            surface.degree_v = spline.order_v - 1

            points = split_by_count(spline.points, spline.point_count_u)
            if self.apply_matrix:
                points = [[list(matrix @ Vector(p.co[:3])*p.co[3]) + [p.co[3]] for p in row] for row in points]
            else:
                points = [[tuple(p.co) for p in row] for row in points]
            if spline.use_cyclic_v:
                for row_idx in range(len(points)):
                    points[row_idx].extend(points[row_idx][:spline.order_v])
            if spline.use_cyclic_u:
                points.extend(points[:spline.order_u])

            # Control points
            surface.ctrlpts2d = points
            n_u_total = len(points)
            n_v_total= len(points[0])
            if spline.use_cyclic_u:
                knots_u = list(range(n_u_total + spline.order_u))
            else:
                knots_u = knotvector.generate(surface.degree_u, n_u_total, clamped=spline.use_endpoint_u)
            self.debug("Auto knots U: %s", knots_u)

            if spline.use_cyclic_v:
                knots_v = list(range(n_v_total + spline.order_v))
            else:
                knots_v = knotvector.generate(surface.degree_v, n_v_total, clamped=spline.use_endpoint_v)
            self.debug("Auto knots V: %s", knots_v)

            surface.knotvector_u = knots_u
            surface.knotvector_v = knots_v

            new_surf = SvExGeomdlSurface(surface)
            if spline.use_cyclic_u:
                u_min = surface.knotvector_u[surface.degree_u]
                u_max = surface.knotvector_u[-surface.degree_u - 2]
            else:
                if spline.use_endpoint_u:
                    u_min = min(surface.knotvector_u)
                    u_max = max(surface.knotvector_u)
                else:
                    u_min = surface.knotvector_u[surface.degree_u]
                    u_max = surface.knotvector_u[-surface.degree_u - 1]
            if spline.use_cyclic_v:
                v_min = surface.knotvector_v[surface.degree_v]
                v_max = surface.knotvector_v[-surface.degree_v - 2]
            else:
                if spline.use_endpoint_v:
                    v_min = min(surface.knotvector_v)
                    v_max = max(surface.knotvector_v)
                else:
                    v_min = surface.knotvector_v[surface.degree_v]
                    v_max = surface.knotvector_v[-surface.degree_v - 1]
            new_surf.u_bounds = u_min, u_max
            new_surf.v_bounds = v_min, v_max

            return new_surf

        def get_curve(self, spline, matrix):
            curve = NURBS.Curve()
            curve.degree = spline.order_u - 1
            if self.apply_matrix:
                vertices = [tuple(matrix @ Vector(p.co[:3])) for p in spline.points]
            else:
                vertices = [tuple(p.co)[:3] for p in spline.points]
            weights = [tuple(p.co)[3] for p in spline.points]
            if spline.use_cyclic_u:
                vertices = vertices + vertices[:curve.degree+1]
                weights = weights + weights[:curve.degree+1]
            n_total = len(vertices)
            curve.ctrlpts = vertices
            curve.weights = weights
            if spline.use_cyclic_u:
                knots = list(range(n_total + curve.degree + 1))
            else:
                knots = knotvector.generate(curve.degree, n_total, clamped=spline.use_endpoint_u)
            self.debug('Auto knots: %s', knots)
            curve.knotvector = knots

            new_curve = SvExGeomdlCurve(curve)
            if spline.use_cyclic_u:
                u_min = curve.knotvector[curve.degree]
                u_max = curve.knotvector[-curve.degree-2]
                new_curve.u_bounds = u_min, u_max
            else:
                if spline.use_endpoint_u:
                    u_min = min(curve.knotvector)
                    u_max = max(curve.knotvector)
                else:
                    u_min = curve.knotvector[curve.degree]
                    u_max = curve.knotvector[-curve.degree-1]
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

        def storage_get_data(self, node_dict):
            node_dict['object_names'] = [o.name for o in self.object_names]

def register():
    if geomdl is not None:
        bpy.utils.register_class(SvExNurbsInCallbackOp)
        bpy.utils.register_class(SvExNurbsInNode)

def unregister():
    if geomdl is not None:
        bpy.utils.unregister_class(SvExNurbsInNode)
        bpy.utils.unregister_class(SvExNurbsInCallbackOp)

