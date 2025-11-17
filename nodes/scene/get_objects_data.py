# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
import bmesh
from mathutils import Vector, Matrix
import json

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.sv_operator_mixins import SvGenericNodeLocator
from sverchok.data_structure import updateNode
from sverchok.utils.sv_bmesh_utils import pydata_from_bmesh
from sverchok.utils.sv_mesh_utils import mesh_join
from sverchok.utils.nodes_mixins.show_3d_properties import Show3DProperties
from sverchok.ui.sv_icons import custom_icon
from sverchok.utils.blender_mesh import (
    read_verts, read_edges, read_verts_normal,
    read_face_normal, read_face_center, read_face_area, read_materials_idx)
import numpy as np


class SvOB3BDataCollectionMK4(bpy.types.PropertyGroup):
    object_pointer: bpy.props.PointerProperty(
        name="object",
        type=bpy.types.Object
    )
    #name   : bpy.props.StringProperty(default='')
    icon   : bpy.props.StringProperty(default="BLANK1")
    exclude: bpy.props.BoolProperty(
        default=False,
        description='Exclude from process',
    )

    # dynamic table element description:
    def _get_description(self):
        s = 'No object'
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
                pass
            chars.append("---------------------")
            s = "\n".join(chars)

        return s
    test_text1: bpy.props.StringProperty(get=_get_description)





class ReadingObjectDataError(Exception):
    pass

class SvOB3ItemSelectObjectMK4(bpy.types.Operator):
    '''Select object as active in 3D Viewport. Use shift to add object into current selection of objects in scene.'''
    bl_idname = "node.sv_ob3_item_select_object_mk4"
    bl_label = "Select object as active"

    node_name: bpy.props.StringProperty(default='')
    tree_name: bpy.props.StringProperty(default='')  # all item types should have actual name of a tree
    fn_name  : bpy.props.StringProperty(default='')
    idx      : bpy.props.IntProperty(default=0)

    def invoke(self, context, event):
        node = context.node
        if node:
            if self.idx>=0 and self.idx<=len(node.object_names)-1:
                object_pointer = node.object_names[self.idx].object_pointer
                for area in bpy.context.screen.areas:
                    if area.type == 'VIEW_3D':
                        #with context.temp_override(area = area , region = area.regions[-1]):
                            if event.shift==False:
                                # Если Shift не нажат, то сбросить выделения всех объектов:
                                for o in bpy.context.view_layer.objects:
                                    o.select_set(False)
                            if object_pointer.name in bpy.context.view_layer.objects:
                                bpy.context.view_layer.objects.active = object_pointer
                                if object_pointer.select_get()==False:
                                    object_pointer.select_set(True)
                            else:
                                self.report({'INFO'}, f"Object is not in the current scene")
                            break
            pass
        return {'FINISHED'}
    
class SvOB3BItemEnablerMK4(bpy.types.Operator):
    '''Enable/Disable object to process.\nCtrl button to disable all objects first\nShift button to inverse list.'''
    bl_idname = "node.sv_ob3b_item_enabler_mk4"
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

class SvOB3ItemEmptyOperatorMK4(bpy.types.Operator):
    '''Empty operator to fill empty cells in grid'''

    # example of usage to show dynamic description onmouseover:
    # op = row0.column(align=True).operator(SvOB3ItemEmptyOperatorMK4.bl_idname, icon='BLANK1', text='', emboss=False)
    # op.description_text='Object pointer is empty'

    bl_idname = "node.sv_ob3_empty_operator_mk4"
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

class SvOB3BItemRemoveMK4(bpy.types.Operator):
    '''Remove object from list'''
    bl_idname = "node.sv_ob3b_item_remove_mk4"
    bl_label = "Remove"

    fn_name: bpy.props.StringProperty(default='')
    idx    : bpy.props.IntProperty(default=0)

    def invoke(self, context, event):
        #node = context.node.object_names[self.idx]
        if self.idx <= len(context.node.object_names)-1:
            if self.fn_name == 'REMOVE':
                context.node.object_names.remove(self.idx)
                context.node.process_node(None)
        return {'FINISHED'}

class SVOB3B_UL_NamesListMK4(bpy.types.UIList):
    '''Show objects in list item with controls'''
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        # object_exists=False
        # item_icon = "GHOST_DISABLED"
        # if item.name in bpy.data.objects:
        #     object_exists=True
        #     #bpy.data.objects[item.name].data
        #     item_icon = item.icon
        #     if not item.icon or item.icon == "BLANK1":
        #         try:
        #             item_icon = 'OUTLINER_OB_' + bpy.data.objects[item.name].type
        #         except:
        #             ...
        # else:
        #     pass

        item_icon = "GHOST_DISABLED"
        if item.object_pointer:
            try:
                item_icon = 'OUTLINER_OB_' + item.object_pointer.type
            except:
                ...

        item_base = len(str(len(data.object_names)))

        grid = layout.grid_flow(row_major=False, columns=3, align=True)
        UI0 = grid.row(align=True)
        UI0.alignment = 'LEFT'
        UI01 = UI0.column(align=True)
        UI01.alignment = 'LEFT'
        UI01.label(text=f'{index:0{item_base}d}')
        if data.object_names_ui_minimal==True:
            UI02 = UI0.column(align=True)
            UI02.alignment = 'LEFT'
            UI02.label(text='', icon=item_icon)
        #grid.label(text=f'{index:0{item_base}d} {item.name}', icon=item_icon)
        UI03 = UI0.row(align=True)
        if data.object_names_ui_minimal==False:
            usable = max(data.width - 160, 20)
            scale = usable/120
            UI03.scale_x = max(scale, 1.0)
            UI03.prop(item, 'object_pointer', text='')
        else:
            UI03.alignment = 'LEFT'
            UI03.label(text=item.object_pointer.name)


        if data.object_names_ui_minimal:
            pass
        else:
            UI2=grid.row(align=True)
            UI2.alignment = 'RIGHT'

            if item.object_pointer:
                op = UI2.column(align=True).operator(SvOB3ItemSelectObjectMK4.bl_idname, icon='CURSOR', text='', emboss=False)
                op.idx = index
            else:
                op = UI2.column(align=True).operator(SvOB3ItemEmptyOperatorMK4.bl_idname, icon='BLANK1', text='', emboss=False)
                op.description_text='Object pointer is empty'
                pass
            if item.exclude:
                exclude_icon='CHECKBOX_DEHLT'
            else:
                exclude_icon='CHECKBOX_HLT'

            if item.object_pointer:
                op = UI2.column(align=True).operator(SvOB3BItemEnablerMK4.bl_idname, icon=exclude_icon, text='', emboss=False)
                op.fn_name = 'ENABLER'
                op.idx = index
            else:
                op = UI2.column(align=True).operator(SvOB3ItemEmptyOperatorMK4.bl_idname, icon='BLANK1', text='', emboss=False)
                op.description_text='Object pointer is empty'
                pass
            
            op = UI2.column(align=True).operator(SvOB3BItemRemoveMK4.bl_idname, icon='X', text='', emboss=False)
            op.fn_name = 'REMOVE'
            op.idx = index

            duplicate_sign='BLANK1'
            if item.object_pointer and active_data.object_names[getattr(active_data, active_propname)].object_pointer==item.object_pointer:
                lst = [o for o in active_data.object_names if o.object_pointer and o.object_pointer==item.object_pointer]
                if len(lst)>1:
                    duplicate_sign='ONIONSKIN_ON'
            col = UI2.column(align=True).column(align=True)
            col.label(text='', icon=duplicate_sign)
            col.scale_x=0
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
                    (item.object_pointer)
                )
                flt_flags.append(self.bitflag_filter_item if ok else 0)

        return flt_flags, flt_neworder


