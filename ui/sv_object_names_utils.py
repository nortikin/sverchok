# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from sverchok.utils.sv_operator_mixins import SvGenericNodeLocator
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.utils.blender_mesh import read_materials_idx
import json

# object properties in Blender viewport -> Object Properties -> Viewport Display
prop_names = ['name', 'axis', 'wire', 'all_edges', 'texture_space', 'shadows', 'in_front']

def walk_collection(col, objs, visited_cols, use_sort_alpha):
    # recursion safe:
    if col in visited_cols:
        return
    visited_cols.add(col)

    if use_sort_alpha==False:
        # get objects in current collection
        _objs = []
        for obj in col.objects:
            # skip links
            if obj.library:
                continue

            # skip duplicated of objects
            if obj not in objs and obj not in _objs:
                _objs.append(obj)
            pass
        if use_sort_alpha==True:
            _objs = sorted(_objs, key=lambda o: o.name)
        objs.extend(_objs)

    # childer recursion
    for child in col.children:
        walk_collection(child, objs, visited_cols, use_sort_alpha)

    if use_sort_alpha==True:
        # get objects in current collection
        _objs = []
        for obj in col.objects:
            # skip links
            if obj.library:
                continue

            # skip duplicated of objects
            if obj not in objs and obj not in _objs:
                _objs.append(obj)
            pass
        if use_sort_alpha==True:
            _objs = sorted(_objs, key=lambda o: o.name)

        objs.extend(_objs)


def all_local_objects_recursive(root_collection, use_sort_alpha):
    '''return objects from collection and its childer without links and duplicated.'''
    objs = list()
    visited_cols = set()
    walk_collection(root_collection, objs, visited_cols, use_sort_alpha)
    return objs

def get_objects_of_collection(coll, use_sort_alpha):
    obj_coll = []
    
    # if False and hasattr(coll, 'children_recursive'):
    #     if use_sort_alpha==False:
    #         # objects before collections
    #         obj_coll.extend(coll.objects)

    #     for child in coll.children_recursive if use_sort_alpha==False else reversed(coll.children_recursive):
    #         if use_sort_alpha==True:
    #             obj_coll.extend(sorted(child.objects, key=lambda o: o.name))
    #         else:
    #             obj_coll.extend( list(child.objects))

    #     if use_sort_alpha==True:
    #         # objects after collections
    #         obj_coll.extend(sorted(list(coll.objects), key=lambda o: o.name))
    # else:
    #     obj_coll = all_local_objects_recursive(coll, True)
    #     obj_coll = list(obj_coll)
    #     pass

    # for compatibility with Blender 3.0 coll.children_recursive are not using
    obj_coll = all_local_objects_recursive(coll, True)
    obj_coll = list(obj_coll)
    return obj_coll

def get_objects_from_item(item):
    '''item - element of object_names table'''
    objs = []
    if item:
        if item.pointer_type=='OBJECT':
            if item.object_pointer:
                objs.append(item.object_pointer)
            pass
        elif item.pointer_type=='COLLECTION':
            if item.collection_pointer:
                # find outlines sort order:
                use_sort_alpha = True
                for area in bpy.context.window.screen.areas:
                    if area.type == 'OUTLINER':
                        space = area.spaces.active
                        use_sort_alpha = space.use_sort_alpha
                        break
                obj_coll = get_objects_of_collection(item.collection_pointer, use_sort_alpha)
                objs.extend(list(obj_coll))
            pass
        pass
    return objs

def get_objects_from_node(object_names, with_exclude=False):
    objs = []
    for o in object_names:
        if with_exclude==True and o.exclude==False or with_exclude==False:
            if o.pointer_type=='OBJECT':
                if o.object_pointer:
                    objs.append(o.object_pointer)
            elif o.pointer_type=='COLLECTION':
                if o.collection_pointer:
                    # find outlines sort order:
                    use_sort_alpha = True
                    for area in bpy.context.window.screen.areas:
                        if area.type == 'OUTLINER':
                            space = area.spaces.active
                            use_sort_alpha = space.use_sort_alpha
                            break
                    
                    obj_coll = get_objects_of_collection(o.collection_pointer, use_sort_alpha)
                    objs.extend(list(obj_coll))
    return objs

def get_pointers_from_node(object_names, with_exclude=False):
    objects_set = set()
    for item in object_names:
        if with_exclude==False or with_exclude==True and item.exclude==False:
            if item.pointer_type=='OBJECT':
                if item.object_pointer:
                    objects_set.add(item.object_pointer)
                pass
            elif item.pointer_type=='COLLECTION':
                if item.collection_pointer:
                    objects_set.add(item.collection_pointer)
                pass
            pass
    return objects_set

def ShowMessageBox(message = "", title = "Message Box", icon = 'INFO'):
    # The inner draw function defines the layout of the popup
    def draw(self, context):
        self.layout.label(text=message)
    
    # Call the popup_menu method from the window manager
    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)

class SvONDataCollectionMK4(bpy.types.PropertyGroup):
    '''One item of pointer to a Collection or an object'''
    pointer_types = [
            ('OBJECT'     , "Object"    , 'Use as Object Pointer', 0),
            ('COLLECTION' , "Collection", 'Use as collection Pointer', 1),
        ]
    # what type of pointer are using for this item. Do not change after initialize
    pointer_type : bpy.props.EnumProperty(
        name = "Pointer Type",
        default = 'OBJECT',
        description = "Pointer Type",
        items = pointer_types,
        #update = updateNode
        ) # type: ignore
    
    object_pointer: bpy.props.PointerProperty(
        name="object",
        type=bpy.types.Object
    )
    collection_pointer: bpy.props.PointerProperty(
        name="collection",
        type=bpy.types.Collection
    )
    icon   : bpy.props.StringProperty(default="BLANK1", options={'SKIP_SAVE'},)
    exclude: bpy.props.BoolProperty(
        default=False,
        description='Exclude from process',
    )

    # dynamic table element description: (appear on mouseover), but do not work on bpy.props.PointerProperty
    def _get_description(self):
        s = 'No object'
        if self.pointer_type=='OBJECT':
            if self.object_pointer:
                s = self.object_pointer.type
                object_pointer = self.object_pointer
                chars = [object_pointer.name]
                if object_pointer.type=='CURVE':
                    if object_pointer.data.splines:
                        splines = object_pointer.data.splines
                        for I, spline in enumerate(splines):
                            if spline.type=='BEZIER':
                                chars.append(f" {I}. {spline.type.lower()}, segments: {len(spline.bezier_points)-1+(1 if spline.use_cyclic_u else 0)}, {'closed' if spline.use_cyclic_u else 'open'}")
                            else:
                                chars.append(f" {I}. {spline.type.lower()}, segments: {len(spline.points)-1+(1 if spline.use_cyclic_u else 0)},{'closed' if spline.use_cyclic_u else 'open'}")
                            pass
                        pass
                    else:
                        chars.append("Curve object, No splines")
                        pass
                else:
                    # TODO: add another types: objects, collections, empty and other
                    objs = get_objects_from_item(self)
                    for obj in objs:
                        chars.append( f"{obj.type}, {obj.name}{' not in the scene' if obj.name not in bpy.context.scene.objects else ''}")
                    pass
                chars.append("---------------------")
                s = "\n".join(chars)
            else:
                pass
        elif self.pointer_type=='COLLECTION':
            if self.collection_pointer:
                chars = [f'Collection: {self.collection_pointer.name}']
                objs = get_objects_from_item(self)
                if objs:
                    chars.append("Members:  (Sorted Alphabetically as sorted view in Outliner. Members of collections are first)\n")
                for obj in objs:
                    chars.append( f"   {obj.type}, {obj.name}{': not in the scene' if obj.name not in bpy.context.scene.objects else ''}")
                chars.append("---------------------")
                s = "\n".join(chars)
            else:
                s = 'Collection is empty. Select collection.\n'
        else:
            pass

        return s
    
    test_text1: bpy.props.StringProperty(
        get=_get_description,
        options={'SKIP_SAVE'},
    )

class SvONSocketDataMK4(bpy.types.PropertyGroup):
    '''Custom properties Socket Info'''
    socket_types = [
            ('OBJECT'   , "Object"  , 'Object Custom Property'          , 'OBJECT_DATA', 0),
            ('DATA'     , "Data"    , 'Data Custom property'            , 'OUTLINER_DATA_MESH', 1),
            ('MATERIAL' , "Material", 'Material Custom Property'        , 'MATERIAL_DATA', 2),
            ('SOCKET'   , "Material", 'Only socket, no custom property' , 'QUESTION', 3),
        ]
    # what type of socket are using for this item.
    socket_type : bpy.props.EnumProperty(
        name = "Socket Type",
        default = 'OBJECT',
        description = "Socket Type",
        items = socket_types,
        #update = updateNode
        )
    socket_inner_name: bpy.props.StringProperty(
        name="Node Socket Inner Name",
    )
    custom_property_name: bpy.props.StringProperty(
        name="Custom Property Name",
        description="What custom property name",
    )
    socket_ui_name: bpy.props.StringProperty(
        name="Socket Name",
        description="Socket Name in UI",
    )
    socket_ui_label: bpy.props.StringProperty(
        name="Socket Label",
    )
    remove: bpy.props.BoolProperty(
        default=False,
        description='Remove socket',
    )

    # Определение свойств:
    #custom_property_name: bpy.props.StringProperty()
    custom_property_type            : bpy.props.StringProperty()
    custom_property_description     : bpy.props.StringProperty()
    custom_property_subtype         : bpy.props.StringProperty()
    custom_property_is_array        : bpy.props.BoolProperty()
    custom_property_array_size      : bpy.props.IntProperty(min=0, max=32)
    custom_property_min_str         : bpy.props.StringProperty()
    custom_property_max_str         : bpy.props.StringProperty()
    custom_property_min_float       : bpy.props.FloatProperty()
    custom_property_max_float       : bpy.props.FloatProperty()
    custom_property_min_int         : bpy.props.IntProperty()
    custom_property_max_int         : bpy.props.IntProperty()
    custom_property_min_bool        : bpy.props.BoolProperty()
    custom_property_max_bool        : bpy.props.BoolProperty()
    custom_property_default_str     : bpy.props.StringProperty()
    custom_property_default_float   : bpy.props.FloatVectorProperty(size=32)
    custom_property_default_int     : bpy.props.IntVectorProperty(size=32)
    custom_property_default_bool    : bpy.props.BoolVectorProperty(size=32)

