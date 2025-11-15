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
    object_pointer: bpy.props.PointerProperty(
        name="object",
        type=bpy.types.Object
    )
    #name: bpy.props.StringProperty()
    exclude: bpy.props.BoolProperty(
        description='Exclude from process',
    )
    #icon: bpy.props.StringProperty(default="BLANK1")


class ReadingBezierInDataError(Exception):
    pass

def get_object_data_spline_info(object_pointer):
    '''Is object exists, has spline and bezier info?'''
    object_exists=False
    curve_object = True
    bezier_object = False
    non_bezier_object = False
    chars = []

    if object_pointer:
        object_exists=True
        #obj = bpy.data.objects[object_name]
        if hasattr(object_pointer.data, 'splines'):
            #_set = set([s.type for s in obj.data.splines])
            
            if len(object_pointer.data.splines)>0:
                curve_object = True
                bezier_object = True
                splines = object_pointer.data.splines
                if splines:
                    for spline in splines:
                        if spline.type=='BEZIER':
                            bezier_object = True
                            chars.append(f"{len(spline.bezier_points)-1+(1 if spline.use_cyclic_u else 0)}{'c' if spline.use_cyclic_u else 'o'}")
                        else:
                            non_bezier_object = True
                            chars.append(f"{spline.type[0]}{'c' if spline.use_cyclic_u else 'o'}")
                        pass
                else:
                    chars=["[empty]"]
                pass
            else:
                curve_object = True
                bezier_object = False
                non_bezier_object = False
                chars.append("")
                pass
            pass
        else:
            curve_object = False
            bezier_object = False
            non_bezier_object = False
            chars.append("")
            pass

    return object_exists, curve_object, bezier_object, non_bezier_object, chars