class SvOB3BItemOperatorMK4(bpy.types.Operator, SvGenericNodeLocator):

    bl_idname = "node.sv_ob3b_collection_operator_mk4"
    bl_label = "generic bladibla"

    fn_name: bpy.props.StringProperty(default='')
    idx    : bpy.props.IntProperty()

    def sv_execute(self, context, node):
        if self.fn_name == 'REMOVE':
            node.object_names.remove(self.idx)
        node.process_node(None)

class SvOB3BAddObjectsFromSceneUpMK4(bpy.types.Operator, SvGenericNodeLocator):

    bl_idname = "node.sv_ob3b_add_object_from_scene_mk4"
    bl_label = "Add selected objects from scene into the list"
    bl_options = {'INTERNAL'}

    def sv_execute(self, context, node):
        """
        
        """
        node.add_objects_from_scene(self)

class SvOB3BMoveUpMK4(bpy.types.Operator, SvGenericNodeLocator):

    bl_idname = "node.sv_ob3b_moveup_mk4"
    bl_label = "Move current object up"
    bl_options = {'INTERNAL'}

    def sv_execute(self, context, node):
        """
        passes the operator's 'self' too to allow calling self.report()
        """
        node.move_current_object_up(self)

class SvOB3BMoveDownMK4(bpy.types.Operator, SvGenericNodeLocator):

    bl_idname = "node.sv_ob3b_movedown_mk4"
    bl_label = "Move current object down"
    bl_options = {'INTERNAL'}

    def sv_execute(self, context, node):
        """
        passes the operator's 'self' too to allow calling self.report()
        """
        node.move_current_object_down(self)

class SvOB3BClearObjectsFromListMK4(bpy.types.Operator, SvGenericNodeLocator):

    bl_idname = "node.sv_ob3b_clear_list_of_objects_mk4"
    bl_label = "Clear list of objects"
    bl_options = {'INTERNAL'}

    def sv_execute(self, context, node):
        """
        passes the operator's 'self' too to allow calling self.report()
        """
        node.clear_objects_from_list(self)

class SvOB3BHighlightProcessedObjectsInSceneMK4(bpy.types.Operator, SvGenericNodeLocator):
    '''Select objects that marked as processed in this node. Use shift to append objects into a previous selected objects'''
    bl_idname = "node.sv_ob3b_highlight_proc_objects_in_list_scene_mk4"
    bl_label = "Highlight processed objects in scene"

    fn_name: bpy.props.StringProperty(default='')

    def invoke(self, context, event):
        node = context.node
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                #with context.temp_override(area = area , region = area.regions[-1]):
                    if event.shift==False:
                        for o in bpy.context.view_layer.objects:
                            o.select_set(False)
                    some_objects_not_in_the_scene = False
                    for item in node.object_names:
                        if item.exclude==False and item.object_pointer:
                            if item.object_pointer.name in bpy.context.view_layer.objects:
                                item.object_pointer.select_set(True)
                            else:
                                some_objects_not_in_the_scene = True
                        pass
                    pass
                    if some_objects_not_in_the_scene == True:
                        self.report({'INFO'}, f"Some objects are not in the current scene")
                #pass
            pass
        pass
        return {'FINISHED'}


class SvOB3BHighlightAllObjectsInSceneMK4(bpy.types.Operator, SvGenericNodeLocator):
    '''Select all objects in this node.'''
    bl_idname = "node.sv_ob3b_highlight_all_objects_in_list_scene_mk4"
    bl_label = "Select all objects in scene"

    fn_name: bpy.props.StringProperty(default='')

    def invoke(self, context, event):
        node = context.node
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                #with context.temp_override(area = area , region = area.regions[-1]):
                    if event.shift==False:
                        for o in bpy.context.view_layer.objects:
                            o.select_set(False)
                    some_objects_not_in_the_scene = False
                    for item in node.object_names:
                        if item.object_pointer:
                            if item.object_pointer.name in bpy.context.view_layer.objects:
                                item.object_pointer.select_set(True)
                            else:
                                some_objects_not_in_the_scene = True
                        pass
                    pass
                    if some_objects_not_in_the_scene == True:
                        self.report({'INFO'}, f"Some objects are not in the current scene")
                #pass
            pass
        pass

        return {'FINISHED'}

class SvOB3BSyncSceneObjectWithListMK4(bpy.types.Operator, SvGenericNodeLocator):

    bl_idname = "node.sv_ob3b_sync_scene_object_with_list_mk4"
    bl_label = ""
    bl_options = {'INTERNAL'}

    description_text: bpy.props.StringProperty(default='')

    @classmethod
    def description(cls, context, properties):
        s = properties.description_text
        return s

    def sv_execute(self, context, node):
        node.sync_active_object_in_scene_with_list(self)

class SvOB3BInRemoveDuplicatesObjectsInListMK4(bpy.types.Operator, SvGenericNodeLocator):

    bl_idname = "node.sv_ob3b_remove_duplicates_objects_in_list"
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

class SvOB3BCallbackMK4(bpy.types.Operator, SvGenericNodeLocator):

    bl_idname = "node.ob3b_callback_mk4"
    bl_label = "Object In mk4 callback"
    bl_options = {'INTERNAL'}

    fn_name: bpy.props.StringProperty(default='')

    def sv_execute(self, context, node):
        """
        returns the operator's 'self' too to allow the code being called to
        print from self.report.
        """
        getattr(node, self.fn_name)(self)

def get_vertgroups(mesh):
    return [k for k,v in enumerate(mesh.vertices) if v.groups.values()]

numpy_socket_names = ['vertices', 'edges', 'vertex_normals', 'material_idx', 'polygon_areas', 'polygon_centers', 'polygon_normals']