class ReadingObjectDataError(Exception):
    pass

class SvONSwitchOffUnlinkedSocketsMK4(bpy.types.Operator):
    '''Hide all unlinked sockets'''
    bl_idname = "node.sv_on_switch_off_unlinked_sockets_mk4"
    bl_label = "Select object as active"
    description_text: bpy.props.StringProperty(default='Only hide unlinked output sockets.\nTo hide linked socket you have to unlink it first.')

    description_text: bpy.props.StringProperty(default='')
    node_group      : bpy.props.StringProperty(default='')
    node_name       : bpy.props.StringProperty(default='')

    @classmethod
    def description(cls, context, property):
        s = property.description_text
        return s

    def invoke(self, context, event):
        node = bpy.data.node_groups[self.node_group].nodes[self.node_name]
        #node = context.node
        if node:
            for s in node.outputs:
                if not s.is_linked:
                    s.hide = True
            pass
        return {'FINISHED'}


class SvONItemSelectObjectMK4(bpy.types.Operator):
    '''Select object as active in 3D Viewport. Use shift to add object into current selection of objects in scene.'''
    bl_idname = "node.sv_on_item_select_object_mk4"
    bl_label = "Select object as active"

    node_name: bpy.props.StringProperty(default='')
    tree_name: bpy.props.StringProperty(default='')  # all item types should have actual name of a tree
    fn_name  : bpy.props.StringProperty(default='')
    idx      : bpy.props.IntProperty(default=0)

    def invoke(self, context, event):
        node = context.node
        if node:
            if self.idx>=0 and self.idx<=len(node.object_names)-1:
                item = node.object_names[self.idx]
                objs = get_objects_from_item(item)
                for area in bpy.context.screen.areas:
                    if area.type == 'VIEW_3D':
                        if event.shift==False:
                            # Если Shift не нажат, то сбросить выделения всех объектов:
                            for o in bpy.context.view_layer.objects:
                                o.select_set(False)
                        for obj in objs:
                            if obj.name in bpy.context.view_layer.objects:
                                bpy.context.view_layer.objects.active = obj
                                if obj.select_get()==False:
                                    obj.select_set(True)
                            else:
                                self.report({'INFO'}, f"Object is not in the current scene")
                            #break
                    pass
                pass
            pass
        return {'FINISHED'}
    
class SvONItemEnablerMK4(bpy.types.Operator):
    '''Enable/Disable object to process.\nCtrl button to disable all objects first\nShift button to inverse list.'''
    bl_idname = "node.sv_on_item_enabler_mk4"
    bl_label = "Processed"

    fn_name: bpy.props.StringProperty(default='')
    idx    : bpy.props.IntProperty(default=0)

    def invoke(self, context, event):
        if self.idx <= len(context.node.object_names)-1:
            if self.fn_name == 'ENABLER':
                if event.ctrl==True:
                    for obj in context.node.object_names:
                        obj.exclude = True
                    context.node.object_names[self.idx].exclude = False
                elif event.shift==True:
                    for obj in context.node.object_names:
                        obj.exclude = not(obj.exclude)
                        pass
                    pass
                else:
                    context.node.object_names[self.idx].exclude = not(context.node.object_names[self.idx].exclude)
                    pass
                context.node.process_node(None)
        return {'FINISHED'}

class SvONItemEmptyOperatorMK4(bpy.types.Operator):
    '''Empty operator to fill empty cells in grid of object_names'''

    # example of usage to show dynamic description onmouseover:
    # op = row0.column(align=True).operator(SvONItemEmptyOperatorMK4.bl_idname, icon='BLANK1', text='', emboss=False)
    # op.description_text='Object pointer is empty'

    bl_idname = "node.sv_on_item_empty_operator_mk4"
    bl_label = ""

    fn_name         : bpy.props.StringProperty(default='')
    idx             : bpy.props.IntProperty(default=0)
    description_text: bpy.props.StringProperty(default='')

    @classmethod
    def description(cls, context, property):
        s = property.description_text
        return s
    
    def invoke(self, context, event):
        return {'FINISHED'}

class SvONItemRemoveMK4(bpy.types.Operator):
    '''Remove object from list'''
    bl_idname = "node.sv_on_item_remove_mk4"
    bl_label = "Remove"

    idx    : bpy.props.IntProperty(default=0)

    def invoke(self, context, event):
        #node = context.node.object_names[self.idx]
        if self.idx <= len(context.node.object_names)-1:
            o = context.node.object_names[self.idx]
            objs = get_objects_from_item(o)
            for o in objs:
                o.display_type = 'TEXTURED'
            context.node.object_names.remove(self.idx)
            context.node.process_node(None)
        return {'FINISHED'}

class SVON_UL_NamesListMK4(bpy.types.UIList):
    '''Show objects in list item with controls'''

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if item.pointer_type in ['OBJECT', 'COLLECTION']:
            item_icon = "GHOST_DISABLED"
            if item.pointer_type=='OBJECT' and item.object_pointer:
                try:
                    item_icon = 'OUTLINER_OB_' + item.object_pointer.type
                except:
                    ...
            elif item.pointer_type=='COLLECTION':
                item_icon = 'GROUP'

            _object_pointer = item.object_pointer if item.pointer_type=='OBJECT' else item.collection_pointer
            _pointer_prop_name = 'object_pointer' if item.pointer_type=='OBJECT' else 'collection_pointer'

            item_base = len(str(len(data.object_names)))

            grid = layout.grid_flow(row_major=False, columns=3, align=True)
            UI0 = grid.row(align=True)
            UI0.alignment = 'LEFT'
            if _pointer_prop_name=='object_pointer' and _object_pointer:
                object_in_scene = _object_pointer.name in bpy.context.scene.objects
                UI0.alert = not object_in_scene

            if hasattr(active_data, 'check_object_allowed')==True:
               active_data.check_object_allowed(UI0, item)

            UI01 = UI0.column(align=True)
            UI01.alignment = 'LEFT'
            UI01.label(text=f'{index:0{item_base}d}')
            if data.object_names_ui_minimal==True:
                UI02 = UI0.column(align=True)
                UI02.alignment = 'LEFT'
                UI02.label(text='', icon=item_icon)
            UI03 = UI0.row(align=True)
            if data.object_names_ui_minimal==False:
                usable = max(data.width - 160, 20)
                scale = usable/120
                UI03.scale_x = max(scale, 1.0)
                UI03.prop(item, _pointer_prop_name, text='')
            else:
                UI03.alignment = 'LEFT'
                UI03.label(text=_object_pointer.name)


            if data.object_names_ui_minimal:
                pass
            else:
                UI2=grid.row(align=True)
                UI2.alignment = 'RIGHT'

                if _object_pointer:
                    op = UI2.column(align=True).operator(SvONItemSelectObjectMK4.bl_idname, icon='CURSOR', text='', emboss=False)
                    op.idx = index
                else:
                    op = UI2.column(align=True).operator(SvONItemEmptyOperatorMK4.bl_idname, icon='BLANK1', text='', emboss=False)
                    op.description_text='Object pointer is empty'
                    pass
                if item.exclude:
                    exclude_icon='CHECKBOX_DEHLT'
                else:
                    exclude_icon='CHECKBOX_HLT'

                if _object_pointer:
                    op = UI2.column(align=True).operator(SvONItemEnablerMK4.bl_idname, icon=exclude_icon, text='', emboss=False)
                    op.fn_name = 'ENABLER'
                    op.idx = index
                else:
                    op = UI2.column(align=True).operator(SvONItemEmptyOperatorMK4.bl_idname, icon='BLANK1', text='', emboss=False)
                    op.description_text='Object pointer is empty'
                    pass
                
                op = UI2.column(align=True).operator(SvONItemRemoveMK4.bl_idname, icon='X', text='', emboss=False)
                op.idx = index

                # find duplicated (objects or collection names)
                duplicate_sign='BLANK1'
                active_index = getattr(active_data, active_propname)
                if active_index<=len(active_data.object_names)-1:
                    # Find duplicates of items with collections content
                    active_item = active_data.object_names[active_index]
                    if active_item.pointer_type=='OBJECT':
                        objs = get_objects_from_node(active_data.object_names)
                        lst = [o for o in objs if o==active_item.object_pointer]
                        if len(lst)>1:
                            objs_item = get_objects_from_item(item)
                            if active_item.object_pointer in objs_item:
                                duplicate_sign='ONIONSKIN_ON'
                        pass
                    elif active_item.pointer_type=='COLLECTION':
                        # find duplicates of collection names (only names, not intersections of content)
                        if active_item.collection_pointer:
                            collections_names = []
                            if item.pointer_type=='COLLECTION':
                                for item1 in active_data.object_names:
                                        if item1.collection_pointer and item1.collection_pointer == active_item.collection_pointer:
                                            collections_names.append( item1.collection_pointer.name )
                                if len(collections_names)>1 and item.collection_pointer==active_item.collection_pointer:
                                    duplicate_sign='ONIONSKIN_ON'
                            pass
                        pass
                col = UI2.column(align=True).column(align=True)
                col.label(text='', icon=duplicate_sign)
                col.scale_x=0
            pass
        else:
            pass
        pass

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
                ok = (
                    (not item.exclude) and
                    ((item.object_pointer and item.pointer_type=='OBJECT' and (item.object_pointer.name in bpy.context.scene.objects)) or
                     (item.collection_pointer and item.pointer_type=='COLLECTION'))
                )
                flt_flags.append(self.bitflag_filter_item if ok else 0)

        return flt_flags, flt_neworder


