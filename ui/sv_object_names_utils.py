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

# object properties in Blender viewport -> Object Properties -> Viewport Display
prop_names = ['name', 'axis', 'wire', 'all_edges', 'texture_space', 'shadows', 'in_front']

def get_objects_of_collection(coll, use_sort_alpha):
    obj_coll = []
    if use_sort_alpha==False:
        # objects before collections
        obj_coll.extend(coll.objects)
    
    for child in coll.children_recursive if use_sort_alpha==False else reversed(coll.children_recursive):
        if use_sort_alpha==True:
            obj_coll.extend(sorted(child.objects, key=lambda o: o.name))
        else:
            obj_coll.extend( list(child.objects))

    if use_sort_alpha==True:
        # objects after collections
        obj_coll.extend(sorted(list(coll.objects), key=lambda o: o.name))
    
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
    icon   : bpy.props.StringProperty(default="BLANK1")
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
                        chars.append( f"{obj.type}, {obj.name}")
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
                    chars.append("Members:  (Orders as Outliner->Filter->Sort Alphabetically (On/Off))\n")
                for obj in objs:
                    chars.append( f"   {obj.type}, {obj.name}")
                chars.append("---------------------")
                s = "\n".join(chars)
            else:
                s = 'Collection is empty. Select collection.\n'
        else:
            pass

        return s
    test_text1: bpy.props.StringProperty(get=_get_description)

class ReadingObjectDataError(Exception):
    pass

class SvONSwitchOffUnlinkedSocketsMK4(bpy.types.Operator):
    '''Hide all unlinked sockets'''
    bl_idname = "node.sv_on_switch_off_unlinked_sockets_mk4"
    bl_label = "Select object as active"

    # node_name: bpy.props.StringProperty(default='')
    # tree_name: bpy.props.StringProperty(default='')  # all item types should have actual name of a tree
    # fn_name  : bpy.props.StringProperty(default='')
    # idx      : bpy.props.IntProperty(default=0)
    description_text: bpy.props.StringProperty(default='Only hide unlinked output sockets')

    @classmethod
    def description(cls, context, property):
        s = property.description_text
        return s

    def invoke(self, context, event):
        node = context.node
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

class SvON_UL_NamesListMK4(bpy.types.UIList):
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
                    ((item.object_pointer and item.pointer_type=='OBJECT') or (item.collection_pointer and item.pointer_type=='COLLECTION'))
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
    bl_ui_units_x = 15

    # def is_extended():
    #     return True

    def draw(self, context):
        if hasattr(context, "node"):
            layout = self.layout
            #layout.use_property_split = True https://blender.stackexchange.com/questions/161581/how-to-display-the-animate-property-diamond-keyframe-insert-button-2-8x
            root_grid = layout.grid_flow(row_major=False, columns=2, align=True)
            grid1 = root_grid.grid_flow(row_major=False, columns=1, align=True)
            grid1.label(text='Viewport Display:')
            for n in prop_names:
                prop_name = "show_"+n
                grid1.prop(context.node, prop_name)

            grid2 = root_grid.grid_flow(row_major=False, columns=1, align=True)
            grid2.label(text='Output Sockets:')
            for s in context.node.outputs:
                row = grid2.row(align=True)
                row.enabled = not s.is_linked
                row.prop(s, 'hide', text=f'{s.label}{" (linked)" if s.is_linked else ""}' if s.label else s.name)
            grid2.row(align=True).operator(SvONSwitchOffUnlinkedSocketsMK4.bl_idname, icon='GP_CAPS_FLAT', text='Hide unlinked sockets', emboss=True)

        pass

class SvNodeInDataMK4(SverchCustomTreeNode):
    object_names: bpy.props.CollectionProperty(type=SvONDataCollectionMK4)
    minimal_node_ui: bpy.props.BoolProperty(default=False)
    object_names_ui_minimal: bpy.props.BoolProperty(default=False, description='Minimize table view')
    active_obj_index: bpy.props.IntProperty()

    apply_matrix: bpy.props.BoolProperty(
        name = "Apply matrices",
        description = "Apply objects matrices",
        default = True,
        update = updateNode,
    )

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
        #self.object_names.clear()

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

    def move_current_object_up(self, ops):
        '''Move current obbect in list up'''

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
        layout.template_list("SvON_UL_NamesListMK4", f"uniq_{self.name}", self, "object_names", self, "active_obj_index", rows=3, item_dyntip_propname='test_text1')
        pass
    pass

classes = [
    SvONItemEmptyOperatorMK4,
    SvONHighlightAllObjectsInSceneMK4,
    SvONHighlightProcessedObjectsInSceneMK4,
    SvONClearObjectsFromListMK4,
    SvONSyncSceneObjectWithListMK4,
    SvONRemoveDuplicatesObjectsInListMK4,
    SvONItemMoveDownMK4,
    SvONItemMoveUpMK4,
    SvONAddObjectsFromSceneUpMK4,
    SvONAddEmptyCollectionMK4,
    SvONSwitchOffUnlinkedSocketsMK4,
    SvONItemSelectObjectMK4,
    SvONItemEnablerMK4,
    SvONItemRemoveMK4,
    SvONItemOperatorMK4,
    SvONDataCollectionMK4,
    SvON_UL_NamesListMK4,
    SV_PT_ViewportDisplayPropertiesMK4,
]

register, unregister = bpy.utils.register_classes_factory(classes)