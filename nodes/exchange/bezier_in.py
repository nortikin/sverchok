# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, StringProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.nodes_mixins.show_3d_properties import Show3DProperties
from sverchok.utils.sv_operator_mixins import SvGenericNodeLocator
from sverchok.data_structure import updateNode, zip_long_repeat, split_by_count
from sverchok.utils.curve.algorithms import concatenate_curves
from sverchok.utils.curve.bezier import SvCubicBezierCurve


class SvBIDataCollectionMK2(bpy.types.PropertyGroup):
    base: bpy.props.IntProperty(default=1, min=1)
    name: bpy.props.StringProperty()
    exclude: bpy.props.BoolProperty(
        description='Exclude from process',
    )
    icon: bpy.props.StringProperty(default="BLANK1")


class ReadingBezierInDataError(Exception):
    pass


class SVBI_UL_NamesListMK2(bpy.types.UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        
        grid = layout.grid_flow(row_major=False, columns=4, align=True)

        object_exists=False
        chars = []
        if item.name in bpy.data.objects:
            object_exists=True
            splines = bpy.data.objects[item.name].data.splines
            if splines:
                for spline in splines:
                    chars.append(f"{len(spline.bezier_points)}{'c' if spline.use_cyclic_u else 'o'}")
                    pass
            else:
                chars=["[empty]"]
            pass

        item_icon = item.icon
        if not item.icon or item.icon == "BLANK1":
            try:
                item_icon = 'OUTLINER_OB_' + bpy.data.objects[item.name].type
            except:
                item_icon = "GHOST_DISABLED"
        item_base = len(str(len(data.object_names)))
        grid.label(text=f'{index:0{item_base}d} {item.name} {",".join(chars)}', icon=item_icon)
        #grid.prop(text='', icon='GHOST_ENABLED')

        if object_exists:
            op = grid.operator(SvBezierInItemSelectObjectMK2.bl_idname, icon='CURSOR', text='', emboss=False)
            op.idx = index

        else:
            pass

        if item.exclude:
            exclude_icon='UNPINNED'
        else:
            exclude_icon='PINNED'
        grid.prop(item, 'exclude', icon_only=True, icon=exclude_icon, emboss=False)
        pass
        op = grid.operator(SvBezierInItemRemoveMK2.bl_idname, icon='X', text='', emboss=False)
        op.fn_name = 'REMOVE'
        op.idx = index
        pass
        #action = data.wrapper_tracked_ui_draw_op(layout, "node.sv_bezierin_collection_operator_mk2", icon='X', text='', emboss=False)
        #action.fn_name = 'REMOVE'
        #action.idx = index

class SvBezierInItemSelectObjectMK2(bpy.types.Operator):
    '''Select object as active in 3D Viewport. Use shift to add object into current selection of objects in scene.'''
    bl_idname = "node.sv_bezierin_item_select_object_mk2"
    bl_label = "Select object as active"

    node_name: bpy.props.StringProperty()
    tree_name: bpy.props.StringProperty()  # all item types should have actual name of a tree
    fn_name: StringProperty(default='')
    idx: IntProperty()

    def invoke(self, context, event):
        node = context.node
        if node:
            if self.idx>=0 and self.idx<=len(node.object_names)-1:
                object_name = node.object_names[self.idx].name
                if object_name in bpy.data.objects:
                    obj = bpy.data.objects[object_name]
                    obj_location = obj.location
                    context.scene.cursor.location = obj_location[:]

                    for area in bpy.context.screen.areas:
                        if area.type == 'VIEW_3D':
                            with context.temp_override(area = area , region = area.regions[-1]):
                                #bpy.ops.view3d.view_center_cursor()
                                if event.shift==False:
                                    # Если Shift не нажат, то сбросить выделения всех объектов:
                                    for o in bpy.context.view_layer.objects:
                                        o.select_set(False)
                                bpy.context.view_layer.objects.active = obj
                                if obj.select_get()==False:
                                    obj.select_set(True)
                                #bpy.ops.view3d.view_selected(use_all_regions=False) # Иногда крашит Blender, пока отключил. Может вернусь позже. Оставлю пока только выделение объекта в сцене
                                break
            pass
        return {'FINISHED'}

# Тестовый пример оператора с получением события event.
class SvBezierInItemRemoveMK2(bpy.types.Operator):
    '''Remove object from list'''
    bl_idname = "node.sv_bezierin_item_remove_mk2"
    bl_label = "Remove"

    fn_name: StringProperty(default='')
    idx: IntProperty()

    def invoke(self, context, event):
        #node = context.node.object_names[self.idx]
        if self.idx <= len(context.node.object_names)-1:
            if self.fn_name == 'REMOVE':
                context.node.object_names.remove(self.idx)
                context.node.process_node(None)
        return {'FINISHED'}

class SvBezierInCallbackOpMK2(bpy.types.Operator, SvGenericNodeLocator):

    bl_idname = "node.sv_bezier_in_callback_mk2"
    bl_label = "Bezier In Callback mk2"
    bl_options = {'INTERNAL'}

    def sv_execute(self, context, node):
        """
        passes the operator's 'self' too to allow calling self.report()
        """
        node.get_objects_from_scene(self)

class SvBezierInAddObjectsFromSceneUpMK2(bpy.types.Operator, SvGenericNodeLocator):

    bl_idname = "node.sv_bezierin_add_object_from_scene_mk2"
    bl_label = "Add selected objects from scene into the list"
    bl_options = {'INTERNAL'}

    def sv_execute(self, context, node):
        """
        
        """
        node.add_objects_from_scene(self)

class SvBezierInMoveUpMK2(bpy.types.Operator, SvGenericNodeLocator):

    bl_idname = "node.sv_bezierin_moveup_mk2"
    bl_label = "Move current object up"
    bl_options = {'INTERNAL'}

    def sv_execute(self, context, node):
        """
        passes the operator's 'self' too to allow calling self.report()
        """
        node.move_current_object_up(self)

class SvBezierInMoveDownMK2(bpy.types.Operator, SvGenericNodeLocator):

    bl_idname = "node.sv_bezierin_movedown_mk2"
    bl_label = "Move current object down"
    bl_options = {'INTERNAL'}

    def sv_execute(self, context, node):
        """
        passes the operator's 'self' too to allow calling self.report()
        """
        node.move_current_object_down(self)

class SvBezierInClearObjectsFromListMK2(bpy.types.Operator, SvGenericNodeLocator):

    bl_idname = "node.sv_bezierin_clear_list_of_objects_mk2"
    bl_label = "Clear list of objects"
    bl_options = {'INTERNAL'}

    def sv_execute(self, context, node):
        """
        passes the operator's 'self' too to allow calling self.report()
        """
        node.clear_objects_from_list(self)

class SvBezierInViewAlignMK2(bpy.types.Operator, SvGenericNodeLocator):
    """ Zoom to object """
    bl_idname = "node.sv_bezierin_align_from_mk2"
    bl_label = "Align 3dview to Object"

    fn_name: bpy.props.StringProperty(default='')

    def sv_execute(self, context, node):

        if node.active_obj_index>=0 and node.active_obj_index<=len(node.object_names)-1:
            object_name = node.object_names[node.active_obj_index].name
            if object_name in bpy.data.objects:
                obj = bpy.data.objects[object_name]
                obj_location = obj.location
                vector_3d = obj_location        

                print(vector_3d)
                context.scene.cursor.location = vector_3d[:]

                for area in bpy.context.screen.areas:
                    if area.type == 'VIEW_3D':
                        with context.temp_override(area = area , region = area.regions[-1]):
                            #bpy.ops.view3d.view_center_cursor()
                            for o in bpy.context.view_layer.objects:
                                o.select_set(False)
                            bpy.context.view_layer.objects.active = obj
                            if obj.select_get()==False:
                                obj.select_set(True)
                            bpy.ops.view3d.view_selected(use_all_regions=False)

                            # for area in bpy.context.screen.areas:
                            #         if area.type == 'VIEW_3D':
                            #             for region in area.regions:
                            #                 if region.type == 'WINDOW':
                            #                     override = {
                            #                         'area': area,
                            #                         'region': region,
                            #                         'space': area.spaces.active,
                            #                     }
                            #                     bpy.ops.view3d.view_selected(use_all_regions=False)
        print("SvBezierInViewAlignMK2 FINISHED")
        return {'FINISHED'}

class SvBezierInHighlightAllObjectsInSceneMK2(bpy.types.Operator, SvGenericNodeLocator):
    '''Select and highlight object in 3D Viewport.'''
    bl_idname = "node.sv_bezierin_highlight_all_objects_in_list_scene_mk2"
    bl_label = "Highlight objects in scene"

    fn_name: StringProperty(default='')

    def invoke(self, context, event):
        node = context.node
        if node.active_obj_index>=0 and node.active_obj_index<=len(node.object_names)-1:
            object_name = node.object_names[node.active_obj_index].name
            if object_name in bpy.data.objects:
                obj = bpy.data.objects[object_name]
                obj_location = obj.location
                context.scene.cursor.location = obj_location[:]

                for area in bpy.context.screen.areas:
                    if area.type == 'VIEW_3D':
                        with context.temp_override(area = area , region = area.regions[-1]):
                            #bpy.ops.view3d.view_center_cursor()
                            for o in bpy.context.view_layer.objects:
                                o.select_set(False)
                            for object_name in node.object_names:
                                if object_name.name in bpy.data.objects:
                                    bpy.data.objects[object_name.name].select_set(True)
                                pass
                            bpy.context.view_layer.objects.active = obj
                            if obj.select_get()==False:
                                obj.select_set(True)
                            pass
                        pass
                    pass
                pass

        #print(f"SvBezierInHighlightAllObjectsInSceneMK2 FINISHED")
        return {'FINISHED'}



class SvBezierInNodeMK2(Show3DProperties, SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Input Bezier
    Tooltip: Get Bezier Curve objects from scene
    """
    bl_idname = 'SvBezierInNodeMK2'
    bl_label = 'Bezier Input MK2'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_OBJECTS_IN'

    @property
    def is_scene_dependent(self):
        return self.object_names

    @property
    def is_animation_dependent(self):
        return self.object_names
    
    #object_names: bpy.props.CollectionProperty(type=bpy.types.PropertyGroup)

    object_names: bpy.props.CollectionProperty(type=SvBIDataCollectionMK2)

    active_obj_index: bpy.props.IntProperty() # type: ignore

    source_curves_join_modes = [
            ('SEPARATE', "Separate", "Separate the object curves into individual curves", 'MOD_OFFSET', 0),
            ('KEEP' , "Keep", "Keep curves as in source objects", 'SYNTAX_ON', 1),
            #('MERGE', "Merge", "Join all curves into a single object", 'STICKY_UVS_LOC', 2)
        ]

    source_curves_join_mode : EnumProperty(
        name = "How process object curves",
        items = source_curves_join_modes,
        default = 'KEEP',
        update = updateNode) # type: ignore

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
    
    def draw_curves_out_socket(self, socket, context, layout):
        layout.prop(self, 'source_curves_join_mode', text='')
        if socket.is_linked:
            layout.label(text=f"{socket.label}. {socket.objects_number or ''}")
        else:
            layout.label(text=f'{socket.label}')
        pass
    
    def sv_init(self, context):
        self.outputs.new('SvCurveSocket', 'Curves')
        self.outputs.new('SvStringsSocket', 'use_cyclic_u').label='Cyclic U'
        #self.outputs.new('SvVerticesSocket', 'ControlPoints')
        self.outputs.new('SvVerticesSocket', 'control_points_c0')
        self.outputs.new('SvVerticesSocket', 'control_points_c1')
        self.outputs.new('SvVerticesSocket', 'control_points_c2')
        self.outputs.new('SvVerticesSocket', 'control_points_c3')
        self.outputs.new('SvMatrixSocket', 'Matrices')
        self.outputs.new('SvStringsSocket', 'Tilt')
        self.outputs.new('SvStringsSocket', 'Radius')

        self.outputs["Curves"].label = 'Curves'
        self.outputs["Curves"].custom_draw = 'draw_curves_out_socket'

        self.outputs['control_points_c0'].label = "Controls Points c0"
        self.outputs['control_points_c1'].label = "Controls Points handle c1"
        self.outputs['control_points_c2'].label = "Controls Points handle c2"
        self.outputs['control_points_c3'].label = "Controls Points c3"

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

    def add_objects_from_scene(self, ops):
        """
        Add selected objects on the top of the list
        """
        #self.object_names.clear()

        names = [obj.name for obj in bpy.data.objects if (obj.select_get() and len(obj.users_scene) > 0 and len(obj.users_collection) > 0)]

        for name in names:
            self.object_names.add().name = name
            self.object_names.move(len(self.object_names)-1, 0)
            self.active_obj_index=0

        if not self.object_names:
            ops.report({'WARNING'}, "Warning, no selected objects in the scene")
            return

        self.process_node(None)

    def clear_objects_from_list(self, ops):
        """
        Clear list of objects
        """
        self.object_names.clear()
        self.process_node(None)

    def move_current_object_up(self, ops):
        """
        Move current obbect in list up
        """

        if self.active_obj_index>0:
            self.object_names.move(self.active_obj_index, self.active_obj_index-1)
            self.active_obj_index-=1

        if not self.object_names:
            ops.report({'WARNING'}, "Warning, no selected objects in the scene")
            return

        self.process_node(None)

    def move_current_object_down(self, ops):
        """
        Move current obbect in list down
        """

        if self.active_obj_index<=len(self.object_names)-2:
            self.object_names.move(self.active_obj_index, self.active_obj_index+1)
            self.active_obj_index+=1

        self.process_node(None)

    def draw_obj_names(self, layout):
        # display names currently being tracked, stop at the first 5..
        # if self.object_names:
        #     remain = len(self.object_names) - 5

        #     for i, obj_ref in enumerate(self.object_names):
        #         layout.label(text=obj_ref.name)
        #         if i > 4 and remain > 0:
        #             postfix = ('' if remain == 1 else 's')
        #             more_items = '... {0} more item' + postfix
        #             layout.label(text=more_items.format(remain))
        #             break
        # else:
        #     layout.label(text='--None--')

        if self.object_names:
            #layout.template_list("SVBI_UL_NamesListMK2", "", self, "object_names", self, "active_obj_index")
            
            # grid = layout.grid_flow(row_major=False, columns=2, align=True)
            # grid.template_list("SVBI_UL_NamesListMK2", "", self, "object_names", self, "active_obj_index")
            # col = grid.column(align=True)
            # self.wrapper_tracked_ui_draw_op(col, SvBezierInMoveUpMK2.bl_idname, text='', icon='TRIA_UP')
            # self.wrapper_tracked_ui_draw_op(col, SvBezierInMoveDownMK2.bl_idname, text='', icon='TRIA_DOWN')
            
            # object_names_base = len(f'{len(self.object_names)}')
            # for I, elem in enumerate(self.object_names):
            #     elem.base = object_names_base
            #     pass

            row = layout.row(align=True)
            row.column().template_list("SVBI_UL_NamesListMK2", "", self, "object_names", self, "active_obj_index")
            col = row.column(align=True)
            self.wrapper_tracked_ui_draw_op(col, SvBezierInAddObjectsFromSceneUpMK2.bl_idname, text='', icon='ADD')
            self.wrapper_tracked_ui_draw_op(col, SvBezierInMoveUpMK2.bl_idname, text='', icon='TRIA_UP')
            self.wrapper_tracked_ui_draw_op(col, SvBezierInMoveDownMK2.bl_idname, text='', icon='TRIA_DOWN')
            self.wrapper_tracked_ui_draw_op(col, SvBezierInHighlightAllObjectsInSceneMK2.bl_idname, text='', icon='GROUP_VERTEX')

        else:
            layout.label(text='--None--')

    def draw_buttons_3dpanel(self, layout):
        row = layout.row(align=True)
        row.label(text=self.label if self.label else self.name)
        self.wrapper_tracked_ui_draw_op(row, SvBezierInCallbackOpMK2.bl_idname, text='GET')
        self.wrapper_tracked_ui_draw_op(row, "node.sv_nodeview_zoom_border", text="", icon="TRACKER_DATA")

    def sv_draw_buttons(self, context, layout):
        col = layout.column(align=True)
        row = col.row(align=True)

        row = col.row()
        op_text = "Get selection"  # fallback

        if self.prefs_over_sized_buttons:
            row.scale_y = 4.0
            op_text = "G E T"

        self.wrapper_tracked_ui_draw_op(row, SvBezierInCallbackOpMK2.bl_idname, text=op_text)

        layout.prop(self, 'sort', text='Sort', toggle=False)
        layout.prop(self, 'apply_matrix', toggle=False)
        layout.prop(self, 'concat_segments', toggle=False)
        row = layout.row(align=True)
        
        self.draw_obj_names(layout)

        if len(self.object_names)>0:
            row = layout.row(align=True)
            row.label(text='')
            self.wrapper_tracked_ui_draw_op(row, SvBezierInClearObjectsFromListMK2.bl_idname, text='', icon='CANCEL')

    def get_curve(self, spline, matrix):
        segments = []
        pairs = list(zip(spline.bezier_points, spline.bezier_points[1:]))
        if spline.use_cyclic_u:
            pairs = pairs + [(spline.bezier_points[-1], spline.bezier_points[0])]
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
            return points, tilt_values, radius_values, concatenate_curves(segments), spline.use_cyclic_u
        else:
            for p1, p2 in pairs:
                tilt_values.append([p1.tilt, p2.tilt])
                radius_values.append([p1.radius, p2.radius])
            points_by_segments = [[[p] for p in cp] for cp in points]
            return points_by_segments, tilt_values, radius_values, segments, spline.use_cyclic_u

    def process(self):

        if not self.object_names:
            return

        curves_out = []
        use_cyclic_u_out = []
        matrices_out = []
        controls_out = []
        control_points_c0_out = []
        control_points_c1_out = []
        control_points_c2_out = []
        control_points_c3_out = []
        tilt_out = []
        radius_out = []
        for item in self.object_names:
            object_name = item.name
            if item.exclude:
                continue
            obj = bpy.data.objects.get(object_name)
            if not obj:
                raise ValueError(f"{object_name} does not exists. Try exclude it from process (Pin button).")

            matrix = obj.matrix_world
            if obj.type != 'CURVE':
                self.warning("%s: not supported object type: %s", object_name, obj.type)
                continue

            splines_curves       = []
            splines_use_cyclic_u = []
            #splines_controls     = []
            splines_controls_c0  = []
            splines_controls_c1  = []
            splines_controls_c2  = []
            splines_controls_c3  = []
            #spline_matrices     = []
            splines_tilt         = []
            splines_radius       = []
            if obj.data.splines:
                for spline in obj.data.splines:
                    if spline.type != 'BEZIER':
                        self.warning("%s: not supported spline type: %s", spline, spline.type)
                        continue
                    controls, tilt_values, radius_values, curve, use_cyclic_u = self.get_curve(spline, matrix)
                    n = len(tilt_values)
                    #tilt_ts = range(n)
                    #curve.tilt_pairs = list(zip(tilt_ts, tilt_values))
                    splines_curves.append(curve)
                    splines_use_cyclic_u.append(use_cyclic_u)
                    #spline_matrices.append(matrix)
                    #splines_controls.append(controls)
                    spline_controls_c0  = []
                    spline_controls_c1  = []
                    spline_controls_c2  = []
                    spline_controls_c3  = []
                    for segments_c in controls:
                        spline_controls_c0.append(segments_c[0])
                        spline_controls_c1.append(segments_c[1])
                        spline_controls_c2.append(segments_c[2])
                        spline_controls_c3.append(segments_c[3])
                    
                    splines_controls_c0.append(spline_controls_c0)
                    splines_controls_c1.append(spline_controls_c1)
                    splines_controls_c2.append(spline_controls_c2)
                    splines_controls_c3.append(spline_controls_c3)

                    splines_tilt.append(tilt_values)
                    splines_radius.append(radius_values)
                    pass
            else:
                splines_curves.append([])
                splines_use_cyclic_u.append([])
                splines_controls_c0.append([])
                splines_controls_c1.append([])
                splines_controls_c2.append([])
                splines_controls_c3.append([])

                splines_tilt.append([])
                splines_radius.append([])
                pass

            if self.source_curves_join_mode=='KEEP':
                curves_out.append(splines_curves)
                use_cyclic_u_out.append(splines_use_cyclic_u)
                matrices_out.append([matrix])
                control_points_c0_out.append(splines_controls_c0)
                control_points_c1_out.append(splines_controls_c1)
                control_points_c2_out.append(splines_controls_c2)
                control_points_c3_out.append(splines_controls_c3)
                tilt_out.append(splines_tilt)
                radius_out.append(splines_radius)
                pass
            elif self.source_curves_join_mode=='SEPARATE':

                for I, spline in enumerate(splines_curves):
                    splines_curves_I = splines_curves[I]
                    if self.concat_segments==True:
                        curves_out.append([splines_curves_I])
                        use_cyclic_u_out.append([splines_use_cyclic_u[I]])
                        matrices_out.append([matrix])
                        control_points_c0_out.append([splines_controls_c0[I]])
                        control_points_c1_out.append([splines_controls_c1[I]])
                        control_points_c2_out.append([splines_controls_c2[I]])
                        control_points_c3_out.append([splines_controls_c3[I]])
                        tilt_out.append([splines_tilt[I]])
                        radius_out.append([splines_radius[I]])
                    else:
                        for IJ, segment in enumerate( splines_curves_I ):
                            curves_out.append([segment])
                            use_cyclic_u_out.append(False) # [splines_use_cyclic_u[I]]) потому что сегмент всегда разомкнут
                            matrices_out.append([matrix])
                            control_points_c0_out.append([splines_controls_c0[I][IJ][0]])
                            control_points_c1_out.append([splines_controls_c1[I][IJ][0]])
                            control_points_c2_out.append([splines_controls_c2[I][IJ][0]])
                            control_points_c3_out.append([splines_controls_c3[I][IJ][0]])
                            tilt_out.append([splines_tilt[I]])
                            radius_out.append([splines_radius[I]])
                        pass
                pass
            else:
                pass
            pass

        self.outputs['Curves'].sv_set(curves_out)
        self.outputs['use_cyclic_u'].sv_set(use_cyclic_u_out)
        #self.outputs['ControlPoints'].sv_set(controls_out)
        self.outputs['control_points_c0'].sv_set(control_points_c0_out)
        self.outputs['control_points_c1'].sv_set(control_points_c1_out)
        self.outputs['control_points_c2'].sv_set(control_points_c2_out)
        self.outputs['control_points_c3'].sv_set(control_points_c3_out)
        self.outputs['Matrices'].sv_set(matrices_out)
        if 'Tilt' in self.outputs:
            self.outputs['Tilt'].sv_set(tilt_out)
        if 'Radius' in self.outputs:
            self.outputs['Radius'].sv_set(radius_out)

classes = [SvBezierInItemRemoveMK2, SvBezierInItemSelectObjectMK2, SvBezierInViewAlignMK2, SvBIDataCollectionMK2, SVBI_UL_NamesListMK2, SvBezierInMoveUpMK2, SvBezierInMoveDownMK2, SvBezierInAddObjectsFromSceneUpMK2, SvBezierInClearObjectsFromListMK2, SvBezierInCallbackOpMK2, SvBezierInHighlightAllObjectsInSceneMK2, SvBezierInNodeMK2]
register, unregister = bpy.utils.register_classes_factory(classes)