class SvGetObjectsDataMK4(Show3DProperties, SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Object Info
    Tooltip: Get Scene Objects into Sverchok Tree
    """

    bl_idname = 'SvGetObjectsDataMK4'
    bl_label = 'Get Objects Data'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_OBJECTS_IN'

    @property
    def is_scene_dependent(self):
        return (not self.inputs['objects'].is_linked) and (self.inputs['objects'].object_ref_pointer
                                                           or self.object_names)

    @property
    def is_animation_dependent(self):
        return (not self.inputs['objects'].is_linked) and (self.inputs['objects'].object_ref_pointer
                                                           or self.object_names)

    def hide_show_versgroups(self, context):
        outs = self.outputs
        showing_vg = 'Vers_grouped' in outs

        if self.vergroups and not showing_vg:
            outs.new('SvStringsSocket', 'Vers_grouped')
        elif not self.vergroups and showing_vg:
            outs.remove(outs['Vers_grouped'])

    modifiers: bpy.props.BoolProperty(
        name='Post',
        description='Apply modifier geometry to import (original untouched)',
        default=False, update=updateNode) # type: ignore

    vergroups: bpy.props.BoolProperty(
        name='Verts Groups',
        description='Use vertex groups to nesty insertion',
        default=False, update=hide_show_versgroups) # type: ignore

    sort: bpy.props.BoolProperty(
        name='Sort',
        description='sorting inserted objects by names',
        default=True, update=updateNode) # type: ignore

    object_names: bpy.props.CollectionProperty(type=SvOB3BDataCollectionMK4) # type: ignore
    minimal_node_ui: bpy.props.BoolProperty(default=False)
    object_names_ui_minimal: bpy.props.BoolProperty(default=False, description='Minimize table view')

    active_obj_index: bpy.props.IntProperty() # type: ignore

    out_np: bpy.props.BoolVectorProperty(
        name="Output Numpy",
        description="Output NumPy arrays (makes node faster)",
        size=7, update=updateNode) # type: ignore

    output_np_all: bpy.props.BoolProperty(
        name='Output all numpy',
        description='Output numpy arrays if possible',
        default=False, update=updateNode) # type: ignore
    
    apply_matrix: bpy.props.BoolProperty(
        name = "Apply matrices",
        description = "Apply objects matrices",
        default = True,
        update = updateNode) # type: ignore
    
    mesh_join : bpy.props.BoolProperty(
        name = "Mesh Join",
        description = "If checked, join mesh elements into one object",
        default = False,
        update = updateNode) # type: ignore

    display_types = [
            ('BOUNDS', "", "BOUNDS: Display the bounds of the object", "MATPLANE", 0),
            ('WIRE', "", "WIRE: Display the object as a wireframe", "MESH_CUBE", 1),
            ('SOLID', "", "SOLID: Display the object as a solid (if solid drawing is enabled in the viewport)", "SNAP_VOLUME", 2),  #custom_icon("SV_MAKE_SOLID")
            ('TEXTURED', "", "TEXTURED: Display the object with textures (if textures are enabled in the viewport)", "TEXTURE",  3),
        ]
    
    def update_display_type(self, context):
        for item in self.object_names:
            if item.object_pointer:
                #if item.exclude==False:
                item.object_pointer.display_type=self.display_type
        return
    
    display_type : bpy.props.EnumProperty(
        name = "Display Types",
        items = display_types,
        default = 'WIRE',
        update = update_display_type) # type: ignore
    
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
        update = update_render_type) # type: ignore
    
    align_3dview_types = [
            ('ISOLATE_CURRENT', "", "Toggle local view with only current selected object in the list\nPress again to restore view", "PIVOT_CURSOR", 0),
            ('ISOLATE_ALL', "", "Toggle local view with all objects in the list\nPress again to restore view", "PIVOT_INDIVIDUAL", 1),
        ]


    def _verts_sockets_update(self, context):
        for name in ['vertices_select', 'vertices_crease', 'vertices_bevel_weight']:
            self.outputs[name].hide = not(self.enable_verts_attribute_sockets)

    def verts_sockets_update(self, context):
        self._verts_sockets_update(context)
        updateNode(self, context)

    def _edges_sockets_update(self, context):
        for name in ['edges_select', 'edges_seams', 'edges_sharps', 'edges_crease', 'edges_bevel_weight',]:
            self.outputs[name].hide = not(self.enable_edges_attribute_sockets)

    def edges_sockets_update(self, context):
        self._edges_sockets_update(context)
        updateNode(self, context)

    def _polygons_sockets_update(self, context):
        for name in ['polygon_selects', 'polygon_smooth', ]:
            self.outputs[name].hide = not(self.enable_polygons_attribute_sockets)
    def polygons_sockets_update(self, context):
        self._polygons_sockets_update(context)
        updateNode(self, context)

    enable_verts_attribute_sockets: bpy.props.BoolProperty(
        name = "Show verts attribute sockets",
        description = "Show additional sockets for verts attributes:\n1. select\n2. crease\n3. bevel weight",
        default = False,
        update = verts_sockets_update) # type: ignore

    enable_edges_attribute_sockets: bpy.props.BoolProperty(
        name = "Show edges attribute sockets",
        description = "Show additional sockets for edges attributes:\n1. select\n2. sharp\n3. seams\n4. crease\n4. bevel weight",
        default = False,
        update = edges_sockets_update) # type: ignore

    enable_polygons_attribute_sockets: bpy.props.BoolProperty(
        name = "Show polygons attribute sockets",
        description = "Show additional sockets for faces attributes:\n1. select\n2. smooth",
        default = False,
        update = polygons_sockets_update) # type: ignore
    
    vertex_attribute_types = [
        ('SELECTED', "", "Get faces indicex, currently selected", "FACESEL", 0),
        ('ACTIVE_FACE_MAP', "", "Get faces indices, currently actived in Face Maps of object", "FACE_MAPS", 1),
    ]

    vertex_attribute_type : bpy.props.EnumProperty(
        name = "Render Types",
        items = vertex_attribute_types,
        default = 'SELECTED',
        update = updateNode) # type: ignore

    def update_align_3dview(self, context):
        if len(self.object_names)==0:
            return
        obj_in_list = self.object_names[self.active_obj_index]
        if obj_in_list:
            # reset all selections
            for obj in bpy.context.selected_objects:
                obj.select_set(False)
            
            # select all objects in list of this node
            if self.align_3dview_type=='ISOLATE_ALL':
                for item in self.object_names:
                    if item.object_pointer:
                        item.object_pointer.select_set(True)

            if obj_in_list.object_pointer:
                obj_in_list.object_pointer.select_set(True)
                bpy.context.view_layer.objects.active = obj_in_list.object_pointer

            for area in bpy.context.screen.areas:
                if area.type == 'VIEW_3D':
                    ctx = bpy.context.copy()
                    ctx['area'] = area
                    ctx['region'] = area.regions[-1]
                    # test if current mode is local view: https://blender.stackexchange.com/questions/290669/checking-for-object-being-in-local-view
                    if self.align_3dview_type_previous_value!=self.align_3dview_type and area.spaces.active.local_view:
                        bpy.ops.view3d.localview(ctx, frame_selected=False)
                    self.align_3dview_type_previous_value = self.align_3dview_type
                    bpy.ops.view3d.localview(ctx, frame_selected=False)
                    #bpy.ops.view3d.view_selected(ctx)
                    break

            pass
        return
    
    align_3dview_type : bpy.props.EnumProperty(
        name = "Local View",
        items = align_3dview_types,
        default = 'ISOLATE_CURRENT',
        update = update_align_3dview) # type: ignore
    
    align_3dview_type_previous_value : bpy.props.EnumProperty(
        name = "Local View",
        items = align_3dview_types,
        default = 'ISOLATE_CURRENT') # type: ignore

    def migrate_from(self, old_node):
        self.outputs["vertices_select"]         .hide = not(self.enable_verts_attribute_sockets)
        self.outputs["vertices_crease"]         .hide = not(self.enable_verts_attribute_sockets)
        self.outputs["vertices_bevel_weight"]   .hide = not(self.enable_verts_attribute_sockets)
        self.outputs["edges_select"]            .hide = not(self.enable_edges_attribute_sockets)
        self.outputs["edges_crease"]            .hide = not(self.enable_edges_attribute_sockets)
        self.outputs["edges_seams"]             .hide = not(self.enable_edges_attribute_sockets)
        self.outputs["edges_sharps"]            .hide = not(self.enable_edges_attribute_sockets)
        self.outputs["edges_bevel_weight"]      .hide = not(self.enable_edges_attribute_sockets)
        self.outputs["polygon_selects"]         .hide = not(self.enable_polygons_attribute_sockets)
        self.outputs["polygon_smooth"]          .hide = not(self.enable_polygons_attribute_sockets)
    
    def draw_vertices_out_socket(self, socket, context, layout):
        layout.label(text=f'{socket.label} ')
        layout.prop(self, 'enable_verts_attribute_sockets', icon='STICKY_UVS_DISABLE', text='', toggle=True)
        if socket.is_linked:  # linked INPUT or OUTPUT
            layout.label(text=f". {socket.objects_number or ''}")
        elif socket.is_output:  # unlinked OUTPUT
            layout.separator()

    def draw_edges_out_socket(self, socket, context, layout):
        layout.prop(self, 'hide_render_type', expand=True)
        layout.separator()
        layout.prop(self, 'align_3dview_type', expand=True)
        layout.separator()
        layout.label(text=f'  {socket.label} ')
        layout.prop(self, 'enable_edges_attribute_sockets', icon='MESH_DATA', text='', toggle=True)
        if socket.is_linked:  # linked INPUT or OUTPUT
            layout.label(text=f". {socket.objects_number or ''}")
        elif socket.is_output:  # unlinked OUTPUT
            layout.separator()

    def draw_polygons_out_socket(self, socket, context, layout):
        layout.prop(self, 'display_type', expand=True, text='')
        layout.separator()
        layout.label(text=f'{socket.label} ')
        layout.prop(self, 'enable_polygons_attribute_sockets', icon='FILE_3D', text='', toggle=True)
        if socket.is_linked:  # linked INPUT or OUTPUT
            layout.label(text=f". {socket.objects_number or ''}")
        elif socket.is_output:  # unlinked OUTPUT
            layout.separator()

    def sv_init(self, context):
        #new = self.outputs.new
        self.width = 225
        
        self.inputs.new('SvObjectSocket'   , "objects")

        self.outputs.new('SvVerticesSocket', "vertices")
        self.outputs.new('SvStringsSocket' , "edges")
        self.outputs.new('SvStringsSocket' , "polygons")
        self.outputs.new('SvStringsSocket' , "vertices_select")
        self.outputs.new('SvStringsSocket' , "vertices_crease")
        self.outputs.new('SvStringsSocket' , "vertices_bevel_weight")
        self.outputs.new('SvStringsSocket' , "edges_select")
        self.outputs.new('SvStringsSocket' , "edges_crease")
        self.outputs.new('SvStringsSocket' , "edges_seams")
        self.outputs.new('SvStringsSocket' , "edges_sharps")
        self.outputs.new('SvStringsSocket' , "edges_bevel_weight")
        self.outputs.new('SvStringsSocket' , "polygon_selects")
        self.outputs.new('SvStringsSocket' , "polygon_smooth")
        self.outputs.new('SvVerticesSocket', "vertex_normals")
        self.outputs.new('SvStringsSocket' , "material_idx")
        self.outputs.new('SvStringsSocket' , "polygon_areas")
        self.outputs.new('SvVerticesSocket', "polygon_centers")
        self.outputs.new('SvVerticesSocket', "polygon_normals")
        self.outputs.new('SvMatrixSocket'  , "matrix")
        self.outputs.new('SvObjectSocket'  , "object")

        self.inputs ["objects"]         .label = "Objects"

        self.outputs["vertices"]                .label = "Vertices"
        self.outputs["edges"]                   .label = "Edges"
        self.outputs["polygons"]                .label = "Polygons"
        self.outputs["vertices_select"]         .label = "(*) Vertices Select"
        self.outputs["vertices_crease"]         .label = "(*) Vertices Crease"
        self.outputs["vertices_bevel_weight"]   .label = "(*) Vertices Bevel Weight"
        self.outputs["edges_select"]            .label = "(|) Edges Select"
        self.outputs["edges_seams"]             .label = "(|) Edges Seam"
        self.outputs["edges_sharps"]            .label = "(|) Edges Sharp"
        self.outputs["edges_crease"]            .label = "(|) Edges Crease"
        self.outputs["edges_bevel_weight"]      .label = "(|) Edges Bevel Weight"
        self.outputs["polygon_selects"]         .label = "(+) Polygons Select"
        self.outputs["polygon_smooth"]          .label = "(+) Polygons Smooth"
        self.outputs["vertex_normals"]          .label = "Vertex Normals"
        self.outputs["material_idx"]            .label = "Material Idx"
        self.outputs["polygon_areas"]           .label = "Polygon Areas"
        self.outputs["polygon_centers"]         .label = "Polygon Centers"
        self.outputs["polygon_normals"]         .label = "Polygon Normals"
        self.outputs["matrix"]                  .label = "Matrix"
        self.outputs["object"]                  .label = "Object"

        self.outputs["vertices_select"]         .hide = not(self.enable_verts_attribute_sockets)
        self.outputs["vertices_crease"]         .hide = not(self.enable_verts_attribute_sockets)
        self.outputs["vertices_bevel_weight"]   .hide = not(self.enable_verts_attribute_sockets)
        self.outputs["edges_select"]            .hide = not(self.enable_edges_attribute_sockets)
        self.outputs["edges_seams"]             .hide = not(self.enable_edges_attribute_sockets)
        self.outputs["edges_sharps"]            .hide = not(self.enable_edges_attribute_sockets)
        self.outputs["edges_crease"]            .hide = not(self.enable_edges_attribute_sockets)
        self.outputs["edges_bevel_weight"]      .hide = not(self.enable_edges_attribute_sockets)
        self.outputs["polygon_selects"]         .hide = not(self.enable_polygons_attribute_sockets)
        self.outputs["polygon_smooth"]          .hide = not(self.enable_polygons_attribute_sockets)

        self.outputs["vertices"].custom_draw = 'draw_vertices_out_socket'
        self.outputs["edges"].custom_draw = 'draw_edges_out_socket'
        self.outputs["polygons"].custom_draw = 'draw_polygons_out_socket'

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
        ops.report({'INFO'}, f"Removed {len(remove_idx)} object(s) ")
        return

    def sync_active_object_in_scene_with_list(self, ops):
        object_synced = False
        if bpy.context.view_layer.objects.active:
            active_object = bpy.context.view_layer.objects.active
            first_duplicated = None
            sync_index = None
            object_name_active = self.object_names[self.active_obj_index]
            for I, item in enumerate(self.object_names):
                if object_name_active.object_pointer and object_name_active.object_pointer == active_object and I<=self.active_obj_index:
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
            item.name = name
            item.icon = 'OUTLINER_OB_' + bpy.data.objects[name].type

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
            item = self.object_names.add()
            item.object_pointer = bpy.data.objects[name]
            item.name = name
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

    def set_objects_selected_scene(self, ops):
        """
        Collect selected objects
        """
        if len(self.object_names)>0:
            for item in self.object_names:
                if item.object_pointer:
                    if bpy.context.scene in item.object_pointer.users_scene:
                        item.object_pointer.select_set(True)
                    else:
                        print(f'Object {item.object_pointer.name} is not on the current scene. You can switch from [{bpy.context.scene.name}] to [{";".join([s.name for s in item.object_pointer.users_scene ])}]')
                pass
        else:
            print(f"No object in list of 'Get objects Data' '{self.name}'")

    def deselect_objects_from_scene(self, ops):
        """
        Collect selected objects
        """
        if len(self.object_names)>0:
            for item in self.object_names:
                if item.object_pointer:
                    if bpy.context.scene in item.object_pointer.users_scene:
                        item.object_pointer.select_set(False)
                    else:
                        print(f'Object {item.object_pointer.name} is not on the current scene. You can switch from [{bpy.context.scene.name}] to [{";".join([s.name for s in item.object_pointer.users_scene ])}]')
                pass
        else:
            print(f"No object in list of 'Get objects Data' '{self.name}'")

        self.process_node(None)


    def select_objs(self, ops):
        """select all objects referenced by node"""
        for item in self.object_names:
            item.object_pointer.select = True

        if not self.object_names:
            ops.report({'WARNING'}, "Warning, no object associated with the obj in Node")
        pass

    @property
    def by_input(self):
        return self.inputs[0].object_ref_pointer is not None or self.inputs[0].is_linked

    def sv_draw_buttons(self, context, layout):
        col = layout.column(align=True)
        by_input = self.by_input
        if not by_input:
            row = col.row()

            op_text = "Get selection"  # fallback
            callback = SvOB3BCallbackMK4.bl_idname

            if self.prefs_over_sized_buttons:
                row.scale_y = 4.0
                op_text = "G E T"

            self.wrapper_tracked_ui_draw_op(row, callback, text=op_text).fn_name = 'get_objects_from_scene'

        grid = layout.grid_flow(row_major=False, columns=0, align=True)
        grid.column(align=True).prop(self, 'sort')
        grid.column(align=True).prop(self, 'apply_matrix')
        grid.column(align=True).prop(self, 'mesh_join')
        grid.column(align=True).prop(self, 'modifiers')
        grid.column(align=True).prop(self, 'vergroups')

        if not by_input:
            if self.object_names:
                col = layout.column(align=True)
                elem = col.row(align=True)
                elem.alignment='RIGHT'
                self.wrapper_tracked_ui_draw_op(elem, SvOB3BAddObjectsFromSceneUpMK4.bl_idname, text='', icon='ADD')
                self.wrapper_tracked_ui_draw_op(elem, SvOB3BMoveUpMK4.bl_idname, text='', icon='TRIA_UP')
                self.wrapper_tracked_ui_draw_op(elem, SvOB3BMoveDownMK4.bl_idname, text='', icon='TRIA_DOWN')
                self.wrapper_tracked_ui_draw_op(elem, SvOB3BHighlightProcessedObjectsInSceneMK4.bl_idname, text='', icon='GROUP_VERTEX')
                self.wrapper_tracked_ui_draw_op(elem, SvOB3BHighlightAllObjectsInSceneMK4.bl_idname, text='', icon='OUTLINER_OB_POINTCLOUD')
                self.wrapper_tracked_ui_draw_op(elem, SvOB3BSyncSceneObjectWithListMK4.bl_idname, icon='TRACKING_BACKWARDS_SINGLE', text='', emboss=True, description_text = 'Select the scene active object in list\n(Cycle between duplicates if there are any)')
                
                set_object_names = set([o.name for o in self.object_names if o.object_pointer])
                if len(set_object_names)<len(self.object_names):
                    icon = 'AUTOMERGE_ON'
                    description_text = f'Remove any duplicates objects in list\nCount of duplicates objects: {len(self.object_names)-len(set_object_names)}'
                else:
                    icon = 'AUTOMERGE_OFF'
                    description_text = 'Remove any duplicates objects in list.\nNo duplicates objects in list now'
                description_text += "\n\nShift-Cliсk - skip confirmation dialog"
                self.wrapper_tracked_ui_draw_op(elem, SvOB3BInRemoveDuplicatesObjectsInListMK4.bl_idname, text='', icon=icon, description_text=description_text)
                elem.separator()
                self.wrapper_tracked_ui_draw_op(elem, SvOB3BClearObjectsFromListMK4.bl_idname, text='', icon='CANCEL')
                elem.separator()
                if self.object_names_ui_minimal:
                    elem.prop(self, "object_names_ui_minimal", text='', toggle=True, icon='FULLSCREEN_EXIT')
                else:
                    elem.prop(self, "object_names_ui_minimal", text='', toggle=True, icon='FULLSCREEN_ENTER')


                col.template_list("SVOB3B_UL_NamesListMK4", "", self, "object_names", self, "active_obj_index", rows=3, item_dyntip_propname='test_text1')
                
            else:
                layout.label(text='--None--')
        pass

    def sv_draw_buttons_ext(self, context, layout):
        r = layout.column(align=True)
        row = r.row(align=True)
        row.label(text="Output Numpy:")
        row.prop(self, 'output_np_all', text='If possible', toggle=True)
        if not self.output_np_all:
            for i in range(7):
                r.prop(self, "out_np", index=i, text=numpy_socket_names[i], toggle=True)

    def rclick_menu(self, context, layout):
        '''right click sv_menu items'''
        layout.label(text="Output Numpy:")
        layout.prop(self, 'output_np_all', text='All', toggle=True)
        if not self.output_np_all:
            for i in range(7):
                layout.prop(self, "out_np", index=i, text=numpy_socket_names[i], toggle=True)

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, "draw_3dpanel", icon="PLUGIN")
        self.sv_draw_buttons_ext(context, layout)

    def draw_buttons_3dpanel(self, layout):
        if not self.by_input:
            callback = SvOB3BCallbackMK4.bl_idname
            row = layout.row(align=True)
            row.label(text=self.label if self.label else self.name)
            colo = row.row(align=True)
            colo.scale_x = 1.6

            self.wrapper_tracked_ui_draw_op(colo, callback, text='Get').fn_name = 'get_objects_from_scene'
        else:
            row = layout.row(align=True)
            row.label(text=self.label if self.label else self.name)
            self.draw_animatable_buttons(row, icon_only=True)

    def get_materials_from_bmesh(self, bm):
        return [face.material_index for face in bm.faces[:]]

    def process(self):
        objs = self.inputs[0].sv_get(default=[[]])
        if not self.object_names and not objs[0]:
            return
        
        data_objects = bpy.data.objects
        outputs = self.outputs

        vers_out_grouped = []

        o_vertices, o_edges, o_polygons, o_vertices_select, o_vertices_crease, o_vertices_bevel_weight, o_edges_select, o_edges_crease, o_edges_seams, o_edges_sharps, o_edges_bevel_weight, o_polygon_selects, o_polygon_smooth, o_vertex_normals, o_material_idx, o_polygon_areas, o_polygon_centers, o_polygon_normals, o_matrices, o_objects = [s.is_linked for s in self.outputs[:20]]
        l_vertices, l_edges, l_polygons, l_vertices_select, l_vertices_crease, l_vertices_bevel_weight, l_edges_select, l_edges_crease, l_edges_seams, l_edges_sharps, l_edges_bevel_weight, l_polygon_selects, l_polygon_smooth, l_vertex_normals, l_material_idx, l_polygon_areas, l_polygon_centers, l_polygon_normals, l_matrices = [[] for s in self.outputs[:19]]
        sv_depsgraph = None
        if self.modifiers:
            sv_depsgraph = bpy.context.evaluated_depsgraph_get()

        out_np = self.out_np if not self.output_np_all else [True for i in range(7)]
        if isinstance(objs[0], list):
            objs = objs[0]
        if not objs:
            objs = (o.object_pointer for o in self.object_names if o.exclude==False and o.object_pointer)

        # iterate through references
        for obj in objs:

            if not obj:
                continue

            mtrx = obj.matrix_world
            # if self.apply_matrix==True:
            #     mtrx = obj.matrix_world
            # else:
            #     mtrx = Matrix()

            if obj.type in {'EMPTY', 'CAMERA', 'LAMP', 'LIGHT' }:
                if o_matrices:
                    l_matrices.append(mtrx)
                if o_vertices:
                    verts = []
                if o_edges:
                    edgs = []
                if o_polygons:
                    pols = []
                if o_vertices_select:
                    vertices_select1 = []
            else:
                try:
                    if obj.mode == 'EDIT' and obj.type == 'MESH':
                        # Mesh objects do not currently return what you see
                        # from 3dview while in edit mode when using obj.to_mesh.
                        me = obj.data
                        bm = bmesh.from_edit_mesh(me)
                        # verts, edgs, pols = pydata_from_bmesh(bm)

                        if o_vertices:
                            if self.apply_matrix:
                                verts = [ (mtrx @ Vector(v.co[:]))[:] for v in bm.verts]  # v.co is a Vector()
                            else:
                                verts = [ (Vector(v.co[:]))[:] for v in bm.verts]  # v.co is a Vector()
                        if o_edges:
                            edgs = [[e.verts[0].index, e.verts[1].index] for e in bm.edges]
                        if o_polygons:
                            pols = [[i.index for i in p.verts] for p in bm.faces]
                        if o_vertices_select:
                            vertices_select1 = [v.select for v in bm.verts]

                        if o_vertices_crease:
                            if hasattr(bm.verts.layers, 'crease'):
                                # before blender 4.0
                                crease_layer = bm.verts.layers.crease.verify()
                                vertices_crease1 = [v[crease_layer] for v in bm.verts]
                            elif hasattr(bm.verts.layers, 'float') and 'crease_vert' in bm.verts.layers.float:
                                # after blender 4.0
                                crease_vert_layer = bm.verts.layers.float.get('crease_vert')
                                vertices_crease1 = [v[crease_vert_layer] for v in bm.verts]
                            else:
                                # if no layer then all creases are 0.0
                                vertices_crease1 = [0.0 for v in bm.verts]

                        if o_vertices_bevel_weight:
                            if hasattr(bm.verts.layers, 'bevel_weight'):
                                # before blender 4.0
                                bevel_weight_layer = bm.verts.layers.bevel_weight.verify()
                                vertices_bevel_weight1 = [v[bevel_weight_layer] for v in bm.verts]
                            elif hasattr(bm.verts.layers, 'float') and 'bevel_weight_vert' in bm.verts.layers.float:
                                # after blender 4.0
                                bevel_weight_vert_layer = bm.verts.layers.float.get('bevel_weight_vert')
                                vertices_bevel_weight1 = [v[bevel_weight_vert_layer] for v in bm.verts]
                            else:
                                # if no layer then all bevels are 0.0
                                vertices_bevel_weight1 = [0.0 for v in bm.verts]

                        if o_edges_select:
                            edges_select1 = [e.select for e in bm.edges]
                        if o_edges_seams:
                            edges_seams1 = [e.seam for e in bm.edges]
                        if o_edges_sharps:
                            edges_sharps1 = [not(e.smooth) for e in bm.edges]

                        if o_edges_crease:
                            if hasattr(bm.edges.layers, "crease"):
                                # before blender 4.0
                                crease_layer = bm.edges.layers.crease.verify()
                                edges_crease1 = [ e[crease_layer] for e in bm.edges ]
                            elif hasattr(bm.edges.layers, 'float') and 'crease_edge' in bm.edges.layers.float:
                                # after blender 4.0
                                cel = bm.edges.layers.float.get("crease_edge") # crease edge layer
                                edges_crease1 = [e[cel] for e in bm.edges]
                            else:
                                # edges has no data for crease (not initalized)
                                edges_crease1 = [0.0 for e in bm.edges]
                            pass

                        if o_edges_bevel_weight:
                            if hasattr(bm.edges.layers, "bevel_weight"):
                                # before blender 4.0
                                bevel_weight_layer = bm.edges.layers.bevel_weight.verify()
                                edges_bevel_weight1 = [e[bevel_weight_layer] for e in bm.edges]
                            elif hasattr(bm.edges.layers, 'float') and 'bevel_weight_edge' in bm.edges.layers.float:
                                # after blender 4.0
                                bevel_weight_layer = bm.edges.layers.float.get("bevel_weight_edge") # crease edge layer
                                edges_bevel_weight1 = [e[bevel_weight_layer] for e in bm.edges]
                            else:
                                # edges has no data for bevel (not initalized)
                                edges_bevel_weight1 = [0.0 for e in bm.edges]
                            pass

                        if o_polygon_selects:
                            polygon_selects1 = [f.select for f in bm.faces]
                        if o_polygon_smooth:
                            polygon_smooth1 = [f.smooth for f in bm.faces]
                        if self.vergroups:
                            vert_groups      = get_vertgroups(obj.data)
                        if o_vertex_normals:
                            vertex_normals = [ v.normal[:] for v in bm.verts] # v.normal is a Vector()
                        if o_material_idx:
                            material_indexes = self.get_materials_from_bmesh(bm)
                        if o_polygon_areas:
                            polygons_areas = [ p.calc_area() for p in bm.faces ]
                        if o_polygon_centers:
                            polygon_centers = [ p.calc_center_median()[:] for p in bm.faces ]
                        if o_polygon_normals:
                            polygon_normals = [ p.normal[:] for p in bm.faces ]

                        del bm

                    else: # do in Object mode

                        # https://developer.blender.org/T99661
                        if obj.type == 'CURVE' and obj.mode == 'EDIT' and bpy.app.version[:2] == (3, 2):
                            raise ReadingObjectDataError("Does not support curves in edit mode in Blender 3.2")
                        elif self.modifiers:
                            if obj.type in ['POINTCLOUD']:
                                if sv_depsgraph is None:
                                    sv_depsgraph = bpy.context.evaluated_depsgraph_get()
                                obj = sv_depsgraph.objects[obj.name]
                                obj_eval = obj.evaluated_get(sv_depsgraph)
                                obj_data = obj_eval.data
                            else:
                                obj = sv_depsgraph.objects[obj.name]
                                obj_data = obj.to_mesh(preserve_all_data_layers=True, depsgraph=sv_depsgraph)
                        else:
                            if obj.type in ['META']:
                                if sv_depsgraph is None:
                                    sv_depsgraph = bpy.context.evaluated_depsgraph_get()
                                obj = sv_depsgraph.objects[obj.name]
                                obj_data = obj.to_mesh(preserve_all_data_layers=True, depsgraph=sv_depsgraph)
                            elif obj.type in ['POINTCLOUD']:
                                if sv_depsgraph is None:
                                    sv_depsgraph = bpy.context.evaluated_depsgraph_get()
                                obj = sv_depsgraph.objects[obj.name]
                                #obj_data = obj.to_mesh(preserve_all_data_layers=True, depsgraph=sv_depsgraph)
                                obj_eval = obj.evaluated_get(sv_depsgraph)
                                obj_data = obj_eval.data
                            else:
                                obj_data = obj.to_mesh()
                        
                        T, R, S = mtrx.decompose()

                        if obj.type in ['POINTCLOUD']:
                            if o_vertices:
                                verts            = [ ((mtrx @ v.co)[:] if self.apply_matrix else v.co)[:] for v in obj_data.points]  # v.co is a Vector()
                            if o_edges:
                                edgs             = []
                            if o_polygons:
                                pols             = []
                            if o_vertices_select:
                                vertices_select1 = []
                            if o_vertices_crease:
                                vertices_crease1 = []
                            if o_vertices_bevel_weight:
                                vertices_bevel_weight1 = []
                            if o_edges_select:
                                edges_select1 = []
                            if o_edges_seams:
                                edges_seams1 = []
                            if o_edges_sharps:
                                edges_sharps1 = []
                            if o_edges_crease:
                                edges_crease1 = []
                            if o_edges_bevel_weight:
                                edges_bevel_weight1 = []
                            if o_polygon_selects:
                                polygon_selects1 = []
                            if o_polygon_smooth:
                                polygon_smooth1 = []
                            if self.vergroups:
                                vert_groups      = []
                            if o_vertex_normals:
                                vertex_normals   = [] # v.normal is a Vector(). Update. Blender 3.6.3 crash in no wrap Vector(v.normal). I think this is after line "obj.to_mesh_clear()"
                            if o_material_idx:
                                #material_indexes = read_materials_idx(obj_data, out_np[3])
                                material_indexes = []
                            if o_polygon_areas:
                                polygons_areas   = []
                            if o_polygon_centers:
                                polygon_centers  = []
                            if o_polygon_normals:
                                polygon_normals  = []

                        else:
                            if o_vertices:
                                verts            = [ ((mtrx @ v.co)[:] if self.apply_matrix else v.co)[:] for v in obj_data.vertices]  # v.co is a Vector()
                            if o_edges:
                                edgs             = [[ e.vertices[0], e.vertices[1] ] for e in obj_data.edges]
                            if o_polygons:
                                pols             = [list(p.vertices) for p in obj_data.polygons]
                            if o_vertices_select:
                                vertices_select1 = [v.select for v in obj_data.vertices]

                            if o_vertices_crease:
                                if hasattr(obj_data, 'vertex_creases') and (obj_data.vertex_creases is not None) and hasattr(obj_data.vertex_creases, '__len__') and len(obj_data.vertex_creases)>0:
                                    # it is very hard to identify creases in object mode in blender before 4.0
                                    creases = obj_data.vertex_creases[0]
                                    vertices_crease1 = [creases.data[i].value for i, v in enumerate(obj_data.vertices)]
                                elif 'crease_vert' in obj_data.attributes:
                                    # get creases of vertices in Blender 4.x
                                    vertices_crease1 = [e.value for e in obj_data.attributes['crease_vert'].data]
                                else:
                                    # if no data then all creases are 0.0
                                    vertices_crease1 = [0.0 for i in range( len(obj_data.vertices) )]
                                pass

                            if o_vertices_bevel_weight:
                                if 'bevel_weight_vert' in obj_data.attributes:
                                    # after Blender 4.0
                                    vertices_bevel_weight1 = [e.value for e in obj_data.attributes['bevel_weight_vert'].data]
                                elif len(obj_data.vertices)>0 and hasattr(obj_data.vertices[0], 'bevel_weight'):
                                    # before Blender 4.0
                                    vertices_bevel_weight1 = [v.bevel_weight for v in obj_data.vertices]
                                else:
                                    # vertices has no data in e (not initalized)
                                    vertices_bevel_weight1 = [0.0 for i in range( len(obj_data.vertices) )]
                                pass

                            if o_edges_select:
                                edges_select1 = [e.select for e in obj_data.edges]
                            if o_edges_seams:
                                edges_seams1 = [e.use_seam for e in obj_data.edges]
                            if o_edges_sharps:
                                edges_sharps1 = [e.use_edge_sharp for e in obj_data.edges]

                            if o_edges_crease:
                                if 'crease_edge' in obj_data.attributes:
                                    # after blender 4.0
                                    edges_crease1 = [e.value for e in obj_data.attributes['crease_edge'].data]
                                elif len(obj_data.edges)>0 and hasattr(obj_data.edges[0], 'crease'):
                                    # before Blender 4.0
                                    edges_crease1 = [e.crease for e in obj_data.edges]
                                else:
                                    # edges has no data in e (not initalized)
                                    edges_crease1 = [0.0 for e in obj_data.edges]
                                pass
                            
                            if o_edges_bevel_weight:
                                if 'bevel_weight_edge' in obj_data.attributes:
                                    # after Blender 4.0
                                    edges_bevel_weight1 = [e.value for e in obj_data.attributes['bevel_weight_edge'].data]
                                elif len(obj_data.edges)>0 and hasattr(obj_data.edges[0], 'bevel_weight'):
                                    # before Blender 4.0
                                    edges_bevel_weight1 = [e.bevel_weight for e in obj_data.edges]
                                else:
                                    # edges has no data for bevel (not initalized)
                                    edges_bevel_weight1 = [0.0 for e in obj_data.edges]
                                pass
                                    
                            if o_polygon_selects:
                                polygon_selects1 = [p.select for p in obj_data.polygons]
                            if o_polygon_smooth:
                                polygon_smooth1 = [p.use_smooth for p in obj_data.polygons]
                            if self.vergroups:
                                vert_groups      = get_vertgroups(obj_data)
                            if o_vertex_normals:
                                vertex_normals   = [ ((   R @ v.co) if self.apply_matrix else v.normal)[:] for v in obj_data.vertices ] # v.normal is a Vector(). Update. Blender 3.6.3 crash in no wrap Vector(v.normal). I think this is after line "obj.to_mesh_clear()"
                            if o_material_idx:
                                material_indexes = read_materials_idx(obj_data, out_np[3])
                            if o_polygon_areas:
                                polygons_areas   = [ polygon.area for polygon in obj_data.polygons]
                            if o_polygon_centers:
                                polygon_centers  = [ ((mtrx @ polygon.center) if self.apply_matrix else polygon.center)[:] for polygon in obj_data.polygons]
                            if o_polygon_normals:
                                polygon_normals  = [ ((   R @ polygon.normal) if self.apply_matrix else polygon.normal)[:] for polygon in obj_data.polygons]

                    if o_matrices:
                        l_matrices.append(mtrx)

                    obj.to_mesh_clear()
                except ReadingObjectDataError as _ex:
                    raise
                except Exception as err:
                    # it's not clear which cases this try catch should handle
                    # probably it should skip wrong object types
                    self.debug('failure in process between frozen area', self.name, err)

            pass
        
            if o_vertices:
                l_vertices.append( verts )
            if o_edges:
                l_edges.append( edgs )
            if o_polygons:
                l_polygons.append( pols )
            if o_vertices_select:
                l_vertices_select.append( vertices_select1 )
            if o_vertices_crease:
                l_vertices_crease.append( vertices_crease1 )
            if o_vertices_bevel_weight:
                l_vertices_bevel_weight.append( vertices_bevel_weight1 )
            if o_edges_select:
                l_edges_select.append( edges_select1 )
            if o_edges_seams:
                l_edges_seams.append( edges_seams1 )
            if o_edges_sharps:
                l_edges_sharps.append( edges_sharps1 )
            if o_edges_crease:
                l_edges_crease.append( edges_crease1 )
            if o_edges_bevel_weight:
                l_edges_bevel_weight.append( edges_bevel_weight1 )
            if o_polygon_selects:
                l_polygon_selects.append( polygon_selects1 )
            if o_polygon_smooth:
                l_polygon_smooth.append( polygon_smooth1 )
            if self.vergroups:
                vers_out_grouped.append( vert_groups )
            if o_vertex_normals:
                l_vertex_normals.append( vertex_normals )
            if o_material_idx:
                l_material_idx.append( material_indexes )
            if o_polygon_areas:
                l_polygon_areas.append( polygons_areas )
            if o_polygon_centers:
                l_polygon_centers.append( polygon_centers )
            if o_polygon_normals:
                l_polygon_normals.append( polygon_normals )

        if self.mesh_join:
            # l_vertices, l_edges, l_polygons, l_vertex_normals, l_material_idx, l_polygon_areas, l_polygon_centers, l_polygon_normals, l_matrices
            offset = 0
            _vertices, _edges, _polygons, _vertices_select, _vertices_crease, _vertices_bevel_weight, _edges_select, _edges_seams, _edges_sharps, _edges_crease, _edges_bevel_weight, _polygon_selects, _polygon_smooth, _vertex_normals, _polygon_areas, _polygon_centers, _polygon_normals, _vg = [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []
            for idx, vertices in enumerate(l_vertices):
                _vertices.extend(vertices)
                if l_edges:
                    _edges.extend( [[i + offset for i in o] for o in l_edges[idx] ] ) # edges
                if l_polygons:
                    _polygons.extend( [[i + offset for i in o] for o in l_polygons[idx] ] ) # polygons
                #_l_vertex_normals.extend( [tuple(i + offset for i in o) for o in ps[idx] ] ) # vers_out_grouped. Skip in mesh_join
                if l_vertices_select:
                    _vertices_select.extend( l_vertices_select[idx] )
                if l_vertices_crease:
                    _vertices_crease.extend( l_vertices_crease[idx] )
                if l_vertices_bevel_weight:
                    _vertices_bevel_weight.extend( l_vertices_bevel_weight[idx] )
                if l_edges_select:
                    _edges_select.extend( l_edges_select[idx] )
                if l_edges_seams:
                    _edges_seams.extend( l_edges_seams[idx] )
                if l_edges_sharps:
                    _edges_sharps.extend( l_edges_sharps[idx] )
                if l_edges_crease:
                    _edges_crease.extend( l_edges_crease[idx] )
                if l_edges_bevel_weight:
                    _edges_bevel_weight.extend( l_edges_bevel_weight[idx] )
                if l_polygon_selects:
                    _polygon_selects.extend( l_polygon_selects[idx] )
                if l_polygon_smooth:
                    _polygon_smooth.extend( l_polygon_smooth[idx] )
                if l_vertex_normals:
                    _vertex_normals.extend( l_vertex_normals[idx] ) # vertex normals
                # _l_material_idx - materia index. Do not change
                # if l_material_idx and len(l_material_idx)>idx:
                #     _l_material_idx.extend( l_material_idx[idx] ) # Skip in mesh_join
                if l_polygon_areas:
                    _polygon_areas.extend( l_polygon_areas[idx] ) # polygon area
                if l_polygon_centers:
                    _polygon_centers.extend( l_polygon_centers[idx] ) # polygon center
                if l_polygon_normals:
                    _polygon_normals.extend( l_polygon_normals[idx] ) # polygon normal
                # if l_matrices: Do not change
                #     _ms.append( l_matrices[idx] ) # matrices. Skip in mesh_join
                if vers_out_grouped:
                    _vg.extend( [ i + offset for i in vers_out_grouped[idx] ] ) # vertex groups
                
                offset += len(vertices)
            
            l_vertices, l_edges, l_polygons, l_vertices_select, l_vertices_crease, l_vertices_bevel_weight, l_edges_select, l_edges_seams, l_edges_sharps, l_edges_crease, l_edges_bevel_weight, l_polygon_selects, l_polygon_smooth, l_vertex_normals, l_polygon_areas, l_polygon_centers, l_polygon_normals, vers_out_grouped = [_vertices], [_edges], [_polygons], [_vertices_select], [_vertices_crease], [_vertices_bevel_weight], [_edges_select], [_edges_seams], [_edges_sharps], [_edges_crease], [_edges_bevel_weight], [_polygon_selects], [_polygon_smooth], [_vertex_normals], [_polygon_areas], [_polygon_centers], [_polygon_normals], [_vg]

        if o_vertices and (out_np[0]):
            l_vertices = [np.array(vert) for vert in l_vertices]
        if o_edges and (out_np[1]):
            l_edges = [np.array(edge) for edge in l_edges]
        # if o_polygons and (out_np[2]):
        #     l_polygons = [np.array(pol)  for pol  in l_polygons]
        # if self.vergroups:
        #     vers_out_grouped = [np.array(group)  for group  in vers_out_grouped]
        if o_vertex_normals and (out_np[2]):
            l_vertex_normals = [np.array(vert_normal)     for vert_normal     in l_vertex_normals]
        if o_material_idx and (out_np[3]):
            l_material_idx = [np.array(material_index)  for material_index  in l_material_idx]
        if o_polygon_areas and (out_np[4]):
            l_polygon_areas = [np.array(polygon_areas)   for polygon_areas   in l_polygon_areas]
        if o_polygon_centers and (out_np[5]):
            l_polygon_centers = [np.array(polygon_centers) for polygon_centers in l_polygon_centers]
        if o_polygon_normals and (out_np[6]):
            l_polygon_normals = [np.array(polygon_normals) for polygon_normals in l_polygon_normals]

        for i, i2 in zip(self.outputs, [l_vertices, l_edges, l_polygons, l_vertices_select, l_vertices_crease, l_vertices_bevel_weight, l_edges_select, l_edges_crease, l_edges_seams, l_edges_sharps, l_edges_bevel_weight, l_polygon_selects, l_polygon_smooth, l_vertex_normals, l_material_idx, l_polygon_areas, l_polygon_centers, l_polygon_normals, l_matrices]):
            if i.is_linked:
                i.sv_set(i2)

        if vers_out_grouped and vers_out_grouped[0]:
            if 'Vers_grouped' in outputs and self.vergroups:
                outputs['Vers_grouped'].sv_set(vers_out_grouped)
        if o_objects:
            if self.by_input:
                outputs['object'].sv_set(objs)
            else:
                outputs['object'].sv_set([data_objects.get(o.name) for o in self.object_names])
            pass
        pass
    pass

    def migrate_from(self, old_node):
        if hasattr(self, 'location_absolute'):
            # Blender 3.0 has no this attribute
            self.location_absolute = old_node.location_absolute
        for I, item in enumerate(old_node.object_names):
            if I<=len(self.object_names)-1:
                if item.name in bpy.data.objects:
                    self.object_names[I].object_pointer = bpy.data.objects[item.name]
        if self.width<305:
            self.width=305
        pass

    def load_from_json(self, node_data: dict, import_version: float):
        '''function to get data when importing from json'''
        data_objects = bpy.data.objects

        if 'object_names' in node_data:
            data_list = node_data.get('object_names')
            if data_list:
                data = json.loads(data_list)
                for I, k in enumerate(data):
                    if len(self.object_names)<=I-1:
                        name    = k['name']
                        exclude = k['exclude']
                        if name in data_objects:
                            self.object_names[I].object_pointer = data_objects[name]
                            pass
                        self.object_names[I].exclude = exclude
                    else:
                        continue
                    pass
        pass

    def save_to_json(self, node_data: list):
        '''function to set data for exporting json'''
        data = []
        for item in self.object_names:
            if item.object_pointer:
                data.append( dict(  name=item.object_pointer.name, exclude=item.exclude ) )
            else:
                data.append( dict(  name='', exclude=item.exclude ) )

        data_json_str = json.dumps(data)
        node_data['object_names'] = data_json_str


classes = [
    SvOB3ItemEmptyOperatorMK4,
    SvOB3BHighlightAllObjectsInSceneMK4,
    SvOB3BHighlightProcessedObjectsInSceneMK4,
    SvOB3BClearObjectsFromListMK4,
    SvOB3BSyncSceneObjectWithListMK4,
    SvOB3BInRemoveDuplicatesObjectsInListMK4,
    SvOB3BMoveDownMK4,
    SvOB3BMoveUpMK4,
    SvOB3BAddObjectsFromSceneUpMK4,
    SvOB3ItemSelectObjectMK4,
    SvOB3BItemEnablerMK4,
    SvOB3BItemRemoveMK4,
    SvOB3BItemOperatorMK4,
    SvOB3BDataCollectionMK4,
    SVOB3B_UL_NamesListMK4,
    SvOB3BCallbackMK4,
    SvGetObjectsDataMK4,
]
register, unregister = bpy.utils.register_classes_factory(classes)
