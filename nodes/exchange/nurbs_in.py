# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from mathutils import Vector

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.nodes_mixins.show_3d_properties import Show3DProperties
from sverchok.utils.sv_operator_mixins import SvGenericNodeLocator
from sverchok.data_structure import updateNode, zip_long_repeat, split_by_count
from sverchok.utils.curve import knotvector as sv_knotvector
from sverchok.utils.curve.nurbs import SvNurbsCurve
from sverchok.utils.surface.nurbs import SvNurbsSurface
from sverchok.dependencies import geomdl

if geomdl is not None:
    from geomdl import NURBS

class SvExNurbsInDataCollectionMK2(bpy.types.PropertyGroup):
    object_pointer: bpy.props.PointerProperty(
        name="object",
        type=bpy.types.Object
    )
    exclude: bpy.props.BoolProperty(
        description='Exclude from process',
    )

def get_object_data_curve_info(object_pointer):
    '''Is object exists, has NURBS info?'''
    object_exists        = None
    SURFACE_CURVE_object = None
    Nurbs_SURFACE        = None
    Nurbs_CURVE          = None

    if object_pointer:
        object_exists=True
        #if hasattr(object_pointer.data, 'splines'):
        if object_pointer.type in ['SURFACE', 'CURVE']:
            SURFACE_CURVE_object = True
            Nurbs_SURFACE        = False
            Nurbs_CURVE          = False
            if object_pointer.data.splines:
                splines = object_pointer.data.splines
                if splines:
                    for spline in splines:
                        if spline.type=='NURBS':
                            if object_pointer.type=='SURFACE':
                                Nurbs_SURFACE = True
                            elif object_pointer.type=='CURVE':
                                Nurbs_CURVE   = True
                            else:
                                pass
                        else:
                            pass
                        pass
                    pass
                pass
            else:
                SURFACE_CURVE_object = True
                Nurbs_SURFACE        = False
                Nurbs_CURVE          = False
                pass
            pass
        else:
            SURFACE_CURVE_object = False
            Nurbs_SURFACE        = False
            Nurbs_CURVE          = False
            pass
    else:
        object_exists=False

    return object_exists, SURFACE_CURVE_object, Nurbs_SURFACE, Nurbs_CURVE

class SvExNurbsInCallbackOpMK2(bpy.types.Operator, SvGenericNodeLocator):

    bl_idname = "node.sv_ex_nurbs_in_callback_mk2"
    bl_label = "Nurbs In Callback"
    bl_options = {'INTERNAL'}

    fn_name: bpy.props.StringProperty(default='')

    def sv_execute(self, context, node):
        """
        returns the operator's 'self' too to allow the code being called to
        print from self.report.
        """
        getattr(node, self.fn_name)(self)