class SVBI_UL_NamesListMK2(bpy.types.UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        general_part_of_comments = '\n\nClick - On/off\nShift-Click - Reverse On/Off all items'
        grid = layout.grid_flow(row_major=False, columns=6, align=True)

        object_exists=False
        curve_object = True
        bezier_object = True
        chars = []
        object_exists, curve_object, bezier_object, non_bezier_object, chars = get_object_data_spline_info(item.object_pointer)

        item_icon = "GHOST_DISABLED"
        if item.object_pointer:
            try:
                item_icon = 'OUTLINER_OB_' + item.object_pointer.type
            except:
                item_icon = "GHOST_DISABLED"
        item_base = len(str(len(data.object_names)))
        #grid.label(text=f'{index:0{item_base}d} {item.name} {",".join(chars)}', icon=item_icon)
        row1 = grid.row(align=True)
        row1.column(align=True).label(text=f'{index:0{item_base}d}')
        row1.label(text='', icon=item_icon)
        grid.prop(item, 'object_pointer', text='')

        if item.object_pointer:
            op = grid.operator(SvBezierInItemSelectObjectMK2.bl_idname, icon='CURSOR', text='', emboss=False)
            op.idx = index
        else:
            op = grid.operator(SvBezierInEmptyOperatorMK2.bl_idname, icon='BLANK1', text='', emboss=False)
            op.text='Object does not exists'
            pass

        if item.object_pointer and curve_object==True and bezier_object==True and non_bezier_object==False:
            # all segments are BEZIER
            if item.exclude:
                exclude_icon='CHECKBOX_DEHLT'
                description_text = 'Object will be excluded from process'
            else:
                exclude_icon='CHECKBOX_HLT'
                description_text = 'Object will be processed'
            op = grid.operator(SvBezierInItemEnablerMK2.bl_idname, icon=exclude_icon, text='', emboss=False)
            op.fn_name = 'ENABLER'
            op.idx = index
            op.description_text = description_text+general_part_of_comments

        elif item.object_pointer and curve_object==True and bezier_object==True and non_bezier_object==True:
            # Not all segments are BEZIER
            if item.exclude:
                exclude_icon='GHOST_DISABLED'
                description_text = 'Object will be excluded from process. Some splines of object are not BEZIER spline (ex.NURBS)'
            else:
                exclude_icon='GHOST_ENABLED'
                description_text = 'Object will be processed but some splines of object are not BEZIER spline (ex.NURBS)'
            op = grid.operator(SvBezierInItemEnablerMK2.bl_idname, icon=exclude_icon, text='', emboss=False)
            op.fn_name = 'ENABLER'
            op.idx = index
            op.description_text = description_text+general_part_of_comments

        elif not item.object_pointer:
            # Object does not exists
            op = grid.operator(SvBezierInEmptyOperatorMK2.bl_idname, icon='REMOVE', text='', emboss=False)
            op.text = 'Object does not exists'
            pass

        else:
            # Object cannot be used
            op = grid.operator(SvBezierInEmptyOperatorMK2.bl_idname, icon='REMOVE', text='', emboss=False)
            op.text = 'Object cannot be used as curve. Will be skipped in process.'
            pass

        op = grid.operator(SvBezierInItemRemoveMK2.bl_idname, icon='X', text='', emboss=False)
        op.fn_name = 'REMOVE'
        op.idx = index
        op.description_text = 'Remove object from list.\n\nUse Shift to skip confirmation dialog.'

        duplicate_sign='BLANK1'
        if item.object_pointer and active_data.object_names[getattr(active_data, active_propname)].object_pointer==item.object_pointer:
            lst = [o for o in active_data.object_names if o.object_pointer and o.object_pointer==item.object_pointer]
            if len(lst)>1:
                duplicate_sign='ONIONSKIN_ON'
        col = grid.column(align=True)
        col.label(text='', icon=duplicate_sign)
        col.scale_x=0

        return

class SvBezierInItemSelectObjectMK2(bpy.types.Operator):
    '''Select object as active in 3D Viewport.\n\nShift-Click - add object into current selection of objects in scene.'''
    bl_idname = "node.sv_bezierin_item_select_object_mk2"
    bl_label = ""

    node_name: bpy.props.StringProperty()
    tree_name: bpy.props.StringProperty()  # all item types should have actual name of a tree
    fn_name: StringProperty(default='')
    idx: IntProperty()

    def invoke(self, context, event):
        node = context.node
        if node:
            if self.idx>=0 and self.idx<=len(node.object_names)-1:
                object_pointer = node.object_names[self.idx].object_pointer
                if object_pointer:
                    for area in bpy.context.screen.areas:
                        if area.type == 'VIEW_3D':
                            with context.temp_override(area = area , region = area.regions[-1]):
                                if event.shift==False:
                                    # If you do not press Shift, drop the selection of all objects
                                    for o in bpy.context.view_layer.objects:
                                        o.select_set(False)
                                bpy.context.view_layer.objects.active = object_pointer
                                if object_pointer.select_get()==False:
                                    object_pointer.select_set(True)
                                #bpy.ops.view3d.view_selected(use_all_regions=False) # Иногда крашит Blender, пока отключил. Может вернусь позже. Оставлю пока только выделение объекта в сцене
                                break
            pass
        return {'FINISHED'}

class SvBezierInEmptyOperatorMK2(bpy.types.Operator):
    '''Empty operator to fill empty cells in grid'''
    bl_idname = "node.sv_bezierin_empty_operator_mk2"
    bl_label = ""

    text: StringProperty(default='')

    @classmethod
    def description(cls, context, properties):
        s = properties.text
        return s

    def invoke(self, context, event):
        return {'FINISHED'}

class SvBezierInItemRemoveMK2(bpy.types.Operator):
    '''Remove object from list'''
    bl_idname = "node.sv_bezierin_item_remove_mk2"
    bl_label = ""

    fn_name: StringProperty(default='')
    idx: IntProperty()
    description_text: StringProperty(default='')
    object_name: StringProperty(default='')
    node_group: StringProperty(default='')
    node_name: StringProperty(default='')

    @classmethod
    def description(cls, context, properties):
        s = properties.description_text
        return s
    
    def draw(self, context):
        layout = self.layout
        layout.label(text=f'{self.node_name}.')
        layout.label(text=f'Remove object \'{self.object_name}\' from list?')

    def invoke(self, context, event):
        if self.idx <= len(context.node.object_names)-1:
            if self.fn_name == 'REMOVE':
                object_pointer = context.node.object_names[self.idx].object_pointer
                if object_pointer:
                    self.object_name = context.node.object_names[self.idx].name
                    self.node_name = context.node.name
                    self.node_group = context.annotation_data_owner.name_full
                    if event.shift==True:
                        return self.execute(context)
                    else:
                        return context.window_manager.invoke_props_dialog(self)
                else:
                    self.report({'INFO'}, f"No object to remove")
        return {'FINISHED'}
    
    def execute(self, context):
        node = bpy.data.node_groups[self.node_group].nodes[self.node_name]
        node.object_names.remove(self.idx)
        node.process_node(None)
        self.report({'INFO'}, f"Removed \'{self.object_name}\' from list")
        return {'FINISHED'}

class SvBezierInItemEnablerMK2(bpy.types.Operator):
    '''Enable/Disable object to process.\nCtrl button to disable all objects first\nShift button to inverse list.'''
    bl_idname = "node.sv_bezierin_item_enabler_mk2"
    bl_label = ""

    fn_name: StringProperty(default='')
    idx: IntProperty()
    description_text: StringProperty(default='')

    @classmethod
    def description(cls, context, properties):
        s = properties.description_text
        return s

    def invoke(self, context, event):
        #node = context.node.object_names[self.idx]
        if self.idx <= len(context.node.object_names)-1:
            if self.fn_name == 'ENABLER':
                if event.ctrl==True:
                    for item in context.node.object_names:
                        item.exclude = True
                    context.node.object_names[self.idx].exclude = False
                elif event.shift==True:
                    for item in context.node.object_names:
                        item.exclude = not(item.exclude)
                        pass
                    pass
                else:
                    context.node.object_names[self.idx].exclude = not(context.node.object_names[self.idx].exclude)
                    pass
                context.node.process_node(None)
        return {'FINISHED'}

class SvBezierInCallbackOpMK2(bpy.types.Operator, SvGenericNodeLocator):
    '''Select objects from scene into this node. Objects selected erlier will be removed'''
    bl_idname = "node.sv_bezier_in_callback_mk2"
    bl_label = "Bezier In Callback mk2"
    bl_options = {'INTERNAL'}

    def sv_execute(self, context, node):
        """
        passes the operator's 'self' too to allow calling self.report()
        """
        node.get_objects_from_scene(self)

class SvBezierInSyncSceneObjectWithListMK2(bpy.types.Operator, SvGenericNodeLocator):

    bl_idname = "node.sv_bezierin_sync_scene_object_with_list"
    bl_label = ""
    bl_options = {'INTERNAL'}

    description_text: StringProperty(default='')

    @classmethod
    def description(cls, context, properties):
        s = properties.description_text
        return s

    def sv_execute(self, context, node):
        node.sync_active_object_in_scene_with_list(self)

class SvBezierInRemoveDuplicatesObjectsInListMK2(bpy.types.Operator, SvGenericNodeLocator):

    bl_idname = "node.sv_bezierin_remove_duplicates_objects_in_list"
    bl_label = ""
    bl_options = {'INTERNAL'}

    description_text: StringProperty(default='')
    node_group: StringProperty(default='')
    node_name: StringProperty(default='')

    @classmethod
    def description(cls, context, properties):
        s = properties.description_text
        return s
    
    def draw(self, context):
        layout = self.layout
        layout.label(text=f'{self.node_name}.')
        layout.label(text=f'Remove duplicates objects from list?')

    def invoke(self, context, event):
        self.node_name = context.node.name
        self.node_group = context.annotation_data_owner.name_full
        if event.shift==True:
            return self.execute(context)
        else:
            return context.window_manager.invoke_props_dialog(self)
    
    def execute(self, context):
        node = bpy.data.node_groups[self.node_group].nodes[self.node_name]
        node.remove_duplicates_objects_in_list(self)
        node.process_node(None)
        return {'FINISHED'}

    # def sv_execute(self, context, node):
    #     node.remove_duplicates_objects_in_list(self)

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
        node.move_current_object_up(self)
        return

class SvBezierInMoveDownMK2(bpy.types.Operator, SvGenericNodeLocator):

    bl_idname = "node.sv_bezierin_movedown_mk2"
    bl_label = "Move current object down"
    bl_options = {'INTERNAL'}

    def sv_execute(self, context, node):
        node.move_current_object_down(self)
        return

class SvBezierInClearObjectsFromListMK2(bpy.types.Operator, SvGenericNodeLocator):

    bl_idname = "node.sv_bezierin_clear_list_of_objects_mk2"
    bl_label = "Clear list of objects"
    bl_options = {'INTERNAL'}

    def sv_execute(self, context, node):
        node.clear_objects_from_list(self)
        return

# class SvBezierInViewAlignMK2(bpy.types.Operator, SvGenericNodeLocator):
#     """ Zoom to object """
#     bl_idname = "node.sv_bezierin_align_from_mk2"
#     bl_label = "Align 3dview to Object"

#     fn_name: bpy.props.StringProperty(default='')

#     def sv_execute(self, context, node):

#         if node.active_obj_index>=0 and node.active_obj_index<=len(node.object_names)-1:
#             object_name = node.object_names[node.active_obj_index].name
#             if object_name in bpy.data.objects:
#                 obj = bpy.data.objects[object_name]

#                 for area in bpy.context.screen.areas:
#                     if area.type == 'VIEW_3D':
#                         with context.temp_override(area = area , region = area.regions[-1]):
#                             for o in bpy.context.view_layer.objects:
#                                 o.select_set(False)
#                             bpy.context.view_layer.objects.active = obj
#                             if obj.select_get()==False:
#                                 obj.select_set(True)
#                             bpy.ops.view3d.view_selected(use_all_regions=False)
#                             pass
#                         pass
#                     pass
#                 pass
#             pass
#         pass
#         return {'FINISHED'}

class SvBezierInHighlightProcessedObjectsInSceneMK2(bpy.types.Operator, SvGenericNodeLocator):
    '''Select objects that marked as processed in this node. Use shift to append objects into a previous selected objects'''

    bl_idname = "node.sv_bezierin_highlight_proc_objects_in_list_scene_mk2"
    bl_label = "Select processed objects in scene"

    fn_name: StringProperty(default='')

    def invoke(self, context, event):
        node = context.node
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                with context.temp_override(area = area , region = area.regions[-1]):
                    if event.shift==False:
                        for o in bpy.context.view_layer.objects:
                            o.select_set(False)
                    for obj in node.object_names:
                        if obj.exclude==False and obj.name in bpy.data.objects:
                            bpy.data.objects[obj.name].select_set(True)
                        pass
                    pass
                pass
            pass
        pass

        return {'FINISHED'}


class SvBezierInHighlightAllObjectsInSceneMK2(bpy.types.Operator, SvGenericNodeLocator):
    '''Select objects that marked as processed in this node. Use shift to append objects into a previous selected objects'''
    bl_idname = "node.sv_bezierin_highlight_all_objects_in_list_scene_mk2"
    bl_label = "Select all list's objects in 3D scene"

    fn_name: StringProperty(default='')

    def invoke(self, context, event):
        node = context.node
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                with context.temp_override(area = area , region = area.regions[-1]):
                    if event.shift==False:
                        for o in bpy.context.view_layer.objects:
                            o.select_set(False)
                    for item in node.object_names:
                        if item.object_pointer:
                            item.object_pointer.select_set(True)
                        pass
                    pass
                pass
            pass
        pass
    
        return {'FINISHED'}


class SvBezierInNodeMK2(Show3DProperties, SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Input Bezier
    Tooltip: Get Bezier Curve objects from scene
    """
    bl_idname = 'SvBezierInNodeMK2'
    bl_label = 'Bezier Input'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_OBJECTS_IN'

    @property
    def is_scene_dependent(self):
        return self.object_names

    @property
    def is_animation_dependent(self):
        return self.object_names

    object_names: bpy.props.CollectionProperty(type=SvBIDataCollectionMK2)

    active_obj_index: bpy.props.IntProperty() # type: ignore

    source_curves_join_modes = [
            #('SPLIT', "Split", "Split/Separate the object curves into individual curves", 'MOD_OFFSET', 0),
            ('KEEP' , "Keep", "Keep curves as in source objects", 'SYNTAX_ON', 1),
            #('MERGE', "Merge", "Join all curves into a single object", 'STICKY_UVS_LOC', 2)
        ]

    source_curves_join_mode : EnumProperty(
        name = "",
        items = source_curves_join_modes,
        default = 'KEEP',
        update = updateNode) # type: ignore

    legacy_mode: BoolProperty(
        name='Legacy Mode',
        description='Flats output lists (affects all sockets)',
        default=False,
        update=updateNode
        )

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
        description = "If checked, join Bezier segments of the curve into a single Curve object; otherwise, output a separate Curve object for each segment. Recommended for experienced users.",
        default = True,
        update = updateNode)
    
    def draw_curves_out_socket(self, socket, context, layout):
        layout.alignment = 'RIGHT'
        flags = socket.get_mode_flags()
        s_flags = " [" + ",".join(flags) + "]" if flags else ''
        if socket.is_linked:
            layout.label(text=f"{socket.label}. {socket.objects_number or ''}"+s_flags)
        else:
            layout.label(text=f'{socket.label}')
        pass
    
    def sv_init(self, context):
        self.width = 300
        self.outputs.new('SvCurveSocket', 'Curves')
        self.outputs.new('SvStringsSocket', 'use_cyclic_u').label='Cyclic U'
        self.outputs.new('SvVerticesSocket', 'control_points_c0')
        self.outputs.new('SvVerticesSocket', 'control_points_c1')
        self.outputs.new('SvVerticesSocket', 'control_points_c2')
        self.outputs.new('SvVerticesSocket', 'control_points_c3')
        self.outputs.new('SvStringsSocket', 'Tilt')
        self.outputs.new('SvStringsSocket', 'Radius')
        self.outputs.new('SvStringsSocket', 'object_names').label='Object Names'
        self.outputs.new('SvMatrixSocket', 'Matrices')

        self.outputs["Curves"].label = 'Curves'
        self.outputs["Curves"].custom_draw = 'draw_curves_out_socket'

        self.outputs['control_points_c0'].label = "Controls Points c0"
        self.outputs['control_points_c1'].label = "Controls Points handle c1"
        self.outputs['control_points_c2'].label = "Controls Points handle c2"
        self.outputs['control_points_c3'].label = "Controls Points c3"
        return

    def remove_duplicates_objects_in_list(self, ops):
        lst = [s.name for s in self.object_names]
        _s = set(lst)
        remove_idx = []
        for I, item in enumerate(self.object_names):
            if item.name in _s:
                _s.remove(item.name)
            else:
                remove_idx.append(I)
            pass
        remove_idx.sort()
        remove_idx.reverse()
        for idx in remove_idx:
            self.object_names.remove(idx)
        ops.report({'INFO'}, f"removed {len(remove_idx)} object(s) ")
        return

    def sync_active_object_in_scene_with_list(self, ops):
        object_synced = False
        if bpy.context.view_layer.objects.active:
            active_object = bpy.context.view_layer.objects.active
            first_duplicated = None
            sync_index = None
            for I, item in enumerate(self.object_names):
                if self.object_names[self.active_obj_index].name == active_object.name and I<=self.active_obj_index:
                    if first_duplicated==None and self.object_names[I].name == active_object.name:
                        first_duplicated = I
                    continue
                if item.name == active_object.name:
                    sync_index = I
                    #object_synced = True
                    break
                pass

        if sync_index is not None:
            self.active_obj_index=sync_index
            object_synced = True
        elif first_duplicated is not None:
            self.active_obj_index=first_duplicated
            object_synced = True

        if object_synced:
            ops.report({'INFO'}, f"Object {active_object.name} synced.")
        else:
            ops.report({'WARNING'}, f"Object '{active_object.name}' is not in the list of objects")
        return

    def get_objects_from_scene(self, ops):
        """
        Collect selected objects
        """
        self.object_names.clear()

        names = [obj.name for obj in bpy.data.objects if (obj.select_get() and len(obj.users_scene) > 0 and len(obj.users_collection) > 0)]

        if self.sort:
            names.sort()

        for name in names:
            item = self.object_names.add()
            item.name = name
            item.object_pointer = bpy.data.objects[name]
            

        if not self.object_names:
            ops.report({'WARNING'}, "Warning, no selected objects in the scene")
            return
        else:
            ops.report({'INFO'}, f"Added {len(names)} object(s) into node {self.name}")

        self.process_node(None)
        return

    def add_objects_from_scene(self, ops):
        """
        Add selected objects on the top of the list
        """

        names = [obj.name for obj in bpy.data.objects if (obj.select_get() and len(obj.users_scene) > 0 and len(obj.users_collection) > 0)]

        for name in names:
            item = self.object_names.add()
            item.name = name
            item.object_pointer = bpy.data.objects[name]
            self.object_names.move(len(self.object_names)-1, 0)
            self.active_obj_index=0

        if not self.object_names:
            ops.report({'WARNING'}, "Warning, no selected objects in the scene")
            return
        else:
            ops.report({'INFO'}, f"Added {len(names)} object(s)")

        self.process_node(None)
        return

    def clear_objects_from_list(self, ops):
        """
        Clear list of objects
        """
        self.object_names.clear()
        self.process_node(None)
        return

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
        return

    def move_current_object_down(self, ops):
        """
        Move current object in list down
        """

        if self.active_obj_index<=len(self.object_names)-2:
            self.object_names.move(self.active_obj_index, self.active_obj_index+1)
            self.active_obj_index+=1

        self.process_node(None)
        return

    def draw_obj_names(self, layout):
        if self.object_names:
            row = layout.row(align=True)
            row.column().template_list("SVBI_UL_NamesListMK2", f"uniq_{self.name}", self, "object_names", self, "active_obj_index")
            col = row.column(align=True)
            self.wrapper_tracked_ui_draw_op(col, SvBezierInAddObjectsFromSceneUpMK2.bl_idname, text='', icon='ADD')
            self.wrapper_tracked_ui_draw_op(col, SvBezierInMoveUpMK2.bl_idname, text='', icon='TRIA_UP')
            self.wrapper_tracked_ui_draw_op(col, SvBezierInMoveDownMK2.bl_idname, text='', icon='TRIA_DOWN')
            self.wrapper_tracked_ui_draw_op(col, SvBezierInHighlightProcessedObjectsInSceneMK2.bl_idname, text='', icon='GROUP_VERTEX')
            self.wrapper_tracked_ui_draw_op(col, SvBezierInHighlightAllObjectsInSceneMK2.bl_idname, text='', icon='OUTLINER_OB_POINTCLOUD')
            self.wrapper_tracked_ui_draw_op(col, SvBezierInSyncSceneObjectWithListMK2.bl_idname, icon='TRACKING_BACKWARDS_SINGLE', text='', emboss=True, description_text = 'Select the scene active object in list\n(Cycle between duplicates if there are any)')

            set_object_names = set([o.name for o in self.object_names if o.object_pointer])
            if len(set_object_names)<len(self.object_names):
                icon = 'AUTOMERGE_ON'
                description_text = f'Remove any duplicates objects in list\nCount of duplicates objects: {len(self.object_names)-len(set_object_names)}'
            else:
                icon = 'AUTOMERGE_OFF'
                description_text = 'Remove any duplicates objects in list.\nNo duplicates objects in list now'
            description_text += "\n\nShift-Cliсk - skip confirmation dialog"
            self.wrapper_tracked_ui_draw_op(col, SvBezierInRemoveDuplicatesObjectsInListMK2.bl_idname, text='', icon=icon, description_text=description_text)
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
        layout.prop(self, 'legacy_mode')
        # layout.prop(self, 'concat_segments', toggle=False)
        row = layout.row(align=True)
        
        self.draw_obj_names(layout)

        if len(self.object_names)>0:
            row = layout.row(align=True)
            row.label(text='')
            self.wrapper_tracked_ui_draw_op(row, SvBezierInClearObjectsFromListMK2.bl_idname, text='', icon='CANCEL')

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, "concat_segments")
        self.draw_buttons(context, layout)

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

        if not any([sock.is_linked for sock in self.outputs]):
            return

        if not self.object_names:
            return

        curves_out = []
        use_cyclic_u_out = []
        object_names_out = []
        matrices_out = []
        controls_out = []
        control_points_c0_out = []
        control_points_c1_out = []
        control_points_c2_out = []
        control_points_c3_out = []
        tilt_out = []
        radius_out = []
        for item in self.object_names:
            #object_name = item.name
            if item.exclude:
                continue
            object_exists, curve_object, bezier_object, non_bezier_object, chars = get_object_data_spline_info(item.object_pointer)
            if not item.object_pointer or curve_object==False or bezier_object==False:
                continue
            
            if hasattr(item.object_pointer.data, 'splines')==False:
                continue

            matrix = item.object_pointer.matrix_world
            if item.object_pointer.type != 'CURVE':
                self.warning("%s: not supported object type: %s", item.object_pointer.name, item.object_pointer.type)
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
            if item.object_pointer.data.splines:
                for spline in item.object_pointer.data.splines:
                    if spline.type != 'BEZIER':
                        self.warning(f"{item.object_pointer.name}.{spline}: not supported spline type: {spline.type}")
                        continue
                    controls, tilt_values, radius_values, curve, use_cyclic_u = self.get_curve(spline, matrix)
                    splines_curves.append(curve)
                    splines_use_cyclic_u.append(use_cyclic_u)
                    spline_controls_c0  = []
                    spline_controls_c1  = []
                    spline_controls_c2  = []
                    spline_controls_c3  = []
                    for segments_c in controls:
                        spline_controls_c0.append(segments_c[0])
                        spline_controls_c1.append(segments_c[1])
                        spline_controls_c2.append(segments_c[2])
                        spline_controls_c3.append(segments_c[3])
                    
                    splines_controls_c0.append([spline_controls_c0])
                    splines_controls_c1.append([spline_controls_c1])
                    splines_controls_c2.append([spline_controls_c2])
                    splines_controls_c3.append([spline_controls_c3])
                    splines_tilt  .append(tilt_values)
                    splines_radius.append(radius_values)
                    pass
            else:
                # if splines are empty
                splines_curves.append([])
                splines_use_cyclic_u.append([])
                splines_controls_c0.append([])
                splines_controls_c1.append([])
                splines_controls_c2.append([])
                splines_controls_c3.append([])

                splines_tilt.append([])
                splines_radius.append([])
                pass

            if self.concat_segments==True:
                if self.source_curves_join_mode=='KEEP':
                    curves_out           .append(splines_curves)
                    use_cyclic_u_out     .append(splines_use_cyclic_u)
                    matrices_out         .append([matrix]*len(splines_curves))
                    object_names_out     .append([item.object_pointer.name]*len(splines_curves))
                    control_points_c0_out.append([co for lst in splines_controls_c0 for co in lst])
                    control_points_c1_out.append([co for lst in splines_controls_c1 for co in lst])
                    control_points_c2_out.append([co for lst in splines_controls_c2 for co in lst])
                    control_points_c3_out.append([co for lst in splines_controls_c3 for co in lst])
                    tilt_out             .append(splines_tilt)
                    radius_out           .append(splines_radius)
                    pass
                else:
                    raise Exception(f"mode {self.source_curves_join_mode} unused")
                    # for I, spline in enumerate(splines_curves):
                    #     splines_curves_I = splines_curves[I]
                    #     curves_out           .append([splines_curves_I])
                    #     use_cyclic_u_out     .append([splines_use_cyclic_u[I]])
                    #     object_names_out     .append([object_name])
                    #     matrices_out         .append([matrix])
                    #     control_points_c0_out.append(splines_controls_c0[I])
                    #     control_points_c1_out.append(splines_controls_c1[I])
                    #     control_points_c2_out.append(splines_controls_c2[I])
                    #     control_points_c3_out.append(splines_controls_c3[I])
                    #     tilt_out             .append([splines_tilt[I]])
                    #     radius_out           .append([splines_radius[I]])
                    #     pass
                    # pass
            else:
                if self.source_curves_join_mode=='KEEP':
                    curves_out           .append(splines_curves)
                    use_cyclic_u_out     .append(splines_use_cyclic_u)
                    matrices_out         .append([matrix]*len(splines_curves))
                    object_names_out     .append([item.object_pointer.name]*len(splines_curves))
                    spline_c0 = []
                    spline_c1 = []
                    spline_c2 = []
                    spline_c3 = []
                    for I in range(len(splines_controls_c0)):
                        splines_controls_c0_I = splines_controls_c0[I]
                        splines_controls_c1_I = splines_controls_c1[I]
                        splines_controls_c2_I = splines_controls_c2[I]
                        splines_controls_c3_I = splines_controls_c3[I]
                        spline_c0.append([co for controls in splines_controls_c0_I for co in controls])
                        spline_c1.append([co for controls in splines_controls_c1_I for co in controls])
                        spline_c2.append([co for controls in splines_controls_c2_I for co in controls])
                        spline_c3.append([co for controls in splines_controls_c3_I for co in controls])
                        pass
                    control_points_c0_out.append(spline_c0)
                    control_points_c1_out.append(spline_c1)
                    control_points_c2_out.append(spline_c2)
                    control_points_c3_out.append(spline_c3)
                    tilt_out             .append(splines_tilt)
                    radius_out           .append(splines_radius)
                    pass
                else:
                    raise Exception(f"mode {self.source_curves_join_mode} unused")
                    # for I, spline in enumerate(splines_curves):
                    #     splines_curves_I = splines_curves[I]
                    #     for IJ, segment in enumerate( splines_curves_I ):
                    #         curves_out           .append([segment])
                    #         use_cyclic_u_out     .append(False) # [splines_use_cyclic_u[I]]) потому что сегмент всегда разомкнут
                    #         matrices_out         .append([matrix]*len(splines_curves))
                    #         object_names_out     .append([object_name]*len(splines_curves))
                    #         control_points_c0_out.append([splines_controls_c0[I][IJ][0]])
                    #         control_points_c1_out.append([splines_controls_c1[I][IJ][0]])
                    #         control_points_c2_out.append([splines_controls_c2[I][IJ][0]])
                    #         control_points_c3_out.append([splines_controls_c3[I][IJ][0]])
                    #         tilt_out             .append([splines_tilt  [I][IJ]])
                    #         radius_out           .append([splines_radius[I][IJ]])
                    # pass
                pass
            pass

        _curves_out = curves_out
        _use_cyclic_u_out = use_cyclic_u_out
        _control_points_c0_out = control_points_c0_out
        _control_points_c1_out = control_points_c1_out
        _control_points_c2_out = control_points_c2_out
        _control_points_c3_out = control_points_c3_out
        _object_names_out = object_names_out
        _matrices_out = matrices_out
        _tilt_out = tilt_out
        _radius_out = radius_out

        if self.legacy_mode == True:
            _curves_out            = [c for curves in _curves_out            for c in curves]
            _use_cyclic_u_out      = [c for curves in _use_cyclic_u_out      for c in curves]
            _control_points_c0_out = [c for curves in _control_points_c0_out for c in curves]
            _control_points_c1_out = [c for curves in _control_points_c1_out for c in curves]
            _control_points_c2_out = [c for curves in _control_points_c2_out for c in curves]
            _control_points_c3_out = [c for curves in _control_points_c3_out for c in curves]
            _object_names_out      = [c for curves in _object_names_out      for c in curves]
            _matrices_out          = [c for curves in _matrices_out          for c in curves]
            _tilt_out              = [c for curves in _tilt_out              for c in curves]
            _radius_out            = [c for curves in _radius_out            for c in curves]
            

        

        self.outputs['Curves']           .sv_set(_curves_out)
        self.outputs['use_cyclic_u']     .sv_set(_use_cyclic_u_out)
        self.outputs['control_points_c0'].sv_set(_control_points_c0_out)
        self.outputs['control_points_c1'].sv_set(_control_points_c1_out)
        self.outputs['control_points_c2'].sv_set(_control_points_c2_out)
        self.outputs['control_points_c3'].sv_set(_control_points_c3_out)
        self.outputs['object_names']     .sv_set(_object_names_out)
        self.outputs['Matrices']         .sv_set(_matrices_out)
        if 'Tilt' in self.outputs:
            self.outputs['Tilt']         .sv_set(_tilt_out)
        if 'Radius' in self.outputs:
            self.outputs['Radius']       .sv_set(_radius_out)

    def migrate_from(self, old_node):
        if hasattr(self, 'location_absolute'):
            # Blender 3.0 has no this attribute
            self.location_absolute = old_node.location_absolute
        for I, item in enumerate(old_node.object_names):
            if I<=len(self.object_names)-1:
                if hasattr(item, 'name') and item.name in bpy.data.objects:
                    self.object_names[I].object_pointer = bpy.data.objects[item.name]

        pass

classes = [SvBezierInRemoveDuplicatesObjectsInListMK2,
        SvBezierInSyncSceneObjectWithListMK2,
        SvBezierInEmptyOperatorMK2,
        SvBezierInItemRemoveMK2,
        SvBezierInItemEnablerMK2,
        SvBezierInItemSelectObjectMK2,
        SvBIDataCollectionMK2,
        SVBI_UL_NamesListMK2,
        SvBezierInMoveUpMK2,
        SvBezierInMoveDownMK2,
        SvBezierInAddObjectsFromSceneUpMK2,
        SvBezierInClearObjectsFromListMK2,
        SvBezierInCallbackOpMK2,
        SvBezierInHighlightProcessedObjectsInSceneMK2,
        SvBezierInHighlightAllObjectsInSceneMK2,
        SvBezierInNodeMK2
    ]
register, unregister = bpy.utils.register_classes_factory(classes)