# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, StringProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.nodes_mixins.show_3d_properties import Show3DProperties
from sverchok.utils.sv_operator_mixins import SvGenericNodeLocator
from sverchok.data_structure import updateNode, zip_long_repeat, split_by_count
from sverchok.utils.curve.algorithms import concatenate_curves
from sverchok.utils.curve.bezier import SvCubicBezierCurve


class SvBezierInCallbackOp(bpy.types.Operator, SvGenericNodeLocator):

    bl_idname = "node.sv_bezier_in_callback"
    bl_label = "Bezier In Callback"
    bl_options = {'INTERNAL'}

    def sv_execute(self, context, node):
        """
        passes the operator's 'self' too to allow calling self.report()
        """
        node.get_objects_from_scene(self)


class SvBezierInNode(Show3DProperties, SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Input Bezier
    Tooltip: Get Bezier Curve objects from scene
    """
    bl_idname = 'SvBezierInNode'
    bl_label = 'Bezier Input'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_OBJECTS_IN'

    @property
    def is_scene_dependent(self):
        return self.object_names

    @property
    def is_animation_dependent(self):
        return self.object_names

    object_names: bpy.props.CollectionProperty(type=bpy.types.PropertyGroup)

    sort: BoolProperty(
        name='sort by name',
        description='sorting inserted objects by names',
        default=True, update=updateNode)

    apply_matrix: BoolProperty(
        name = "Apply matrices",
        description = "Apply object matrices to control points",
        default = True,
        update = updateNode)
    
    concat_segments : BoolProperty(
        name = "Concatenate segments",
        description = "If checked, join Bezier segments of the curve into a single Curve object; otherwise, output a separate Curve object for each segment",
        default = True,
        update = updateNode)

    def sv_init(self, context):
        self.outputs.new('SvCurveSocket', 'Curves')
        self.outputs.new('SvVerticesSocket', 'ControlPoints')
        self.outputs.new('SvMatrixSocket', 'Matrices')
        self.outputs.new('SvStringsSocket', 'Tilt')
        self.outputs.new('SvStringsSocket', 'Radius')

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

    def draw_buttons_3dpanel(self, layout):
        row = layout.row(align=True)
        row.label(text=self.label if self.label else self.name)
        self.wrapper_tracked_ui_draw_op(row, SvBezierInCallbackOp.bl_idname, text='GET')
        self.wrapper_tracked_ui_draw_op(row, "node.sv_nodeview_zoom_border", text="", icon="TRACKER_DATA")

    def sv_draw_buttons(self, context, layout):
        col = layout.column(align=True)
        row = col.row(align=True)

        row = col.row()
        op_text = "Get selection"  # fallback

        if self.prefs_over_sized_buttons:
            row.scale_y = 4.0
            op_text = "G E T"

        self.wrapper_tracked_ui_draw_op(row, SvBezierInCallbackOp.bl_idname, text=op_text)

        layout.prop(self, 'sort', text='Sort', toggle=False)
        layout.prop(self, 'apply_matrix', toggle=False)
        layout.prop(self, 'concat_segments', toggle=False)

        self.draw_obj_names(layout)

    def get_curve(self, spline, matrix):
        segments = []
        pairs = zip(spline.bezier_points, spline.bezier_points[1:])
        if spline.use_cyclic_u:
            pairs = list(pairs) + [(spline.bezier_points[-1], spline.bezier_points[0])]
        points = []
        for p1, p2 in pairs:
            c0 = p1.co
            c1 = p1.handle_right
            c2 = p2.handle_left
            c3 = p2.co
            if self.apply_matrix:
                c0, c1, c2, c3 = [tuple(matrix @ c) for c in [c0, c1, c2, c3]]
            else:
                c0, c1, c2, c3 = [tuple(c) for c in [c0, c1, c2, c3]]
            points.append([c0, c1, c2, c3])
            segment = SvCubicBezierCurve(c0, c1, c2, c3)
            segments.append(segment)

        tilt_values = []
        radius_values = []
        if self.concat_segments:
            tilt_values = [p.tilt for p in spline.bezier_points]
            radius_values = [p.radius for p in spline.bezier_points]
            return points, tilt_values, radius_values, concatenate_curves(segments)
        else:
            for p1, p2 in pairs:
                tilt_values.append([p1.tilt, p2.tilt])
                radius_values.append([p1.radius, p2.radius])
            return points, tilt_values, radius_values, segments

    def process(self):

        if not self.object_names:
            return

        curves_out = []
        matrices_out = []
        controls_out = []
        tilt_out = []
        radius_out = []
        for item in self.object_names:
            object_name = item.name
            obj = bpy.data.objects.get(object_name)
            if not obj:
                continue

            matrix = obj.matrix_world
            if obj.type != 'CURVE':
                self.warning("%s: not supported object type: %s", object_name, obj.type)
                continue
            for spline in obj.data.splines:
                if spline.type != 'BEZIER':
                    self.warning("%s: not supported spline type: %s", spline, spline.type)
                    continue
                controls, tilt_values, radius_values, curve = self.get_curve(spline, matrix)
                n = len(tilt_values)
                #tilt_ts = range(n)
                #curve.tilt_pairs = list(zip(tilt_ts, tilt_values))
                curves_out.append(curve)
                controls_out.append(controls)
                matrices_out.append(matrix)
                tilt_out.append(tilt_values)
                radius_out.append(radius_values)

        self.outputs['Curves'].sv_set(curves_out)
        self.outputs['ControlPoints'].sv_set(controls_out)
        self.outputs['Matrices'].sv_set(matrices_out)
        if 'Tilt' in self.outputs:
            self.outputs['Tilt'].sv_set(tilt_out)
        if 'Radius' in self.outputs:
            self.outputs['Radius'].sv_set(radius_out)


def register():
    bpy.utils.register_class(SvBezierInCallbackOp)
    bpy.utils.register_class(SvBezierInNode)

def unregister():
    bpy.utils.unregister_class(SvBezierInNode)
    bpy.utils.unregister_class(SvBezierInCallbackOp)