class SvExNurbsIn_UL_NamesListMK2(bpy.types.UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        object_exists, SURFACE_CURVE_object, Nurbs_SURFACE, Nurbs_CURVE = get_object_data_curve_info(item.object_pointer)

        general_part_of_comments = '\n\nClick - On/off\nShift-Click - Reverse On/Off all items'
        grid = layout.grid_flow(row_major=False, columns=3, align=True)
        if item.object_pointer:
            if SURFACE_CURVE_object:
                pass
            else:
                # highlight row that is not surface or curve:
                grid.alert = True
        else:
            # highlight row that object does not exists:
            grid.alert = True

        # curve_object = True
        # bezier_object = True

        item_icon = "GHOST_DISABLED"
        if item.object_pointer:
            try:
                item_icon = 'OUTLINER_OB_' + item.object_pointer.type
            except:
                item_icon = "GHOST_DISABLED"
        item_base = len(str(len(data.object_names)))
        #grid.label(text=f'{index:0{item_base}d} {item.name} {",".join(chars)}', icon=item_icon)
        row1 = grid.row(align=True)
        row1.alignment = 'LEFT'

        row1.column(align=True).label(text=f'{index:0{item_base}d}')

        if data.object_names_ui_minimal:
            row1.label(text='', icon=item_icon)
            row1.label(text=item.object_pointer.name)
            #UI0.label(text='')
        else:
            grid.prop(item, 'object_pointer', text='')
            row2 = grid.row(align=True)
            row2.alignment='RIGHT'
            row2.alert = False
            if item.object_pointer and SURFACE_CURVE_object==True:
                op = row2.column(align=True).operator(SvNurbsInItemSelectObjectMK2.bl_idname, icon='CURSOR', text='', emboss=False)
                op.idx = index
            elif not item.object_pointer:
                # Object cannot be used
                op = row2.column(align=True).operator(SvNurbsInEmptyOperatorMK2.bl_idname, icon='BLANK1', text='', emboss=False)
                op.description_text = 'Object does not exists. Will be skipped from process'
            else:
                # Object cannot be used
                op = row2.column(align=True).operator(SvNurbsInEmptyOperatorMK2.bl_idname, icon='BLANK1', text='', emboss=False)
                op.description_text = 'Object is not compatible. Will be skipped from process'
                pass

            if item.object_pointer and SURFACE_CURVE_object==True:
                # all segments are BEZIER
                if item.exclude:
                    exclude_icon='CHECKBOX_DEHLT'
                    description_text = 'Object will be excluded from process'
                else:
                    exclude_icon='CHECKBOX_HLT'
                    description_text = 'Object will be processed'
                op = row2.column(align=True).operator(SvNurbsInItemEnablerMK2.bl_idname, icon=exclude_icon, text='', emboss=False)
                op.idx = index
                op.description_text = description_text+general_part_of_comments
            elif not item.object_pointer:
                # Object cannot be used
                op = row2.column(align=True).operator(SvNurbsInEmptyOperatorMK2.bl_idname, icon='BLANK1', text='', emboss=False)
                op.description_text = 'Object does not exists. Will be skipped from process'
            else:
                # Object cannot be used
                op = row2.column(align=True).operator(SvNurbsInEmptyOperatorMK2.bl_idname, icon='BLANK1', text='', emboss=False)
                op.description_text = 'Object is not compatible. Will be skipped from process'
                pass

            op = row2.column(align=True).operator(SvNurbsInItemRemoveMK2.bl_idname, icon='X', text='', emboss=False)
            op.idx = index
            op.description_text = 'Remove object from list.\n\nUse Shift to skip confirmation dialog.'

            duplicate_sign='BLANK1'
            if item.object_pointer and active_data.object_names[getattr(active_data, active_propname)].object_pointer==item.object_pointer:
                lst = [o for o in active_data.object_names if o.object_pointer and o.object_pointer==item.object_pointer]
                if len(lst)>1:
                    duplicate_sign='ONIONSKIN_ON'
            col = row2.column(align=True).column(align=True)
            col.alignment='RIGHT'
            col.label(text='', icon=duplicate_sign)
            col.scale_x=0

        return
    
    def filter_items(self, context, data, propname):

        object_names_ui_minimal = getattr(data, "object_names_ui_minimal", False)

        items = getattr(data, propname)

        flt_flags = []
        flt_neworder = []

        for item in items:
            if not object_names_ui_minimal:
                flt_flags.append(self.bitflag_filter_item)
                continue
            else:
                object_exists, SURFACE_CURVE_object, Nurbs_SURFACE, Nurbs_CURVE = get_object_data_curve_info(item.object_pointer)

                non_applicable_type = False
                if item.object_pointer and SURFACE_CURVE_object:
                    pass
                elif not item.object_pointer:
                    non_applicable_type = True
                else:
                    non_applicable_type = True

                ok = (
                    (not item.exclude) and
                    (item.object_pointer) and (not non_applicable_type)
                )
                flt_flags.append(self.bitflag_filter_item if ok else 0)

        return flt_flags, flt_neworder

class SvNurbsInEmptyOperatorMK2(bpy.types.Operator):
    '''Empty operator to fill empty cells in grid'''
    bl_idname = "node.sv_nurbsin_empty_operator_mk2"
    bl_label = ""

    description_text: bpy.props.StringProperty(default='')

    @classmethod
    def description(cls, context, properties):
        s = properties.description_text
        return s

    def invoke(self, context, event):
        return {'FINISHED'}

class SvNurbsInItemSelectObjectMK2(bpy.types.Operator):
    '''Select object as active in 3D Viewport.\n\nShift-Click - add object into current selection of objects in scene.'''
    bl_idname = "node.sv_nurbsin_item_select_object_mk2"
    bl_label = ""

    node_name: bpy.props.StringProperty(default='')
    tree_name: bpy.props.StringProperty(default='')  # all item types should have actual name of a tree
    fn_name  : bpy.props.StringProperty(default='')
    idx      : bpy.props.IntProperty(default=0)

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

class SvNurbsInItemEnablerMK2(bpy.types.Operator):
    '''Enable/Disable object to process.\nCtrl button to disable all objects first\nShift button to inverse list.'''
    bl_idname = "node.sv_nurbsin_item_enabler_mk2"
    bl_label = ""

    fn_name         : bpy.props.StringProperty(default='')
    idx             : bpy.props.IntProperty()
    description_text: bpy.props.StringProperty(default='')

    @classmethod
    def description(cls, context, properties):
        s = properties.description_text
        return s

    def invoke(self, context, event):
        #node = context.node.object_names[self.idx]
        if self.idx <= len(context.node.object_names)-1:
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

class SvNurbsInItemRemoveMK2(bpy.types.Operator):
    '''Remove object from list'''
    bl_idname = "node.sv_nurbsin_item_remove_mk2"
    bl_label = ""

    idx             : bpy.props.IntProperty(default=0)
    description_text: bpy.props.StringProperty(default='')
    node_group      : bpy.props.StringProperty(default='')
    node_name       : bpy.props.StringProperty(default='')

    @classmethod
    def description(cls, context, properties):
        s = properties.description_text
        return s
    
    def draw(self, context):
        layout = self.layout
        layout.label(text=f'{self.node_name}.')
        layout.label(text=f'Remove object \'{self.idx}\'-th elem from list?')

    def invoke(self, context, event):
        if self.idx <= len(context.node.object_names)-1:
            self.node_name = context.node.name
            self.node_group = context.annotation_data_owner.name_full
            if event.shift==True:
                return self.execute(context)
            else:
                return context.window_manager.invoke_props_dialog(self)
        return {'FINISHED'}
    
    def execute(self, context):
        node = bpy.data.node_groups[self.node_group].nodes[self.node_name]
        node.object_names.remove(self.idx)
        node.process_node(None)
        self.report({'INFO'}, f"Removed {self.idx}-th item from list")
        return {'FINISHED'}
    
class SvNurbsInAddObjectsFromSceneUpMK2(bpy.types.Operator, SvGenericNodeLocator):

    bl_idname = "node.sv_nurbsin_add_object_from_scene_mk2"
    bl_label = "Add selected objects from scene into the list"
    bl_options = {'INTERNAL'}

    def sv_execute(self, context, node):
        node.add_objects_from_scene(self)
        pass

class SvNurbsInMoveUpMK2(bpy.types.Operator, SvGenericNodeLocator):

    bl_idname = "node.sv_nurbsin_moveup_mk2"
    bl_label = "Move current object up"
    bl_options = {'INTERNAL'}

    def sv_execute(self, context, node):
        node.move_current_object_up(self)
        return

class SvNurbsInMoveDownMK2(bpy.types.Operator, SvGenericNodeLocator):

    bl_idname = "node.sv_nurbsin_movedown_mk2"
    bl_label = "Move current object down"
    bl_options = {'INTERNAL'}

    def sv_execute(self, context, node):
        node.move_current_object_down(self)
        return

class SvNurbsInHighlightProcessedObjectsInSceneMK2(bpy.types.Operator, SvGenericNodeLocator):
    '''Select objects that marked as processed in this node. Use shift to append objects into a previous selected objects'''

    bl_idname = "node.sv_nurbsin_highlight_proc_objects_in_list_scene_mk2"
    bl_label = "Select processed objects in scene"

    fn_name: bpy.props.StringProperty(default='')

    def invoke(self, context, event):
        node = context.node
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                with context.temp_override(area = area , region = area.regions[-1]):
                    if event.shift==False:
                        for o in bpy.context.view_layer.objects:
                            o.select_set(False)
                    for item in node.object_names:
                        if item.object_pointer and item.exclude==False:
                            item.object_pointer.select_set(True)
                        pass
                    pass
                pass
            pass
        pass

        return {'FINISHED'}

class SvNurbsInHighlightAllObjectsInSceneMK2(bpy.types.Operator, SvGenericNodeLocator):
    '''Select objects that marked as processed in this node. Use shift to append objects into a previous selected objects'''
    bl_idname = "node.sv_nurbsin_highlight_all_objects_in_list_scene_mk2"
    bl_label = "Select all list's objects in 3D scene"

    fn_name: bpy.props.StringProperty(default='')

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

class SvNurbsInSyncSceneObjectWithListMK2(bpy.types.Operator, SvGenericNodeLocator):

    bl_idname = "node.sv_nurbsin_sync_scene_object_with_list"
    bl_label = ""
    bl_options = {'INTERNAL'}

    description_text: bpy.props.StringProperty(default='')

    @classmethod
    def description(cls, context, properties):
        s = properties.description_text
        return s

    def sv_execute(self, context, node):
        node.sync_active_object_in_scene_with_list(self)

class SvNurbsInRemoveDuplicatesObjectsInListMK2(bpy.types.Operator, SvGenericNodeLocator):

    bl_idname = "node.sv_nurbsin_remove_duplicates_objects_in_list"
    bl_label = ""
    bl_options = {'INTERNAL'}

    description_text: bpy.props.StringProperty(default='')
    node_group      : bpy.props.StringProperty(default='')
    node_name       : bpy.props.StringProperty(default='')

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

class SvNurbsInClearObjectsFromListMK2(bpy.types.Operator, SvGenericNodeLocator):

    bl_idname = "node.sv_nurbsin_clear_list_of_objects_mk2"
    bl_label = "Clear list of objects"
    bl_options = {'INTERNAL'}

    def sv_execute(self, context, node):
        node.clear_objects_from_list(self)
        return

class SvExNurbsInNodeMK2(Show3DProperties, SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Input NURBS
    Tooltip: Get NURBS curve or surface objects from scene
    """
    bl_idname = 'SvExNurbsInNodeMK2'
    bl_label = 'NURBS Input'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_OBJECTS_IN'
    is_scene_dependent = True
    is_animation_dependent = True

    
    legacy_mode: bpy.props.BoolProperty(
        name='Legacy Mode',
        description='Flats output lists (affects all sockets)',
        default=False,
        update=updateNode
        )
    
    object_names: bpy.props.CollectionProperty(type=SvExNurbsInDataCollectionMK2)
    active_obj_index: bpy.props.IntProperty()
    object_names_ui_minimal: bpy.props.BoolProperty(default=False, description='Minimize table view')

    sort: bpy.props.BoolProperty(
        name='sort by name',
        description='sorting inserted objects by names',
        default=True, update=updateNode)

    apply_matrix : bpy.props.BoolProperty(
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
            item = self.object_names.add()
            item.object_pointer = bpy.data.objects[name]

        if not self.object_names:
            ops.report({'WARNING'}, "Warning, no selected objects in the scene")
            return

        self.process_node(None)

    def draw_obj_names(self, layout):
        # display names currently being tracked, stop at the first 5..
        if self.object_names:
            remain = len(self.object_names) - 5

            # for i, obj_ref in enumerate(self.object_names):
            #     layout.label(text=obj_ref.name)
            #     if i > 4 and remain > 0:
            #         postfix = ('' if remain == 1 else 's')
            #         more_items = '... {0} more item' + postfix
            #         layout.label(text=more_items.format(remain))
            #         break

            row = layout.row(align=True)
            row.column().template_list("SvExNurbsIn_UL_NamesListMK2", f"uniq_{self.name}", self, "object_names", self, "active_obj_index")
            col = row.column(align=True)
            self.wrapper_tracked_ui_draw_op(col, SvNurbsInAddObjectsFromSceneUpMK2.bl_idname, text='', icon='ADD')
            self.wrapper_tracked_ui_draw_op(col, SvNurbsInMoveUpMK2.bl_idname, text='', icon='TRIA_UP')
            self.wrapper_tracked_ui_draw_op(col, SvNurbsInMoveDownMK2.bl_idname, text='', icon='TRIA_DOWN')
            self.wrapper_tracked_ui_draw_op(col, SvNurbsInHighlightProcessedObjectsInSceneMK2.bl_idname, text='', icon='GROUP_VERTEX')
            self.wrapper_tracked_ui_draw_op(col, SvNurbsInHighlightAllObjectsInSceneMK2.bl_idname, text='', icon='OUTLINER_OB_POINTCLOUD')
            self.wrapper_tracked_ui_draw_op(col, SvNurbsInSyncSceneObjectWithListMK2.bl_idname, icon='TRACKING_BACKWARDS_SINGLE', text='', emboss=True, description_text = 'Select the scene active object in list\n(Cycle between duplicates if there are any)')

            set_object_names = set([o.object_pointer.name for o in self.object_names if o.object_pointer])
            if len(set_object_names)<len(self.object_names):
                icon = 'AUTOMERGE_ON'
                description_text = f'Remove any duplicates objects in list\nCount of duplicates objects: {len(self.object_names)-len(set_object_names)}'
            else:
                icon = 'AUTOMERGE_OFF'
                description_text = 'Remove any duplicates objects in list.\nNo duplicates objects in list now'
            description_text += "\n\nShift-Cliсk - skip confirmation dialog"
            self.wrapper_tracked_ui_draw_op(col, SvNurbsInRemoveDuplicatesObjectsInListMK2.bl_idname, text='', icon=icon, description_text=description_text)
        else:
            layout.label(text='--None--')

    implementations = []
    if geomdl is not None:
        implementations.append(
            (SvNurbsCurve.GEOMDL, "Geomdl", "Geomdl (NURBS-Python) package implementation", 0))
    implementations.append(
        (SvNurbsCurve.NATIVE, "Sverchok", "Sverchok built-in implementation", 1))

    implementation : bpy.props.EnumProperty(
            name = "Implementation",
            items=implementations,
            update = updateNode)
    
    def add_objects_from_scene(self, ops):
        """Add selected objects on the top of the list"""
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
    
    def move_current_object_up(self, ops):
        """Move current obbect in list up"""

        if self.active_obj_index>0:
            self.object_names.move(self.active_obj_index, self.active_obj_index-1)
            self.active_obj_index-=1

        if not self.object_names:
            ops.report({'WARNING'}, "Warning, no selected objects in the scene")
            return

        self.process_node(None)
        return

    def move_current_object_down(self, ops):
        """Move current object in list down"""

        if self.active_obj_index<=len(self.object_names)-2:
            self.object_names.move(self.active_obj_index, self.active_obj_index+1)
            self.active_obj_index+=1

        self.process_node(None)
        return
    
    def sync_active_object_in_scene_with_list(self, ops):
        object_synced = False
        if bpy.context.view_layer.objects.active:
            active_object = bpy.context.view_layer.objects.active
            first_duplicated = None
            sync_index = None
            for I, item in enumerate(self.object_names):
                if self.object_names[self.active_obj_index].object_pointer == active_object and I<=self.active_obj_index:
                    if first_duplicated==None and self.object_names[I].object_pointer == active_object:
                        first_duplicated = I
                    continue
                if item.object_pointer == active_object:
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

    def remove_duplicates_objects_in_list(self, ops):
        lst = [item.object_pointer for item in self.object_names]
        _s = set(lst)
        remove_idx = []
        for I, item in enumerate(self.object_names):
            if item.object_pointer in _s:
                _s.remove(item.object_pointer)
            else:
                remove_idx.append(I)
            pass
        remove_idx.sort()
        remove_idx.reverse()
        for idx in remove_idx:
            self.object_names.remove(idx)
        ops.report({'INFO'}, f"removed {len(remove_idx)} object(s).")
        return
    
    def clear_objects_from_list(self, ops):
        """Clear list of objects"""
        len_object_names = len(self.object_names)
        self.object_names.clear()
        ops.report({'INFO'}, f"Cleared {len_object_names} items in the list.")
        self.process_node(None)
        return

    def sv_draw_buttons(self, context, layout):
        col = layout.column(align=True)
        col.alignment='RIGHT'
        #row = col.row(align=True)
        row = col.row()

        op_text = "Get selection"  # fallback
        if self.prefs_over_sized_buttons:
            row.scale_y = 4.0
            op_text = "G E T"

        callback = SvExNurbsInCallbackOpMK2.bl_idname
        self.wrapper_tracked_ui_draw_op(row, callback, text=op_text).fn_name = 'get_objects_from_scene'

        grid = layout.grid_flow(row_major=True, columns=2, align=True)
        c0 = grid.column()
        c0.alignment = 'RIGHT'
        c0.label(text='Sort:')
        grid.column().prop(self, 'sort', text='')
        c1 = grid.column()
        c1.alignment = 'RIGHT'
        c1.label(text='Implementation:')
        grid.column().prop(self, 'implementation', text='')
        c2 = grid.column()
        c2.alignment = 'RIGHT'
        c2.label(text='Apply matrixes:')
        grid.column().prop(self, 'apply_matrix', text='')
        c3 = grid.column()
        c3.alignment = 'RIGHT'
        c3.label(text='Legacy Mode:')
        grid.column().prop(self, 'legacy_mode', text='')


        # self.draw_obj_names(layout)

        # if len(self.object_names)>0:
        #     row = layout.row(align=True)
        #     row.label(text='')
        #     self.wrapper_tracked_ui_draw_op(row, SvNurbsInClearObjectsFromListMK2.bl_idname, text='', icon='CANCEL')

        if self.object_names:
            col = layout.column(align=True)
            elem = col.row(align=True)
            elem.alignment='RIGHT'
            self.wrapper_tracked_ui_draw_op(elem, SvNurbsInAddObjectsFromSceneUpMK2.bl_idname, text='', icon='ADD')
            self.wrapper_tracked_ui_draw_op(elem, SvNurbsInMoveUpMK2.bl_idname, text='', icon='TRIA_UP')
            self.wrapper_tracked_ui_draw_op(elem, SvNurbsInMoveDownMK2.bl_idname, text='', icon='TRIA_DOWN')
            self.wrapper_tracked_ui_draw_op(elem, SvNurbsInHighlightProcessedObjectsInSceneMK2.bl_idname, text='', icon='GROUP_VERTEX')
            self.wrapper_tracked_ui_draw_op(elem, SvNurbsInHighlightAllObjectsInSceneMK2.bl_idname, text='', icon='OUTLINER_OB_POINTCLOUD')
            self.wrapper_tracked_ui_draw_op(elem, SvNurbsInSyncSceneObjectWithListMK2.bl_idname, icon='TRACKING_BACKWARDS_SINGLE', text='', emboss=True, description_text = 'Select the scene active object in list\n(Cycle between duplicates if there are any)')
            
            set_object_names = set([o.name for o in self.object_names if o.object_pointer])
            if len(set_object_names)<len(self.object_names):
                icon = 'AUTOMERGE_ON'
                description_text = f'Remove any duplicates objects in list\nCount of duplicates objects: {len(self.object_names)-len(set_object_names)}'
            else:
                icon = 'AUTOMERGE_OFF'
                description_text = 'Remove any duplicates objects in list.\nNo duplicates objects in list now'
            description_text += "\n\nShift-Cliсk - skip confirmation dialog"
            self.wrapper_tracked_ui_draw_op(elem, SvNurbsInRemoveDuplicatesObjectsInListMK2.bl_idname, text='', icon=icon, description_text=description_text)
            elem.separator()
            self.wrapper_tracked_ui_draw_op(elem, SvNurbsInClearObjectsFromListMK2.bl_idname, text='', icon='CANCEL')
            elem.separator()
            if self.object_names_ui_minimal:
                elem.prop(self, "object_names_ui_minimal", text='', toggle=True, icon='FULLSCREEN_EXIT')
            else:
                elem.prop(self, "object_names_ui_minimal", text='', toggle=True, icon='FULLSCREEN_ENTER')

            col.template_list("SvExNurbsIn_UL_NamesListMK2", "", self, "object_names", self, "active_obj_index", rows=3)
            
        else:
            layout.label(text='--None--')

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, "draw_3dpanel", icon="PLUGIN")
        self.draw_buttons(context, layout)

    def draw_buttons_3dpanel(self, layout):
        row = layout.row(align=True)
        row.label(text=self.label if self.label else self.name)
        callback = SvExNurbsInCallbackOpMK2.bl_idname
        row.prop(self, 'implementation', text='')
        self.wrapper_tracked_ui_draw_op(row, callback, text='GET').fn_name = 'get_objects_from_scene'
        self.wrapper_tracked_ui_draw_op(row, "node.sv_nodeview_zoom_border", text="", icon="TRACKER_DATA")

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

        if not any([sock.is_linked for sock in self.outputs]):
            return

        if not self.object_names:
            return
        

        curves_out = []
        surfaces_out = []
        matrices_out = []
        for item in self.object_names:
            object_exists, SURFACE_CURVE_object, Nurbs_SURFACE, Nurbs_CURVE = get_object_data_curve_info(item.object_pointer)
            if item.object_pointer:
                if SURFACE_CURVE_object==True:
                    if item.exclude==False:
                        object_curves = []
                        object_surfaces = []
                        object_matrices = []
                        matrix = item.object_pointer.matrix_world
                        for spline in item.object_pointer.data.splines:
                            if spline.type != 'NURBS':
                                self.warning("%s: not supported spline type: %s", spline, spline.type)
                                continue
                            if item.object_pointer.type == 'SURFACE':
                                surface = self.get_surface(spline, matrix)
                                object_surfaces.append(surface)
                                object_matrices.append(matrix)
                            elif item.object_pointer.type == 'CURVE':
                                curve = self.get_curve(spline, matrix)
                                object_curves.append(curve)
                                object_matrices.append(matrix)
                            pass
                    else:
                        continue
                    pass
                    curves_out.append(object_curves)
                    surfaces_out.append(object_surfaces)
                    matrices_out.append(object_matrices)
                    pass
                else:
                    #if item.object_pointer.type not in {'SURFACE', 'CURVE'}:
                    self.warning("%s: not supported object type: %s", item.object_pointer.name, item.object_pointer.type)
                    continue
            else:
                continue
            pass
        pass

        _curves_out = curves_out
        _surfaces_out = surfaces_out
        _matrices_out = matrices_out
        if self.legacy_mode == True:
            _curves_out            = [c for   curves in _curves_out   for c in curves]
            _surfaces_out          = [s for surfaces in _surfaces_out for s in surfaces]
            _matrices_out          = [m for matrices in _matrices_out for m in matrices]

        self.outputs[  'Curves'].sv_set(_curves_out)
        self.outputs['Surfaces'].sv_set(_surfaces_out)
        self.outputs['Matrices'].sv_set(_matrices_out)

    def migrate_from(self, old_node):
        if hasattr(self, 'location_absolute'):
            # Blender 3.0 has no this attribute
            self.location_absolute = old_node.location_absolute
        for I, item in enumerate(old_node.object_names):
            if I<=len(self.object_names)-1:
                if hasattr(item, 'name') and item.name in bpy.data.objects:
                    self.object_names[I].object_pointer = bpy.data.objects[item.name]
        self.legacy_mode = True
        if self.width<305:
            self.width=305
        pass

classes = [
    SvNurbsInEmptyOperatorMK2,
    SvNurbsInItemSelectObjectMK2,
    SvNurbsInItemEnablerMK2,
    SvNurbsInItemRemoveMK2,
    SvNurbsInAddObjectsFromSceneUpMK2,
    SvNurbsInMoveUpMK2,
    SvNurbsInMoveDownMK2,
    SvNurbsInHighlightProcessedObjectsInSceneMK2,
    SvNurbsInHighlightAllObjectsInSceneMK2,
    SvNurbsInSyncSceneObjectWithListMK2,
    SvNurbsInRemoveDuplicatesObjectsInListMK2,
    SvNurbsInClearObjectsFromListMK2,
    SvExNurbsInDataCollectionMK2,
    SvExNurbsIn_UL_NamesListMK2,
    SvExNurbsInCallbackOpMK2,
    SvExNurbsInNodeMK2
]
register, unregister = bpy.utils.register_classes_factory(classes)