class SvONItemOperatorMK4(bpy.types.Operator, SvGenericNodeLocator):

    bl_idname = "node.sv_on_collection_operator_mk4"
    bl_label = "generic bladibla"

    fn_name: bpy.props.StringProperty(default='')
    idx    : bpy.props.IntProperty()

    def sv_execute(self, context, node):
        if self.fn_name == 'REMOVE':
            node.object_names.remove(self.idx)
        node.process_node(None)

class SvONAddObjectsFromSceneUpMK4(bpy.types.Operator, SvGenericNodeLocator):
    '''Select objects in 3DView and add them into current list.'''
    bl_idname = "node.sv_on_add_objects_from_scene_up_mk4"
    bl_label = "Add selected objects from scene into the list"
    bl_options = {'INTERNAL'}

    def sv_execute(self, context, node):
        '''passes the operator's 'self' too to allow calling self.report()'''
        node.add_objects_from_scene(self)

class SvONAddEmptyCollectionMK4(bpy.types.Operator, SvGenericNodeLocator):
    '''Select collection after'''
    bl_idname = "node.sv_on_add_empty_collection_mk4"
    bl_label = "Add empty collection into the list"
    bl_options = {'INTERNAL'}

    def sv_execute(self, context, node):
        '''passes the operator's 'self' too to allow calling self.report()'''
        node.add_empty_collection(self)

class SvONItemMoveUpMK4(bpy.types.Operator, SvGenericNodeLocator):
    '''Move item in object_names list'''
    bl_idname = "node.sv_on_item_moveup_mk4"
    bl_label = "Move current object up"
    bl_options = {'INTERNAL'}

    def sv_execute(self, context, node):
        '''passes the operator's 'self' too to allow calling self.report()'''
        node.move_current_object_up(self)

class SvONItemMoveDownMK4(bpy.types.Operator, SvGenericNodeLocator):
    '''Move item in object_names list'''
    bl_idname = "node.sv_on_item_movedown_mk4"
    bl_label = "Move current object down"
    bl_options = {'INTERNAL'}

    def sv_execute(self, context, node):
        '''passes the operator's 'self' too to allow calling self.report()'''
        node.move_current_object_down(self)

class SvONClearObjectsFromListMK4(bpy.types.Operator, SvGenericNodeLocator):
    '''Clear items in object_names list'''
    bl_idname = "node.sv_on_clear_objects_from_list_mk4"
    bl_label = "Clear list of objects"
    bl_options = {'INTERNAL'}

    def sv_execute(self, context, node):
        '''passes the operator's 'self' too to allow calling self.report()'''
        node.clear_objects_from_list(self)

class SvONLoadActiveObjectCustomPropertiesMK4(bpy.types.Operator, SvGenericNodeLocator):
    '''Clear items in object_names list'''
    bl_idname = "node.sv_on_load_active_object_custom_properties_mk4"
    bl_label = "Load Custom Properties"
    bl_options = {'INTERNAL'}

    def sv_execute(self, context, node):
        '''passes the operator's 'self' too to allow calling self.report()'''
        node.load_active_objects_custom_properties(self)

class SvONHighlightProcessedObjectsInSceneMK4(bpy.types.Operator, SvGenericNodeLocator):
    '''Select objects that marked as processed in this node. Use shift to append objects into a previous selected objects'''
    bl_idname = "node.sv_on_highlight_proc_objects_in_list_scene_mk4"
    bl_label = "Highlight processed objects in scene"

    def invoke(self, context, event):
        node = context.node
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                if event.shift==False:
                    for o in bpy.context.view_layer.objects:
                        o.select_set(False)
                some_objects_not_in_the_scene = False
                objs = get_objects_from_node(node.object_names, with_exclude=True)
                for item in objs:
                    if item:
                        if item.name in bpy.context.view_layer.objects:
                            item.select_set(True)
                        else:
                            some_objects_not_in_the_scene = True
                    pass
                pass
                if some_objects_not_in_the_scene == True:
                    self.report({'INFO'}, f"Some objects are not in the current scene")
                pass
            pass
        pass
        return {'FINISHED'}


class SvONHighlightAllObjectsInSceneMK4(bpy.types.Operator, SvGenericNodeLocator):
    '''Select all objects in this node.'''
    bl_idname = "node.sv_on_highlight_all_objects_in_list_scene_mk4"
    bl_label = "Select all objects in scene"

    fn_name: bpy.props.StringProperty(default='')

    def invoke(self, context, event):
        node = context.node
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                if event.shift==False:
                    for o in bpy.context.view_layer.objects:
                        o.select_set(False)
                some_objects_not_in_the_scene = False
                objs = get_objects_from_node(node.object_names)
                for item in objs:
                    if item:
                        if item.name in bpy.context.view_layer.objects:
                            item.select_set(True)
                        else:
                            some_objects_not_in_the_scene = True
                    pass
                pass
                if some_objects_not_in_the_scene == True:
                    self.report({'INFO'}, f"Some objects are not in the current scene")
                pass
            pass
        pass

        return {'FINISHED'}

class SvONSyncSceneObjectWithListMK4(bpy.types.Operator, SvGenericNodeLocator):

    bl_idname = "node.sv_on_sync_scene_object_with_list_mk4"
    bl_label = ""
    bl_options = {'INTERNAL'}

    description_text: bpy.props.StringProperty(default='')

    @classmethod
    def description(cls, context, properties):
        s = properties.description_text
        return s

    def sv_execute(self, context, node):
        node.sync_active_object_in_scene_with_list(self)

class SvONRemoveDuplicatesObjectsInListMK4(bpy.types.Operator, SvGenericNodeLocator):

    bl_idname = "node.sv_on_remove_duplicates_objects_in_list"
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

class SVON_localview_objectsInListMK4(bpy.types.Operator):
    bl_idname = "sv.localview_objects_in_listmk4"
    bl_label = '' #"Local View Selected"

    #frame_selected  : bpy.props.BoolProperty(default=False)
    local_view_mode : bpy.props.BoolProperty(default=False)
    description_text: bpy.props.StringProperty(default='')
    node_group      : bpy.props.StringProperty(default='')
    node_name       : bpy.props.StringProperty(default='')

    @classmethod
    def description(cls, context, properties):
        s = properties.description_text
        return s

    def execute(self, context):
        node = bpy.data.node_groups[self.node_group].nodes[self.node_name]
        objs = get_objects_from_node(node.object_names)
        # 1. Are objects in node exists?
        if not objs:
            self.report({'INFO'}, f"No objects in Node {node.name}")
            return {'CANCELLED'}

        # 2. Find 3D Viewport in current window
        win = context.window
        screen = win.screen

        # 2. Find 3D Viewport
        for area in screen.areas:
            if area.type != 'VIEW_3D':
                continue

            region = next((r for r in area.regions if r.type == 'WINDOW'), None)
            if region is None:
                continue

            space = area.spaces.active
            in_local = space.local_view is not None  # what local view mode?
            # if in_local==True and self.local_view_mode==True or in_local==False and self.local_view_mode==False:
            #     return {'CANCELLED'}
            
            # reset all selection
            for obj in bpy.context.selected_objects:
                obj.select_set(False)
            for obj in objs:
                obj.select_set(True)
            
            if hasattr(context, "temp_override"):
                # for Blender >=3.1
                with context.temp_override(
                    window=win,
                    screen=screen,
                    area=area,
                    region=region,
                    space_data=space,
                    scene=context.scene,
                    view_layer=context.view_layer,
                ):
                    bpy.ops.view3d.localview(frame_selected=node.frame_selected)
                self.report({'INFO'}, f"Local view is {'OFF' if in_local else 'ON'}")
                return {'FINISHED'}
            else:
                # --- Старый API (2.80–3.1) ---
                override = {
                    "window": win,
                    "screen": screen,
                    "area": area,
                    "region": region,
                    "space_data": space,
                    "scene": context.scene,
                    "view_layer": context.view_layer,
                }
                bpy.ops.view3d.localview(override, frame_selected=node.frame_selected)
                self.report({'INFO'}, f"Local view is {'OFF' if in_local else 'ON'}")
                return {'FINISHED'}

        self.report({'WARNING'}, "No 3D Viewport")
        return {'CANCELLED'}

