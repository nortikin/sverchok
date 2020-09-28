# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, StringProperty
from mathutils import Vector

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.utils.nodes_mixins.sv_animatable_nodes import SvAnimatableNode
from sverchok.data_structure import updateNode, zip_long_repeat, split_by_count
from sverchok.utils.curve.algorithms import concatenate_curves
from sverchok.utils.curve.bezier import SvCubicBezierCurve

class SvBezierInCallbackOp(bpy.types.Operator):

    bl_idname = "node.sv_bezier_in_callback"
    bl_label = "Bezier In Callback"
    bl_options = {'INTERNAL'}

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

        node.get_objects_from_scene(self)
        return {'FINISHED'}

class SvBezierInNode(bpy.types.Node, SverchCustomTreeNode, SvAnimatableNode):
    """
    Triggers: Input Bezier
    Tooltip: Get Bezier Curve objects from scene
    """
    bl_idname = 'SvBezierInNode'
    bl_label = 'Bezier In'
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
        self.outputs.new('SvVerticesSocket', 'ControlPoints')
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
        self.draw_animatable_buttons(layout, icon_only=True)
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

        row.operator(SvBezierInCallbackOp.bl_idname, text=op_text)

        layout.prop(self, 'sort', text='Sort', toggle=True)
        layout.prop(self, 'apply_matrix', toggle=True)

        self.draw_obj_names(layout)

    def get_curve(self, spline, matrix):
        segments = []
        pairs = zip(spline.bezier_points, spline.bezier_points[1:])
        if spline.use_cyclic_u:
            pairs = list(pairs) + [(spline.bezier_points[-1], spline.bezier_points[0])]
        points = []
        is_first = True
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
        return points, concatenate_curves(segments)

    def process(self):

        if not self.object_names:
            return

        curves_out = []
        matrices_out = []
        controls_out = []
        for item in self.object_names:
            object_name = item.name
            obj = bpy.data.objects.get(object_name)
            if not obj:
                continue
            with self.sv_throttle_tree_update():
                matrix = obj.matrix_world
                if obj.type != 'CURVE':
                    self.warning("%s: not supported object type: %s", object_name, obj.type)
                    continue
                for spline in obj.data.splines:
                    if spline.type != 'BEZIER':
                        self.warning("%s: not supported spline type: %s", spline, spline.type)
                        continue
                    controls, curve = self.get_curve(spline, matrix)
                    curves_out.append(curve)
                    controls_out.append(controls)
                    matrices_out.append(matrix)

        self.outputs['Curves'].sv_set(curves_out)
        self.outputs['ControlPoints'].sv_set(controls_out)
        self.outputs['Matrices'].sv_set(matrices_out)

    def storage_get_data(self, node_dict):
        node_dict['object_names'] = [o.name for o in self.object_names]

def register():
    bpy.utils.register_class(SvBezierInCallbackOp)
    bpy.utils.register_class(SvBezierInNode)

def unregister():
    bpy.utils.unregister_class(SvBezierInNode)
    bpy.utils.unregister_class(SvBezierInCallbackOp)