def draw_properties(layout, node_group, node_name):
    node = bpy.data.node_groups[node_group].nodes[node_name]
    #layout.use_property_split = True https://blender.stackexchange.com/questions/161581/how-to-display-the-animate-property-diamond-keyframe-insert-button-2-8x
    root_grid = layout.grid_flow(row_major=False, columns=2, align=True)
    root_grid.alignment = 'EXPAND'
    grid1 = root_grid.grid_flow(row_major=False, columns=1, align=True)
    grid1.label(text='Viewport Display:')
    for n in prop_names:
        prop_name = "show_"+n
        grid1.prop(node, prop_name)
    grid1.label(text='')
    
    grid2 = grid1.grid_flow(row_major=True, columns=2, align=False)
    #grid2.alignment = 'RIGHT'

    row0 = grid2.row(align=True)
    row0.alignment = 'RIGHT'
    row0.label(text='Render Types:')
    grid2.row(align=True).prop(node, 'hide_render_type', expand=True, )

    row1 = grid2.row(align=True)
    row1.alignment = 'RIGHT'
    row1.label(text='Local View:')
    #grid2.row(align=True).prop(node, 'align_3dview_type', expand=True, )
    row11 = grid2.row(align=True)
    op1 = row11.operator(SVON_localview_objectsInListMK4.bl_idname, text='', icon='PIVOT_CURSOR')
    op1.local_view_mode = True
    op1.description_text = 'Turn Local View ON/OFF'
    op1.node_group = node_group
    op1.node_name  = node_name
    row11.prop(node, 'frame_selected', expand=True, icon='ZOOM_SELECTED', text='')
    

    row2 = grid2.row(align=True)
    row2.alignment = 'RIGHT'
    row2.label(text='Display Types:')
    grid2.row(align=True).prop(node, 'display_type', expand=True, text='1234')

    grid2 = root_grid.grid_flow(row_major=False, columns=1, align=True)
    grid2.label(text='Output Sockets:')
    row0 = grid2.row(align=True)
    row0.label(text='- socket is visible', icon='CHECKBOX_HLT')
    row0.label(text='- socket is hidden', icon='CHECKBOX_DEHLT')
    grid2.separator()
    row_op = grid2.row(align=True)
    row_op.alignment = "LEFT"
    op = row_op.operator(SvONSwitchOffUnlinkedSocketsMK4.bl_idname, icon='GP_CAPS_FLAT', text='Hide unlinked sockets', emboss=True)
    op.node_group = node_group
    op.node_name  = node_name

    for s in node.outputs:
        row = grid2.row(align=True)
        row.enabled = not s.is_linked
        row.prop(s, 'hide', text=f'{s.label if s.label else s.name}{" (linked)" if s.is_linked else ""}', invert_checkbox=True)

    row_op = grid2.row(align=True)
    row_op.alignment = "LEFT"
    op = row_op.operator(SvONSwitchOffUnlinkedSocketsMK4.bl_idname, icon='GP_CAPS_FLAT', text='Hide unlinked sockets', emboss=True)
    op.node_group = node_group
    op.node_name  = node_name
    pass

class SV_PT_ViewportDisplayPropertiesDialogMK4(bpy.types.Operator):
    '''Additional objects properties\nYou can pan dialog window out of node.'''
    # this combination do not show this panel on the right side panel
    bl_idname="sv.viewport_display_properties_dialog"
    bl_label = "Objects 3DViewport properties as Dialog Window."

    # horizontal size
    # bl_ui_units_x = 40 - Has no influence in Dialog mode

    description_text: bpy.props.StringProperty(default='')
    node_group      : bpy.props.StringProperty(default='')
    node_name       : bpy.props.StringProperty(default='')

    # def is_extended():
    #     return True

    def execute(self, context):
        return {'FINISHED'}
    
    def invoke(self, context, event):
        self.node_name = context.node.name
        self.node_group = context.annotation_data_owner.name_full
        return context.window_manager.invoke_props_dialog(self, width=500)

    def draw(self, context):
        draw_properties(self.layout, self.node_group, self.node_name)
        pass

class SvONCurrentObjectCustomPropertiesCollectionMK4(bpy.types.PropertyGroup):
    '''One item of pointer to a custom property'''
    name: bpy.props.StringProperty(default="", options={'SKIP_SAVE'},)
    apply: bpy.props.BoolProperty(
        default=False,
        description='Apply to all objects in node',
        options={'SKIP_SAVE'},
    )
    socket_type : bpy.props.EnumProperty(
        name = "Socket Type",
        default = 'OBJECT',
        description = "Socket Type",
        items = SvONSocketDataMK4.socket_types,
        #update = updateNode
    )
    value: bpy.props.StringProperty(default="", options={'SKIP_SAVE'},)

class SVON_UL_CurrentObjectCustomPropertiesListMK4(bpy.types.UIList):
    '''Show objects in list item with controls'''

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        # grid = layout.grid_flow(row_major=False, columns=3, align=True)
        # grid.column(align=True).prop(item, 'apply')
        # grid.column(align=True).label(text=item.name)
        # grid.column(align=True).label(text=item.value)

        row = layout.row(align=True)
        elem1 = row.split(factor=0.3)
        elem1.label(text=item.name, icon=[cp for cp in SvNodeInDataMK4.custom_properties_modes if item.socket_type==cp[0]][0][3])
        elem2 = elem1.split(factor=0.9)
        elem2.label(text=item.value)
        #elem1.column().prop(item, 'apply')
        row2 = elem2.row(align=True)
        row2.alignment='RIGHT'
        op = row2.operator(SvONCustomPropertyAddToOutputSocketMK4.bl_idname, icon='ADD', text='', emboss=True)
        op.node_name  = data.name
        op.node_group = context.annotation_data_owner.name_full
        op.idx = index
        op.socket_type = data.custom_properties_mode
        #op.socket_inner_name = unique_name
        op.custom_property_name = item.name
        op.socket_ui_name = item.name
        op.socket_ui_label = item.name

class SVON_UL_CustomPropertiesSocketsListMK4(bpy.types.UIList):
    '''Show custom properties sockets list'''

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)
        elem1 = row.split(factor=0.3)
        elem1.label(text=item.socket_type, icon=[cp for cp in SvNodeInDataMK4.custom_properties_modes if item.socket_type==cp[0]][0][3])
        elem2 = elem1.split(factor=0.6)
        elem2.label(text=item.socket_ui_name)
        row2 = elem2.row(align=True)
        row2.alignment='RIGHT'
        op = row2.operator(SvONCustomPropertySocketRemoveMK4.bl_idname, icon='X', text='', emboss=True)
        op.node_name  = data.name
        op.node_group = context.annotation_data_owner.name_full
        op.idx = index

class SV_PT_ViewportDisplayCustomPropertiesDialogMK4(bpy.types.Operator):
    '''Copy objects custom properties dialog\nYou can pan dialog window out of node.'''
    # this combination do not show this panel on the right side panel
    bl_idname="sv.viewport_display_custom_properties_dialog"
    bl_label = "Copy Objects custom properties into all objects in node"

    # horizontal size
    # bl_ui_units_x = 40 - Has no influence in Dialog mode

    description_text: bpy.props.StringProperty(default='')
    node_group      : bpy.props.StringProperty(default='')
    node_name       : bpy.props.StringProperty(default='')

    # dynamic table element description: (appear on mouseover), but do not work on bpy.props.PointerProperty
    def _get_description(self):
        s = 'TODO: return description'
        return s
    
    get_description: bpy.props.StringProperty(
        get=_get_description,
        options={'SKIP_SAVE'},
    )

    def execute(self, context):
        # Обработка 'OK':
        node = bpy.data.node_groups[self.node_group].nodes[self.node_name]
        return {'FINISHED'}
    
    def cancel(self, context):
        # Обработка 'Cancel':
        node = bpy.data.node_groups[self.node_group].nodes[self.node_name]
        pass
    
    def invoke(self, context, event):
        # Вызов диалогового окна копирования custom properties
        self.node_name = context.node.name
        self.node_group = context.annotation_data_owner.name_full
        node = bpy.data.node_groups[self.node_group].nodes[self.node_name]
        node.load_active_object_custom_properties()
        return context.window_manager.invoke_props_dialog(self, width=500)

    def draw(self, context):
        # Отображение настроек диалогового окна
        self.draw_custom_properties            (self.layout, self.node_group, self.node_name)
        self.draw_custom_properties_socket_info(self.layout, self.node_group, self.node_name)
        pass

    def draw_custom_properties(self, layout, node_group, node_name):
        node = bpy.data.node_groups[node_group].nodes[node_name]
        #layout.use_property_split = True https://blender.stackexchange.com/questions/161581/how-to-display-the-animate-property-diamond-keyframe-insert-button-2-8x
        root_grid = layout.grid_flow(row_major=False, columns=2, align=True)
        root_grid.alignment = 'EXPAND'
        grid1 = root_grid.grid_flow(row_major=False, columns=1, align=True)
        grid1.label(text=f'Custom properties of object \'{node.active_object_name}\' ({node.active_object_type}):')
        r = grid1.row(align=True)
        r.alignment = 'LEFT'
        r.row(align=True).prop(node, 'custom_properties_mode', expand=True)

        if node.custom_properties_mode=='OBJECT':
            grid1.template_list("SVON_UL_CurrentObjectCustomPropertiesListMK4", f"uniq_active_object_custom_properties_object_{  self.name}", node, "active_object_custom_properties"         , node, "active_object_custom_properties_index"     , rows=3, item_dyntip_propname='get_description')
        elif node.custom_properties_mode=='DATA':
            grid1.template_list("SVON_UL_CurrentObjectCustomPropertiesListMK4", f"uniq_active_object_data_custom_properties_{    self.name}", node, "active_object_data_custom_properties"    , node, "active_object_data_custom_properties_index", rows=3, item_dyntip_propname='get_description')
        elif node.custom_properties_mode=='MATERIAL':
            grid1.template_list("SVON_UL_CurrentObjectCustomPropertiesListMK4", f"uniq_active_object_material_custom_properties_{self.name}", node, "active_object_material_custom_properties", node, "active_object_material_custom_properties_index"   , rows=3, item_dyntip_propname='get_description')
        pass

    def draw_custom_properties_socket_info(self, layout, node_group, node_name):
        node = bpy.data.node_groups[node_group].nodes[node_name]
        row = layout.row(align=True)
        row.column(align=True).label(text="Custom Properties sockets:")
        node.wrapper_tracked_ui_draw_op(row, SvONCustomPropertySocketMoveUpMK4.bl_idname, text='', icon='TRIA_UP')
        node.wrapper_tracked_ui_draw_op(row, SvONCustomPropertySocketMoveDownMK4.bl_idname, text='', icon='TRIA_DOWN')
        grid1 = layout.grid_flow(row_major=False, columns=1, align=True)
        grid1.template_list("SVON_UL_CustomPropertiesSocketsListMK4", f"uniq_sockets_custom_properties_{self.name}", node, "custom_properties_sockets", node, "custom_properties_sockets_index", rows=3, ) # item_dyntip_propname='get_description')
        pass

class SvONCustomPropertySocketMoveUpMK4(bpy.types.Operator, SvGenericNodeLocator):
    '''Move Custom Property Socket up'''
    bl_idname = "node.sv_on_custom_property_socket_moveup_mk4"
    bl_label = "Move Custom Property Socket up"
    bl_options = {'INTERNAL'}

    def sv_execute(self, context, node):
        '''passes the operator's 'self' too to allow calling self.report()'''
        node.move_custom_property_socket_up(self)

class SvONCustomPropertySocketMoveDownMK4(bpy.types.Operator, SvGenericNodeLocator):
    '''Move Custom Property Socket down'''
    bl_idname = "node.sv_on_custom_property_socket_movedown_mk4"
    bl_label = "Move Custom Property Socket down"
    bl_options = {'INTERNAL'}

    def sv_execute(self, context, node):
        '''passes the operator's 'self' too to allow calling self.report()'''
        node.move_custom_property_socket_down(self)


class SvONCustomPropertySocketRemoveMK4(bpy.types.Operator):
    '''Remove Socket'''
    bl_idname = "node.sv_on_custom_property_socket_remove_mk4"
    bl_label = "Remove Socket?"
    bl_description = "Remove Socket from node"

    node_group      : bpy.props.StringProperty(default='')
    node_name       : bpy.props.StringProperty(default='')
    idx             : bpy.props.IntProperty(default=0)
    remove_objects_custom_property: bpy.props.BoolProperty(default=False, name='Remove custom property without active object', description='Remove custom property and keep  active object custom property') # Удалить custom property у всех объектов, кроме активного
    remove_active_object_custom_property: bpy.props.BoolProperty(default=False, name='Remove custom property of active object', description='Remove custom property of active object too') # Удалить custom property и у активного объекта тоже
    remove_active_object_active_material_custom_property: bpy.props.BoolProperty(default=False, name='Remove custom property of active object', description='Remove custom property of active object too') # Удалить custom property и у активного объекта тоже

    def invoke(self, context, event):
        self.remove_objects_custom_property = False
        self.remove_active_object_custom_property = False
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        node = bpy.data.node_groups[self.node_group].nodes[self.node_name]
        if self.idx <= len(node.custom_properties_sockets)-1:
            elem = node.custom_properties_sockets[self.idx]
            objs = node.get_objects(input_socket_name='objects')
            safe_materials = []
            if bpy.context.active_object and bpy.context.active_object.material_slots:
                obj = bpy.context.active_object
                safe_materials = dict([(id, dict(material_name=(None if obj.material_slots[id].material is None else obj.material_slots[id].material.name), material=(None if obj.material_slots[id].material is None else obj.material_slots[id].material),)) for id in range(len(obj.material_slots))])
            if self.remove_objects_custom_property==True:
                for obj in objs:
                    if elem.socket_type=='OBJECT':
                        if obj==bpy.context.active_object and self.remove_active_object_custom_property==False:
                            # Если активный объект не подлежит очистке, то пропустить очистку его свойств. 
                            continue
                        if elem.custom_property_name in obj:
                            del obj[elem.custom_property_name]
                            pass
                        pass
                    elif elem.socket_type=='DATA':
                        if bpy.context.active_object and bpy.context.active_object.data and bpy.context.active_object.data==obj.data and self.remove_active_object_custom_property==False:
                            # Если активный объект не подлежит очистве, то и его свойства
                            # в разных ссылках также не подлежат очистке 
                            continue
                        if obj.data:
                            if elem.custom_property_name in obj.data:
                                del obj.data[elem.custom_property_name]
                        pass
                    elif elem.socket_type=='MATERIAL':
                        if obj.material_slots:
                            # Получить список материалов объекта:
                            materials_info = dict([(id, dict(material_name=(None if obj.material_slots[id].material is None else obj.material_slots[id].material.name), material=(None if obj.material_slots[id].material is None else obj.material_slots[id].material),)) for id in range(len(obj.material_slots))])
                            for k in materials_info:
                                material_name = materials_info[k]['material_name']
                                if any(safe_materials[mat]['material_name']==material_name for mat in safe_materials) and self.remove_active_object_custom_property==False:
                                    # Если материал из списка материалов активного объекта и
                                    # активный объект не подлежит очистке, то и его материалы не подлежат
                                    # очистке, даже если они используются в других объектах 
                                    continue
                                mi = materials_info[k]['material']
                                if mi and elem.custom_property_name in mi:
                                    del mi[elem.custom_property_name]
                                pass
                            pass
                        pass
                pass
            socket_inner_name = node.custom_properties_sockets[self.idx].socket_inner_name
            node.custom_properties_sockets.remove(self.idx)
            if socket_inner_name in node.outputs:
                s = node.outputs[socket_inner_name]
                node.outputs.remove(s)


            #context.node.process_node(None)
        return {'FINISHED'}
    
    def draw(self, context):
        self.layout.prop(self, 'remove_objects_custom_property')
        self.layout.prop(self, 'remove_active_object_custom_property')
        pass

class SvONCustomPropertyAddToOutputSocketMK4(bpy.types.Operator):
    '''Add Custom Property to Output Socket'''
    bl_idname = "node.sv_on_custom_property_add_to_output_socket_mk4"
    bl_label = "Add Socket?"
    bl_description = "Add Custom Property to Output Socket of node and copy custom property to all objects of node too"

    node_group      : bpy.props.StringProperty(default='')
    node_name       : bpy.props.StringProperty(default='')
    idx             : bpy.props.IntProperty(default=0)

    socket_type : bpy.props.EnumProperty(
        name = "Socket Type",
        default = 'OBJECT',
        description = "Socket Type",
        items = SvONSocketDataMK4.socket_types,
        )
    socket_inner_name: bpy.props.StringProperty(
        name="Node Socket Inner Name",
    )
    custom_property_name: bpy.props.StringProperty(
        name="Custom Property Name",
        description="What custom property name",
    )
    socket_ui_name: bpy.props.StringProperty(
        name="Socket Name",
        description="Socket Name in UI",
    )
    socket_ui_label: bpy.props.StringProperty(
        name="Socket Label",
    )

    def invoke(self, context, event):
        node = bpy.data.node_groups[self.node_group].nodes[self.node_name]
        res, message_text, message_title, message_icon = node.custom_property_add_to_output_socket_invoke(self.socket_type, self.socket_inner_name, self.custom_property_name, self.socket_ui_name, self.socket_ui_label, self.idx)
        if res!='FINISHED':
            ShowMessageBox(message_text, message_title, message_icon)
            return {res}

        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        # Проверить, а не создан ли уже для этого параметра сокет:
        node = bpy.data.node_groups[self.node_group].nodes[self.node_name]
        res, message_type, message_text = node.custom_property_add_to_output_socket_execute(self.socket_type, self.socket_inner_name, self.custom_property_name, self.socket_ui_name, self.socket_ui_label, self.idx)
        if res!='FINISHED':
            self.report({message_type}, message_text)
        return {res}

class SV_PT_ViewportDisplayPropertiesMK4(bpy.types.Panel):
    '''Additional objects properties'''
    # this combination do not show this panel on the right side panel
    bl_idname="SV_PT_ViewportDisplayPropertiesMK4"
    bl_label = "Objects 3DViewport properties"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'

    # @classmethod
    # def description(cls, context, properties):
    #     s = "properties.description_text"
    #     return s

    # horizontal size
    bl_ui_units_x = 22

    def draw(self, context):
        if hasattr(context, "node"):
            node_name = context.node.name
            node_group = context.annotation_data_owner.name_full
            draw_properties(self.layout, node_group, node_name)
        pass

# Получить value для вывода в диалоговом окне выбора параметров:
def get_value_as_str(value):
    if type(value).__name__ == "IDPropertyArray":
        name = type(value[0]).__name__
        if name=='float':
            res = ""+name+"["+str(len(value))+']:['+", ".join([f"{x:.3f}" for x in value])+']'
        else:
            res = ""+name+"["+str(len(value))+']:['+", ".join([str(x) for x in value])+']'
    else:
        if type(value).__name__=='float':
            res = f"{value:.3f}"
        else:
            res = str(value)
    return res

class SvNodeInDataMK4(SverchCustomTreeNode):
    object_names        : bpy.props.CollectionProperty(type=SvONDataCollectionMK4)
    active_obj_index    : bpy.props.IntProperty()

    custom_properties_sockets    : bpy.props.CollectionProperty(type=SvONSocketDataMK4)
    custom_properties_sockets_index  : bpy.props.IntProperty()

    active_object_name                              : bpy.props.StringProperty(default='')
    active_object_type                              : bpy.props.StringProperty(default='')
    active_object_custom_properties                 : bpy.props.CollectionProperty(type=SvONCurrentObjectCustomPropertiesCollectionMK4)
    active_object_custom_properties_index           : bpy.props.IntProperty()
    active_object_data_custom_properties            : bpy.props.CollectionProperty(type=SvONCurrentObjectCustomPropertiesCollectionMK4)
    active_object_data_custom_properties_exists     : bpy.props.BoolProperty(default=False,options={'SKIP_SAVE'},) # Существуют ли custom properties в data у активного объекта
    active_object_data_custom_properties_index      : bpy.props.IntProperty()
    active_object_material_custom_properties        : bpy.props.CollectionProperty(type=SvONCurrentObjectCustomPropertiesCollectionMK4)
    active_object_material_custom_properties_index  : bpy.props.IntProperty()
    active_object_material_custom_properties_exists : bpy.props.BoolProperty(default=False,options={'SKIP_SAVE'},) # Существуют ли custom properties в material у активного объекта

    # Cache of active object properties
    custom_properties_of_active_object = dict({'OBJECT':[], 'DATA':[], 'MATERIAL':[],})
    
    custom_properties_modes = [
        ('OBJECT'   , "Object"  , "Object custom properties"    , 'OBJECT_DATA', 0),
        ('DATA'     , "Data"    , "Object Data custom properties"      , 'OUTLINER_DATA_MESH', 1),
        ('MATERIAL' , "Material", "Object Material custom properties"  , 'MATERIAL_DATA', 2),
    ]
    custom_properties_mode : bpy.props.EnumProperty(
        name    = "Custom properties mode",
        items   = custom_properties_modes,
        default = 'OBJECT',
        #update = updateNode
    )


    minimal_node_ui         : bpy.props.BoolProperty(default=False)
    object_names_ui_minimal : bpy.props.BoolProperty(default=False, description='Minimize table view, show only used/enabled objects')

    apply_matrix: bpy.props.BoolProperty(
        name        = "Apply matrices",
        description = "Apply objects matrices",
        default     = True,
        update      = updateNode,
    )

    node_protected_socket_names = []

    def update_viewport_display(self, context):
        objs = get_objects_from_node(self.object_names)
        for o in objs:
            for n in prop_names:
                prop_name = "show_"+n
                if hasattr(o, prop_name):
                    setattr(o, prop_name, getattr(self, prop_name) )
            pass
        pass

    show_name: bpy.props.BoolProperty(
        name = "Name",
        description="Display the object's name",
        default = False,
        update = update_viewport_display
    )

    show_axis: bpy.props.BoolProperty(
        name = "Axes",
        description="Display the object's origin and exes",
        default = False,
        update = update_viewport_display
    )

    show_wire: bpy.props.BoolProperty(
        name = "Wireframe",
        description="Display the object's wireframe over solid shading",
        default = False,
        update = update_viewport_display
    )

    show_all_edges: bpy.props.BoolProperty(
        name = "All edges",
        description="Display all edges for mesh objects",
        default = False,
        update = update_viewport_display
    )

    show_texture_space: bpy.props.BoolProperty(
        name = "Texture space",
        description="Display the object's texture space",
        default = False,
        update = update_viewport_display
    )

    show_shadows: bpy.props.BoolProperty(
        name = "Shadow",
        description="Object cast shadows in the 3D viewport",
        default = True,
        update = update_viewport_display
    )

    show_in_front: bpy.props.BoolProperty(
        name = "In Front",
        description="Make the object dosplay in front of others",
        default = False,
        update = update_viewport_display
    )

    display_types = [
            ('BOUNDS', "", "BOUNDS: Display the bounds of the object", "MATPLANE", 0),
            ('WIRE', "", "WIRE: Display the object as a wireframe", "MESH_CUBE", 1),
            ('SOLID', "", "SOLID: Display the object as a solid (if solid drawing is enabled in the viewport)", "SNAP_VOLUME", 2),  #custom_icon("SV_MAKE_SOLID")
            ('TEXTURED', "", "TEXTURED: Display the object with textures (if textures are enabled in the viewport)", "TEXTURE",  3),
        ]
    
    def update_display_type(self, context):
        objs = get_objects_from_node(self.object_names)
        for o in objs:
            o.display_type=self.display_type
        return
    
    display_type : bpy.props.EnumProperty(
        name = "Display Types",
        items = display_types,
        default = 'WIRE',
        update = update_display_type)
    
    hide_render_types = [
            ('RESTRICT_RENDER_ON', "", "Render objects", "RESTRICT_RENDER_ON", 0),
            ('RESTRICT_RENDER_OFF', "", "Do not render objects", "RESTRICT_RENDER_OFF", 1),
        ]
    
    def update_render_type(self, context):
        for item in self.object_names:
            if item.object_pointer:
                item.object_pointer.hide_render = True if self.hide_render_type=='RESTRICT_RENDER_ON' else False
        return
    
    hide_render_type : bpy.props.EnumProperty(
        name = "Render Types",
        items = hide_render_types,
        default = 'RESTRICT_RENDER_OFF',
        update = update_render_type)
        
    frame_selected: bpy.props.BoolProperty(default=True, description='Frame selected: magnify Local View')

    def custom_property_socket_draw(self, socket, context, layout):
        '''Draw custom property socket label'''
        socket_info = [socket_info for socket_info in self.custom_properties_sockets if socket_info.socket_inner_name==socket.name]
        if socket_info:
            socket_info_0 = socket_info[0]
            layout.label(text=f'{socket_info_0.socket_ui_label}', icon=[cp for cp in SvNodeInDataMK4.custom_properties_modes if socket_info_0.socket_type==cp[0]][0][3])
            if socket.is_linked:  # linked INPUT or OUTPUT
                layout.label(text=f". {socket.objects_number or ''}")
            pass
        else:
            layout.label(text=f'- {socket.label} ')
            if socket.is_linked:  # linked INPUT or OUTPUT
                layout.label(text=f". {socket.objects_number or ''}")
            elif socket.is_output:  # unlinked OUTPUT
                layout.separator()

        pass
    
    def remove_duplicates_objects_in_list(self, ops):
        lst=[]
        remove_idx = []
        for I, item in enumerate(self.object_names):
            pointer = None
            if item.pointer_type=='OBJECT':
                pointer = item.object_pointer
            elif item.pointer_type=='COLLECTION':
                pointer = item.collection_pointer
            if pointer:
                if (pointer in lst)==False:
                    lst.append(pointer)
                else:
                    remove_idx.append(I)

        remove_idx.sort()
        remove_idx.reverse()
        for idx in remove_idx:
            self.object_names.remove(idx)
        ops.report({'INFO'}, f"Removed {len(remove_idx)} object(s) ")
        return

    def sync_active_object_in_scene_with_list(self, ops):
        object_synced = False
        if bpy.context.view_layer.objects.active:
            active_object = bpy.context.view_layer.objects.active
            first_duplicated = sync_index = None
            for I, item in enumerate(self.object_names):
                objs = get_objects_from_item(item)
                if active_object in objs:
                    if first_duplicated==None:
                        first_duplicated = I
                        continue
                    if I>self.active_obj_index:
                        sync_index = I
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
        '''Collect selected objects'''
        self.object_names.clear()
        names = [obj.name for obj in bpy.data.objects if (obj.select_get() and len(obj.users_scene) > 0 and len(obj.users_collection) > 0)]

        if self.sort:
            names.sort()

        for name in names:
            item = self.object_names.add()
            item.object_pointer = bpy.data.objects[name]
            item.name = name
            item.icon = 'OUTLINER_OB_' + bpy.data.objects[name].type

        if not self.object_names:
            ops.report({'WARNING'}, "Warning, no selected objects in the scene")
            return

        self.process_node(None)

    def add_objects_from_scene(self, ops):
        '''Add selected objects on the top of the list'''

        names = [obj.name for obj in bpy.data.objects if (obj.select_get() and len(obj.users_scene) > 0 and len(obj.users_collection) > 0)]

        for name in names:
            item = self.object_names.add()
            item.object_pointer = bpy.data.objects[name]
            item.name = name
            self.object_names.move(len(self.object_names)-1, 0)
            self.active_obj_index=0

        if not self.object_names:
            ops.report({'WARNING'}, "Warning, no selected objects in the scene")
            return

        self.process_node(None)


    def add_empty_collection(self, ops):
        '''Add empty collection pointer on the top of the list'''

        item = self.object_names.add()
        item.pointer_type = "COLLECTION"
        self.object_names.move(len(self.object_names)-1, 0)
        self.active_obj_index=0

        return

    def clear_objects_from_list(self, ops):
        '''Clear list of objects'''
        self.object_names.clear()
        self.process_node(None)
    
    def load_active_object_custom_properties(self):
        '''Load Object Custom Properties'''
        # Независимо от наличия текущего объекта дополнительно проверить
        # в таблице custom properties есть ли в ней какие-то сокеты,
        # которые не относятся к обязательным. Если есть, то вывести их.

        socket_inner_name = {i.socket_inner_name for i in self.custom_properties_sockets}
        lst_not_custom_properties_sockets = [
            s for s in self.outputs
            if s.name not in self.node_protected_socket_names
            and s.name not in socket_inner_name
        ]
        if lst_not_custom_properties_sockets:
            for s in lst_not_custom_properties_sockets:
                elem = self.custom_properties_sockets.add()
                elem.socket_type='SOCKET'
                elem.socket_inner_name = s.name
                elem.socket_ui_name = s.label if s.label else s.name
                elem.socket_ui_label = s.label if s.label else s.name
            pass

        self.active_object_name=''
        self.active_object_type=''
        obj = bpy.context.active_object
        if obj:
            def load_custom_property_info(custom_properties, props, _mi, _socket_type):
                '''Кэширование custom properties при открытом диалоговом окне (нужно только на момент открытия диалогового окна)'''
                for key, value in _mi.items():
                    # системные служебные пропускаем
                    if key.startswith("_"):
                        continue

                    ui = _mi.id_properties_ui(key)
                    meta = ui.as_dict()

                    type_value_name = type(value).__name__
                    is_array = False
                    array_size=0
                    if type_value_name=='IDPropertyArray':
                        type_value_name = type(value[0]).__name__
                        is_array = True
                        array_size = len(value)
                    # Разрешены только массивы или примитивные типы:
                    if type_value_name not in ['str', 'float', 'int', 'bool', 'array']:
                        continue
                    # Не добавлять дубликаты
                    if any(prop['name'] == key for prop in props):
                        continue
                    props.append({
                        "name": key,
                        "type": type_value_name,
                        "is_array": is_array,
                        "array_size": array_size,
                        "min": meta.get("min"),
                        "max": meta.get("max"),
                        "default": meta.get("default") if is_array==True else [meta.get("default")], # Все элементы хранить как array
                        "description": meta.get("description"),
                        "subtype": meta.get("subtype"),
                    })
                    item = custom_properties.add()
                    item.name = key
                    item.socket_type = _socket_type
                    item.apply=False
                    item.value = get_value_as_str(value)
                pass
                
            self.active_object_name=obj.name
            self.active_object_type=obj.type
            # props_obj = []
            self.active_object_custom_properties.clear()
            self.active_object_data_custom_properties.clear()
            self.active_object_material_custom_properties.clear()

            # Очистить закешированные свойства предыдущего активного объекта:
            for elem in self.custom_properties_of_active_object:
                self.custom_properties_of_active_object[elem].clear()

            load_custom_property_info(self.active_object_custom_properties, self.custom_properties_of_active_object['OBJECT'], obj, 'OBJECT')
            if obj.data:
                load_custom_property_info(self.active_object_data_custom_properties, self.custom_properties_of_active_object['DATA'], obj.data, 'DATA')
                self.active_object_data_custom_properties_exists = True
            else:
                # Не у всех есть obj.data, например, obj.data отсутствует у объектов типа empty и
                # force fields (Хотя это и кажется странным), а вот у lamp - есть
                self.active_object_data_custom_properties_exists = False
            
            if obj.material_slots:
                # save all sockets materials in materials sockets of object (materials name if it is not null and info about faces)
                materials_info = dict([(id, dict(material_name=(None if obj.material_slots[id].material is None else obj.material_slots[id].material.name), material=(None if obj.material_slots[id].material is None else obj.material_slots[id].material),)) for id in range(len(obj.material_slots))])
                for k in materials_info:
                    material_name = materials_info[k]['material_name']
                    mi = materials_info[k]['material']
                    if mi:
                        load_custom_property_info(self.active_object_material_custom_properties, self.custom_properties_of_active_object['MATERIAL'], mi, 'MATERIAL')
                    else:
                        # иногда слот материала пустой
                        pass
                    pass
                self.active_object_material_custom_properties_exists = True
            else:
                # Не у всех объектов есть материалы
                self.active_object_material_custom_properties_exists = False
                pass
            return

        return None, None

    def move_current_object_up(self, ops):
        '''Move current object in list up'''

        if self.active_obj_index>0:
            self.object_names.move(self.active_obj_index, self.active_obj_index-1)
            self.active_obj_index-=1

        if not self.object_names:
            ops.report({'WARNING'}, "Warning, no selected objects in the scene")
            return

        self.process_node(None)

    def move_current_object_down(self, ops):
        '''Move current object in list down'''

        if self.active_obj_index<=len(self.object_names)-2:
            self.object_names.move(self.active_obj_index, self.active_obj_index+1)
            self.active_obj_index+=1

        self.process_node(None)

    def recreate_custom_properties_socket_with_socket(self, socket_links=None):
        '''Пересоздание сокетов с custom properties с учётом заданных links'''

        # Удалить сокеты custom properties:
        for I in range(len(self.custom_properties_sockets)):
            custom_properties_sockets_I = self.custom_properties_sockets[I]
            if custom_properties_sockets_I.socket_inner_name in self.outputs:
                s = self.outputs[custom_properties_sockets_I.socket_inner_name]
                self.outputs.remove(s)
            pass
        # Пересоздать сокеты:
        for I in range(len(self.custom_properties_sockets)):
            item = self.custom_properties_sockets[I]
            if item.socket_inner_name not in self.outputs:
                self.outputs.new('SvVerticesSocket', item.socket_inner_name)
                self.outputs[item.socket_inner_name].label = item.socket_ui_label
                self.outputs[item.socket_inner_name].custom_draw = 'custom_property_socket_draw'
        # Пересоздать links:
        if socket_links:
            for socket_name in socket_links:
                if socket_name in self.outputs:
                    s = self.outputs[socket_name]
                    for link in socket_links[socket_name]:
                        restored_link = self.id_data.links.new(s, link['to_socket'])
                    pass
                else:
                    # Очень странная ситуация. Не знаю пока что делать.
                    pass
            pass
        pass

    def recreate_custom_properties_socket(self):
        '''Пересоздание сокетов с custom properties'''
        socket_links = dict()
        # Пересчитать существующие сокеты
        for I in range(len(self.custom_properties_sockets)):
            custom_properties_sockets_I = self.custom_properties_sockets[I]
            if custom_properties_sockets_I.socket_inner_name in self.outputs:
                s = self.outputs[custom_properties_sockets_I.socket_inner_name]
                links = []
                for link in s.links:
                    links.append({'to_node': link.to_node, 'to_socket': link.to_socket, 'socket_name': s.name})
                socket_links[custom_properties_sockets_I.socket_inner_name] = links
            pass
        self.recreate_custom_properties_socket_with_socket(socket_links)
        pass

    def move_custom_property_socket_up(self, ops):
        '''Move Custom Property Socket up'''

        if self.custom_properties_sockets_index>0:
            self.custom_properties_sockets.move(self.custom_properties_sockets_index, self.custom_properties_sockets_index-1)
            self.custom_properties_sockets_index-=1
            self.recreate_custom_properties_socket()
            pass

        if not self.custom_properties_sockets:
            ops.report({'WARNING'}, "Warning, no selected objects in the scene")
            return

        self.process_node(None)

    def move_custom_property_socket_down(self, ops):
        '''Move Custom Property Socket down'''
        if self.custom_properties_sockets_index<=len(self.custom_properties_sockets)-2:
            self.custom_properties_sockets.move(self.custom_properties_sockets_index, self.custom_properties_sockets_index+1)
            self.custom_properties_sockets_index+=1
            self.recreate_custom_properties_socket()
            pass

        if not self.custom_properties_sockets:
            ops.report({'WARNING'}, "Warning, no selected objects in the scene")
            return

        self.process_node(None)

    def draw_controls(self, elem):
        elem.alignment='RIGHT'
        self.wrapper_tracked_ui_draw_op(elem, SvONAddObjectsFromSceneUpMK4.bl_idname, text='', icon='ADD')
        self.wrapper_tracked_ui_draw_op(elem, SvONAddEmptyCollectionMK4.bl_idname, text='', icon='GROUP')
        self.wrapper_tracked_ui_draw_op(elem, SvONItemMoveUpMK4.bl_idname, text='', icon='TRIA_UP')
        self.wrapper_tracked_ui_draw_op(elem, SvONItemMoveDownMK4.bl_idname, text='', icon='TRIA_DOWN')
        self.wrapper_tracked_ui_draw_op(elem, SvONHighlightProcessedObjectsInSceneMK4.bl_idname, text='', icon='GROUP_VERTEX')
        self.wrapper_tracked_ui_draw_op(elem, SvONHighlightAllObjectsInSceneMK4.bl_idname, text='', icon='OUTLINER_OB_POINTCLOUD')
        self.wrapper_tracked_ui_draw_op(elem, SvONSyncSceneObjectWithListMK4.bl_idname, icon='TRACKING_BACKWARDS_SINGLE', text='', emboss=True, description_text = 'Select the scene active object in list\n(Cycle between duplicates if there are any)')
        
        objects_set = get_pointers_from_node(self.object_names)
        if len(objects_set)<len(self.object_names):
            icon = 'AUTOMERGE_ON'
            description_text = f'Remove any duplicates objects in list\nCount of duplicates objects: {len(self.object_names)-len(objects_set)}'
        else:
            icon = 'AUTOMERGE_OFF'
            description_text = 'Remove any duplicates objects in list.\nNo duplicates objects in list now'
        description_text += "\n\nShift-Cliсk - skip confirmation dialog"
        self.wrapper_tracked_ui_draw_op(elem, SvONRemoveDuplicatesObjectsInListMK4.bl_idname, text='', icon=icon, description_text=description_text)
        elem.separator()
        self.wrapper_tracked_ui_draw_op(elem, SvONClearObjectsFromListMK4.bl_idname, text='', icon='CANCEL')
        elem.separator()
        if self.object_names_ui_minimal:
            elem.prop(self, "object_names_ui_minimal", text='', toggle=True, icon='FULLSCREEN_EXIT')
        else:
            elem.prop(self, "object_names_ui_minimal", text='', toggle=True, icon='FULLSCREEN_ENTER')
        pass

    def draw_object_names(self, layout):
        layout.template_list("SVON_UL_NamesListMK4", f"uniq_{self.name}", self, "object_names", self, "active_obj_index", rows=3, item_dyntip_propname='test_text1')
        pass

    def load_from_json(self, node_data: dict, import_version: float):
        '''function to get data when importing from json'''
        data_objects = bpy.data.objects

        if 'object_names' in node_data:
            data_list = node_data.get('object_names')
            if data_list:
                data = json.loads(data_list)
                for I, k in enumerate(data):
                    if I<=len(self.object_names)-1:
                        pointer_type    = k['pointer_type']
                        if pointer_type=='OBJECT':
                            name    = k['object_pointer']
                            if name in data_objects:
                                self.object_names[I].object_pointer = data_objects[name]
                                pass
                        elif pointer_type=='COLLECTION':
                            name    = k['collection_pointer']
                            coll = bpy.data.collections.get(name)
                            if coll is not None:
                                self.object_names[I].collection_pointer = coll
                            pass

                        if 'exclude' in k:
                            exclude = k['exclude']
                            self.object_names[I].exclude = exclude
                    else:
                        continue
                    pass
        pass

    def save_to_json(self, node_data: list):
        '''function to set data for exporting json'''
        data = []
        for item in self.object_names:
            if item.pointer_type=='OBJECT':
                if item.object_pointer:
                    data.append( dict(  object_pointer=item.object_pointer.name, exclude=item.exclude, pointer_type=item.pointer_type ) )
                else:
                    data.append( dict(  object_pointer='', exclude=item.exclude, pointer_type=item.pointer_type ) )
            elif item.pointer_type=='COLLECTION':
                if item.collection_pointer:
                    data.append( dict(  collection_pointer=item.collection_pointer.name, exclude=item.exclude, pointer_type=item.pointer_type ) )
                else:
                    data.append( dict(  collection_pointer='', exclude=item.exclude, pointer_type=item.pointer_type ) )
                pass
            pass

        data_json_str = json.dumps(data)
        node_data['object_names'] = data_json_str

    pass

    def get_objects(self, input_socket_name=None):
        if input_socket_name and input_socket_name in self.inputs:
            objs = self.inputs[input_socket_name].sv_get(default=[[]])
            if not self.object_names and not objs[0]:
                return
            if isinstance(objs[0], list):
                objs = objs[0]
        if not objs:
            objs = []
            for o in self.object_names:
                if o.exclude==False and (o.object_pointer and o.object_pointer.name in bpy.context.scene.objects or o.pointer_type=='COLLECTION'): # objects can be in object_pointer but absent in the scene
                    _obj = get_objects_from_item(o)
                    objs.extend(_obj)
                pass
            pass
        return objs
    
    def apply_custom_property(self, objs):
        '''Применить custom properties к объектам из objs (предполагается, что объекты берутся из списка нода)'''
        
        def _apply_custom_property(obj_elem, cp):
            '''Применить custom propertis к текущему уровню указанного объекта'''
            default = getattr(cp, f"custom_property_default_{cp.custom_property_type}")
            if cp.custom_property_type=='str':
                pass
            else:
                if cp.custom_property_is_array==False:
                    default = default[0]
                else:
                    default = default[:cp.custom_property_array_size]
                pass
            meta = dict({
                'description'   : cp.custom_property_description,
                'subtype'       : cp.custom_property_subtype,
                'default'       : default,
            })
            if cp.custom_property_type not in ['str', 'bool']:
                # Не всем свойствам можно задать min и max
                meta['min'] = getattr(cp, f"custom_property_min_{cp.custom_property_type}")
                meta['max'] = getattr(cp, f"custom_property_max_{cp.custom_property_type}")

            if cp.custom_property_name in obj_elem:
                if (cp.custom_property_is_array==True):
                    # Если свойство заявлено как массив и текущее свойство является массивом
                    # и их размеры равны и их типы равны, то пропустить
                    if (type(obj_elem[cp.custom_property_name]).__name__=='IDPropertyArray'
                        and cp.custom_property_type==type(obj_elem[cp.custom_property_name][0]).__name__
                        and cp.custom_property_array_size==len(obj_elem[cp.custom_property_name])
                    ):
                        pass
                    else:
                        # иначе при любом отклонении и несоответствии данных
                        # требуется переопределение свойств:
                        # TODO: сделать проверку анимации и копирование ключей анимации
                        #       на новое свойство
                        del obj_elem[cp.custom_property_name]
                    pass
                else:
                    if type(obj_elem[cp.custom_property_name]).__name__=='IDPropertyArray':
                        # Если новый тип не массив, а старый был массивом, то требуется
                        # переопределение свойства:
                        del obj_elem[cp.custom_property_name]
                    else:
                        # Если и новый и старый тип не массивы, то проверить,
                        # если их типы не одинаковые, то удалить свойство,
                        # т.к. требуется его переопределение: 
                        if cp.custom_property_type!=type(obj_elem[cp.custom_property_name]).__name__:
                            del obj_elem[cp.custom_property_name]
                        pass
                    pass
                pass

            if cp.custom_property_name not in obj_elem:
                obj_elem[cp.custom_property_name] = default
                pass
            obj_elem.id_properties_ui(cp.custom_property_name).update(**meta)
            pass
        
        # Применить кастомные свойства к объектам и материалам:
        for obj in objs:
            for cp in self.custom_properties_sockets:
                if cp.socket_type=='OBJECT':
                    _apply_custom_property(obj, cp)
                    pass
                elif cp.socket_type=='DATA':
                    if obj.data:
                        _apply_custom_property(obj.data, cp)
                    pass
                elif cp.socket_type=='MATERIAL':
                    if obj.material_slots:
                        # Получить список материалов объекта:
                        materials_info = dict([(id, dict(material_name=(None if obj.material_slots[id].material is None else obj.material_slots[id].material.name), material=(None if obj.material_slots[id].material is None else obj.material_slots[id].material),)) for id in range(len(obj.material_slots))])
                        for k in materials_info:
                            material_name = materials_info[k]['material_name']
                            mi = materials_info[k]['material']
                            if mi:
                                _apply_custom_property(mi, cp)
                            else:
                                # Бывает, что слот пустой, тогда это присвоение custom properties надо пропустить
                                pass
                            pass
                    pass
                else:
                    # Неизвестный тип
                    pass
                pass
            pass
        return objs

    def get_next_unique_socket_name(self):
        custom_property_suffix = "custom_property_"
        lst_names = [cp.socket_inner_name for cp in self.custom_properties_sockets]
        I=0
        while(True):
            socket_inner_name=custom_property_suffix+str(I)
            if socket_inner_name in lst_names:
                I+=1
                continue
            break
        return socket_inner_name
    
    def custom_property_add_to_output_socket_invoke(self, _socket_type, _socket_inner_name, _custom_property_name, _socket_ui_name, _socket_ui_label, _idx):
        lst_socket_info = [custom_property_info for custom_property_info in self.custom_properties_sockets if _custom_property_name==custom_property_info.custom_property_name and _socket_type==custom_property_info.socket_type]
        if len(lst_socket_info)>0:
            lst_socket_info_0 = lst_socket_info[0]
            for s in self.outputs:
                if s.name==lst_socket_info_0.socket_inner_name:
                    #ShowMessageBox(f"Socket '{self.custom_property_name}'({self.socket_type}) already exitsts for this custom property", 'Error', 'ERROR')
                    return 'CANCELLED', f"Socket '{_custom_property_name}'({_socket_type}) already exitsts for this node {self.name}", 'Error', 'ERROR'
                else:
                    continue
            pass
        return 'FINISHED', '', '', ''

    def custom_property_add_to_output_socket_execute(self, _socket_type, _socket_inner_name, _custom_property_name, _socket_ui_name, _socket_ui_label, _idx):
        '''call from SvONCustomPropertyAddToOutputSocket'''
        # Проверить, а не создан ли уже для этого параметра сокет:
    
        lst_socket_info = [custom_property_info for custom_property_info in self.custom_properties_sockets if _custom_property_name==custom_property_info.custom_property_name and _socket_type==custom_property_info.socket_type]
        if len(lst_socket_info)>0:
            lst_socket_info_0 = lst_socket_info[0]
            for s in self.outputs:
                if s.name==lst_socket_info_0.socket_inner_name:
                    # если сокет с этим свойством уже создан, то не создавать такой сокет второй раз
                    return 'CANCELLED', 'WARNING', f"Socket '{_custom_property_name}'({_socket_type}) already exitsts for this custom property"
                else:
                    continue
            pass

        if len(lst_socket_info)>0:
            # Если запись в таблице есть, но сокета нет, то запись в таблицу не заносить
            item                        = lst_socket_info_0
            socket_inner_name           = item.socket_inner_name
        else:
            # Если и записи нет, то занести запись в таблицу:
            socket_inner_name           = self.get_next_unique_socket_name()
            item                        = self.custom_properties_sockets.add()
            item.socket_type            = _socket_type
            item.socket_inner_name      = socket_inner_name
            item.custom_property_name   = _custom_property_name
            item.socket_ui_name         = _custom_property_name
            item.socket_ui_label        = _custom_property_name
            item.remove                 = False

            elem = self.custom_properties_of_active_object[_socket_type][_idx]
            item.custom_property_type           = elem['type']
            item.custom_property_description    = elem['description']
            item.custom_property_subtype        = elem['subtype']
            item.custom_property_is_array       = elem['is_array']
            item.custom_property_array_size     = elem['array_size']
            if elem['type'] not in ['str', 'bool']:
                # Не всем свойствам можно заносить min/max
                setattr(item, f"custom_property_min_{elem['type']}", elem['min'])
                setattr(item, f"custom_property_max_{elem['type']}", elem['max'])
            setattr(item, f"custom_property_default_{elem['type']}", 
                    elem['default'][0] if elem['type']=='str'
                    else elem['default'][0] if elem['type']=='str' else (elem['default']+[elem['default'][-1]]*32)[:32] 
                )
            pass

        self.outputs.new('SvVerticesSocket', item.socket_inner_name)
        self.outputs[socket_inner_name].label = item.socket_ui_label
        self.outputs[socket_inner_name].custom_draw = 'custom_property_socket_draw'
        return 'FINISHED', 'INFO', ''

classes = [
    SvONItemEmptyOperatorMK4,
    SvONHighlightAllObjectsInSceneMK4,
    SvONHighlightProcessedObjectsInSceneMK4,
    SvONClearObjectsFromListMK4,
    SvONLoadActiveObjectCustomPropertiesMK4,
    SvONSyncSceneObjectWithListMK4,
    SvONRemoveDuplicatesObjectsInListMK4,
    SVON_localview_objectsInListMK4,
    SvONItemMoveDownMK4,
    SvONItemMoveUpMK4,
    SvONAddObjectsFromSceneUpMK4,
    SvONAddEmptyCollectionMK4,
    SvONSwitchOffUnlinkedSocketsMK4,
    SvONItemSelectObjectMK4,
    SvONItemEnablerMK4,
    SvONItemRemoveMK4,
    SvONItemOperatorMK4,
    SvONDataCollectionMK4,  # TODO: rename to SvONObjectDataMK4
    SvONSocketDataMK4,
    SvONCurrentObjectCustomPropertiesCollectionMK4,
    SVON_UL_CurrentObjectCustomPropertiesListMK4,
    SVON_UL_CustomPropertiesSocketsListMK4,
    SvONCustomPropertySocketMoveUpMK4,
    SvONCustomPropertySocketMoveDownMK4,
    SvONCustomPropertyAddToOutputSocketMK4,
    SvONCustomPropertySocketRemoveMK4,
    SVON_UL_NamesListMK4,
    SV_PT_ViewportDisplayPropertiesDialogMK4,
    SV_PT_ViewportDisplayCustomPropertiesDialogMK4,
    SV_PT_ViewportDisplayPropertiesMK4,
]

register, unregister = bpy.utils.register_classes_factory(classes)