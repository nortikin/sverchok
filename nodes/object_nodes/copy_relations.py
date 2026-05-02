# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE
from operator import attrgetter

import bpy
from sverchok.data_structure import repeat_last

from sverchok.data_structure import updateNode
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.handle_blender_data import BlModifier
from sverchok.utils.listutils import unwrap_lowest_single_value, unwrap_lowest_single_list
from sverchok.utils.fcurves import get_fcurves, remove_fcurves, copy_fcurves

import bpy
from datetime import datetime

object_params = {
        #'parent'                    : {'node_property_name': 'relations_parent1'                    , 'socket_name': 'relations_parent'                     , 'node_property_name_apply': 'node_parent_apply'                   , 'object_property_name_animation_copy': 'relations_parent_animation_copy'                      , 'object_property_name_copy': 'relations_parent_property_copy'                     , 'node_property_map_mode' : 'relations_parent_map_mode'                    , },
        'parent_type'               : {'node_property_name': 'relations_parent_type1'               , 'socket_name': 'relations_parent_type'                , 'node_property_name_apply': 'node_parent_type_apply'              , 'object_property_name_animation_copy': 'relations_parent_type_animation_copy'                 , 'object_property_name_copy': 'relations_parent_type_property_copy'                , 'node_property_map_mode' : 'relations_parent_type_map_mode'               , },
        'use_parent_final_indices'  : {'node_property_name': 'relations_use_parent_final_indices1'  , 'socket_name': 'relations_use_parent_final_indices'   , 'node_property_name_apply': 'node_use_parent_final_indices_apply' , 'object_property_name_animation_copy': 'relations_use_parent_final_indices_animation_copy'    , 'object_property_name_copy': 'relations_use_parent_final_indices_property_copy'   , 'node_property_map_mode' : 'relations_use_parent_final_indices_map_mode'  , },
        'parent_vertices'           : {'node_property_name': 'relations_parent_vertices1'           , 'socket_name': 'relations_parent_vertices'            , 'node_property_name_apply': 'node_parent_vertices_apply'          , 'object_property_name_animation_copy': 'relations_parent_vertices_animation_copy'             , 'object_property_name_copy': 'relations_parent_vertices_property_copy'            , 'node_property_map_mode' : 'relations_parent_vertices_map_mode'           , },
        'use_camera_lock_parent'    : {'node_property_name': 'relations_use_camera_lock_parent1'    , 'socket_name': 'relations_use_camera_lock_parent'     , 'node_property_name_apply': 'node_use_camera_lock_parent_apply'   , 'object_property_name_animation_copy': 'relations_use_camera_lock_parent_animation_copy'      , 'object_property_name_copy': 'relations_use_camera_lock_parent_property_copy'     , 'node_property_map_mode' : 'relations_use_camera_lock_parent_map_mode'    , },
        'track_axis'                : {'node_property_name': 'relations_track_axis1'                , 'socket_name': 'relations_track_axis'                 , 'node_property_name_apply': 'node_track_axis_apply'               , 'object_property_name_animation_copy': 'relations_track_axis_animation_copy'                  , 'object_property_name_copy': 'relations_track_axis_property_copy'                 , 'node_property_map_mode' : 'relations_track_axis_map_mode'                , },
        'up_axis'                   : {'node_property_name': 'relations_up_axis1'                   , 'socket_name': 'relations_up_axis'                    , 'node_property_name_apply': 'node_up_axis_apply'                  , 'object_property_name_animation_copy': 'relations_up_axis_animation_copy'                     , 'object_property_name_copy': 'relations_up_axis_property_copy'                    , 'node_property_map_mode' : 'relations_up_axis_map_mode'                   , },
        'pass_index'                : {'node_property_name': 'relations_pass_index1'                , 'socket_name': 'relations_pass_index'                 , 'node_property_name_apply': 'node_pass_index_apply'               , 'object_property_name_animation_copy': 'relations_pass_index_animation_copy'                  , 'object_property_name_copy': 'relations_pass_index_property_copy'                 , 'node_property_map_mode' : 'relations_pass_index_map_mode'                , },
        #{'object': '', 'node': 'rigid_body_', },
    }

relations_socket_names = dict()
for (params, params_settings) in object_params.items():
    socket_name = params_settings['socket_name']
    relations_socket_names[socket_name] = params_settings

# Show popup. Example: https://github.com/user-attachments/assets/90107adc-85ce-4b3d-9e75-35c0ac93a32e
def show_popup(message, title="Info", icon='INFO'):
    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)

def copy_object_relations(src_obj, target_obj):
    #bpy.context.view_layer.update()

    new_parent = src_obj
    # if target_obj.parent == new_parent and target_obj.parent_type == 'OBJECT' and target_obj.parent_bone == "":
    #     return
    
    world_matrix = target_obj.matrix_world.copy()

    # target_obj.matrix_world = new_parent.matrix_world.inverted() @ world_matrix
    # target_obj.parent = new_parent
    # target_obj.parent_type = 'OBJECT'
    # target_obj.parent_bone = ""
    # target_obj.matrix_parent_inverse = new_parent.matrix_world.inverted()

    target_obj.parent = None
    target_obj.matrix_world = world_matrix
    target_obj.parent = new_parent
    target_obj.parent_type = 'OBJECT'
    target_obj.parent_bone = ""
    target_obj.matrix_parent_inverse = new_parent.matrix_world.inverted()
    pass

    #bpy.context.view_layer.update()

def updateNodeCopyParent(self, context):
    """
    When a node has changed state and need to call a partial update.
    For example a user exposed bpy.prop
    """
    if self.copy_objects_parent==True or self.clear_objects_parent==True:
        self.process_node(context)
    pass

def updateAnimationProperty(self, context):
    # skip node process
    pass

class SvUIShowIconRelations(bpy.types.Operator):
    '''Filled - socket connected, Circle - socket is not connected'''
    bl_idname = "node.sv_ui_show_icon_relations"
    bl_label = ""

    description_text: bpy.props.StringProperty(default='')

    node_name: bpy.props.StringProperty(default='')
    tree_name: bpy.props.StringProperty(default='')  # all item types should have actual name of a tree
    fn_name  : bpy.props.StringProperty(default='')
    idx      : bpy.props.IntProperty(default=0)

    @classmethod
    def description(cls, context, property):
        s = property.description_text
        return s

    def invoke(self, context, event):
        # node = context.node
        # if node:
        #     pass
        return {'FINISHED'}

def draw_properties(layout, node_group, node_name):
    node = bpy.data.node_groups[node_group].nodes[node_name]
    root_grid = layout.column(align=True).grid_flow(row_major=True, columns=4, align=True, even_columns=False)
    root_grid.alignment = 'EXPAND'

    for (param_name, param_settings) in object_params.items():
        prop_enabled = True
        if 'node_property_name_apply' in param_settings:
            node_property_name_apply = param_settings['node_property_name_apply']
            if getattr(node, node_property_name_apply)==False:
                prop_enabled = False

        if 'object_property_name_copy' in param_settings:
            object_property_name_copy = param_settings['object_property_name_copy']
            row = root_grid.row(align=False)
            row.alignment='LEFT'
            row.prop(node, object_property_name_copy, icon='OBJECT_DATA', text='')
            
        if 'node_property_map_mode' in param_settings:
            node_property_map_mode = param_settings['node_property_map_mode']
            socket_name = param_settings['socket_name']
            row = root_grid.row(align=True)
            row.alignment='RIGHT'

            op = row.operator(SvUIShowIconRelations.bl_idname, icon='FORWARD' if node.inputs[socket_name].is_linked else 'RADIOBUT_OFF', text='', emboss=False)
            op.description_text = 'Socket is connected.' if node.inputs[socket_name].is_linked==True else 'Socket is not connected.'

        if 'node_property_map_mode' in param_settings:
            node_property_map_mode = param_settings['node_property_map_mode']
            row = root_grid.row(align=True)
            row.enabled = prop_enabled
            row.prop(node, node_property_map_mode, expand=True)


        if 'node_property_name_apply' in param_settings:
            node_property_name_apply = param_settings['node_property_name_apply']
            row = root_grid.row(align=True)
            row.alignment='LEFT'
            row.prop(node, node_property_name_apply,)
        pass

    if bpy.data.node_groups[node_group].sv_process==False:
        row = layout.row(align=True)
        row.alignment = 'CENTER'
        row.alert = True
        col = row.column(align=False)
        col.alignment = 'CENTER'
        col.label(text=f'WARNING! "Live update" is not enabled! ')
        col.label(text=f'Sverchok node group "{node_group}" is not working ', icon='ERROR')

    pass


def draw_copy_or_clear_animated_properties(layout, node_group, node_name):
    node = bpy.data.node_groups[node_group].nodes[node_name]
    #layout.use_property_split = True https://blender.stackexchange.com/questions/161581/how-to-display-the-animate-property-diamond-keyframe-insert-button-2-8x
    #layout.alignment = 'LEFT'
    root_grid = layout.column(align=True).grid_flow(row_major=True, columns=2, align=True, even_columns=False)
    root_grid.alignment = 'EXPAND'
    #root_grid.column(align=True).row(align=True).label(text='')
    #root_grid.column(align=True).row(align=True).label(text='')
    #root_grid.column(align=True).row(align=True).label(text='')
    
    # grid2 = root_grid.grid_flow(row_major=False, columns=1, align=True)
    # grid2.label(text='Priority params:')
    # row0 = grid2.column(align=True)
    # row0.label(text='- socket is priority', icon='CHECKBOX_HLT')
    # row0.label(text='- socket is not priority', icon='CHECKBOX_DEHLT')
    # grid2.separator()

    for (param_name, param_settings) in object_params.items():
        prop_enabled = True
        if 'node_property_name_apply' in param_settings:
            node_property_name_apply = param_settings['node_property_name_apply']
            if getattr(node, node_property_name_apply)==False:
                prop_enabled = False

        if 'node_property_map_mode' in param_settings:
            node_property_map_mode = param_settings['node_property_map_mode']
            socket_name = param_settings['socket_name']
            row = root_grid.row(align=True)
            #row.enabled = prop_enabled
            row.alignment='RIGHT'

            op = row.operator(SvUIShowIconRelations.bl_idname, icon='FORWARD' if node.inputs[socket_name].is_linked else 'RADIOBUT_OFF', text='', emboss=False)
            op.description_text = 'Socket is connected.' if node.inputs[socket_name].is_linked==True else 'Socket is not connected.'

        if 'object_property_name_animation_copy' in param_settings:
            object_property_name_animation_copy = param_settings['object_property_name_animation_copy']
            row = root_grid.row(align=False)
            row.alignment='LEFT'
            row.prop(node, object_property_name_animation_copy, icon='KEYTYPE_KEYFRAME_VEC' if getattr(node, object_property_name_animation_copy)==True else 'HANDLETYPE_FREE_VEC' )
            pass
        pass
    if bpy.data.node_groups[node_group].sv_process==False:
        row = layout.row(align=True)
        row.alignment = 'CENTER'
        row.alert = True
        col = row.column(align=True)
        col.alignment = 'CENTER'
        col.label(text=f'WARNING! "Live update" is not enabled! ')
        col.label(text=f'Copy/clear animation will not work ', icon='ERROR')
    pass

class SV_PT_ViewportDisplayPropertiesDialogRelations(bpy.types.Operator):
    '''Overwrite Settings of Rigid Body properties node values and sockets'''
    # this combination do not show this panel on the right side panel
    bl_idname="sv.viewport_display_properties_dialog_objects_relations"
    bl_label = "Overwrite Settings"

    # horizontal size
    # bl_ui_units_x = 40 - Has no influence in Dialog mode, use 'width' property in context.window_manager.invoke_props_dialog

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
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        # Прочитать и определить здесь, какие параметры аниммированы и вывести в окне
        # признак, что параметр анимирован (что он не будет устанавливаться при анимации
        # в работе этого нода, даже если выставлен priority, т.е. animated/kinetic
        # отменяет приоритет)
        draw_properties(self.layout, self.node_group, self.node_name)
        pass

    def execute(self, context):
        #self._is_open = False
        return {'FINISHED'}

    def cancel(self, context):
        #self._is_open = False
        return None


class SV_PT_ViewportDisplayPropertiesRelations(bpy.types.Panel):
    '''Additional node properties'''
    # this combination do not show this panel on the right side panel
    bl_idname="SV_PT_ViewportDisplayPropertiesRelations"
    bl_label = "node properties as Dialog Window."
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'

    # @classmethod
    # def description(cls, context, properties):
    #     s = "properties.description_text"
    #     return s

    # horizontal size
    bl_ui_units_x = 20

    def draw(self, context):
        if hasattr(context, "node"):
            node_name = context.node.name
            node_group = context.annotation_data_owner.name_full
            draw_properties(self.layout, node_group, node_name)
        pass


class SV_PT_CopyAnimatedPropertiesDialogRelations(bpy.types.Operator):
    '''Copy Animated Properties of Rigid Body settings (FCurve)'''
    # this combination do not show this panel on the right side panel
    bl_idname="sv.copy_animation_properties_dialog_relations"
    bl_label = "Copy FCurve"

    # horizontal size
    # bl_ui_units_x = 40 - Has no influence in Dialog mode, use 'width' property in context.window_manager.invoke_props_dialog

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
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        # Прочитать и определить здесь, какие парамерны анимированы и вывести в окне
        # признак, что параметр анимирован (что он не будет устанавливаться при анимации
        # в работе этого нода, даже если выставлен priority, т.е. animated/kinetic
        # отменяет приоритет)
        draw_copy_or_clear_animated_properties(self.layout, self.node_group, self.node_name)
        pass

    def execute(self, context):
        node = bpy.data.node_groups[self.node_group].nodes[self.node_name]
        if node:
            node.copy_objects_animation = True
            # node.process() - do not call this function. Trigger in property call this
            pass
        return {'FINISHED'}

    def cancel(self, context):
        #self._is_open = False
        return None


class SV_PT_ClearAnimatedPropertiesDialogRelations(bpy.types.Operator):
    '''Clear Animated Properties of Rigid Body (FCurve)'''
    bl_idname="sv.clear_animation_properties_dialog_relations"
    bl_label = "Clear FCurve"

    # horizontal size
    # bl_ui_units_x = 40 - Has no influence in Dialog mode, use 'width' property in context.window_manager.invoke_props_dialog

    description_text: bpy.props.StringProperty(default='')
    node_group      : bpy.props.StringProperty(default='')
    node_name       : bpy.props.StringProperty(default='')

    # def is_extended():
    #     return True

    # def execute(self, context):
    #     return {'FINISHED'}
    
    def invoke(self, context, event):
        self.node_name = context.node.name
        self.node_group = context.annotation_data_owner.name_full
        return context.window_manager.invoke_props_dialog(self, width=350)

    def draw(self, context):
        # Прочитать и определить здесь, какие парамерны аниммированы и вывести в окне
        # признак, что параметр анимирован (что он не будет устанавливаться при анимации
        # в работе этого нода, даже если выставлен priority, т.е. animated/kinetic
        # отменяет приоритет)
        draw_copy_or_clear_animated_properties(self.layout, self.node_group, self.node_name)
        pass

    def execute(self, context):
        # context has no node property. 
        node = bpy.data.node_groups[self.node_group].nodes[self.node_name]
        if node:
            node.clear_objects_animation = True
            #bpy.ops.wm.sv_message(message="Clear canceled")
            show_popup("Animation cleared")
            # node.process() - do not call this function. Trigger in property call this
            pass
        return {'FINISHED'}

    def cancel(self, context):
        #self._is_open = False
        return None

def updateNodeCopy(self, context):
    if self.copy_objects_animation or self.clear_objects_animation:
        self.process_node(context)
    pass

class SvSetObjectsReleationNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: modifiers
    Tooltip:
    """
    bl_idname = 'SvSetObjectsReleationNode'
    bl_label = 'Set Objects Relation (Objects)'
    bl_icon = 'MATERIAL'
    is_scene_dependent = True
    is_animation_dependent = True

    copy_objects_animation : bpy.props.BoolProperty(
        name        = "Copy Animation",
        description = "Copy animation keys of mapped objects to objects",
        default     = False,
        options     = {'SKIP_SAVE'},
        update      = updateNodeCopy,
    )
    clear_objects_animation : bpy.props.BoolProperty(
        name        = "Clear Animation",
        description = "Copy animation keys of mapped objects to objects",
        default     = False,
        options     = {'SKIP_SAVE'},
        update      = updateNodeCopy,
    )
    
    some_properties_animated : bpy.props.BoolProperty(
        name        = "Copy Animation",
        description = "Copy animation keys of mapped objects to objects",
        default     = False,
        options     = {'SKIP_SAVE'},
        #update      = updateNodeCopy,
    )

    copy_objects_parent : bpy.props.BoolProperty(
        name        = "Copy Objects Parent",
        description = "Copy Objects Parent to objects",
        default     = False,
        options     = {'SKIP_SAVE'},
        update      = updateNodeCopyParent,
    )
    clear_objects_parent : bpy.props.BoolProperty(
        name        = "Clear Objects Parent",
        description = "Clear Objects Parent of objects",
        default     = False,
        options     = {'SKIP_SAVE'},
        update      = updateNodeCopyParent,
    )


    targeting_objects1: bpy.props.PointerProperty(
        name="Objects",
        description = "Where to copy material slots",
        type=bpy.types.Object,
    )

    objects_indexes_maps1 : bpy.props.IntProperty(
        name = "Objects map",
        description = "Original Object Id of Objects Parent list",
        default = 0,
        min = 0,
        update = updateNode)


    parent_objects1: bpy.props.PointerProperty(
        name="Objects Parent",
        description = "Objects Parent of Objects",
        type=bpy.types.Object,
    )

    objects_indexes_maps_mode_modes = [
            ('OBJECT_INDEX_MAP,MAPPING' , "Mapping" , "Mapping objects by input socket data", 0),
            ('OBJECT_INDEX_MAP,INDEXING', "Indexing", "Mapping objects by indexes (ignore mapping)"  , 1),
        ]

    objects_indexes_maps_mode1 : bpy.props.EnumProperty(
        name        = "Objects map mode",
        description = "Mappings Objects by map or by Indexes",
        items       = objects_indexes_maps_mode_modes,
        default     = 'OBJECT_INDEX_MAP,MAPPING',
        update      = updateNode,
    )

    relations_parent_type_modes = [
            ('RELATIONS_PARENT_TYPE,OBJECT'     , "Object"      , "The object is parented to an object"             , 0),
            ('RELATIONS_PARENT_TYPE,ARMATURE'   , "Armature"    , "The Object is parented to an armature"           , 1),
            ('RELATIONS_PARENT_TYPE,LATTICE'    , "Lattice"     , "The object is parented to a lattice"             , 2),
            ('RELATIONS_PARENT_TYPE,VERTEX'     , "Vertex"      , "Object is parented to a vertex"                  , 3),
            ('RELATIONS_PARENT_TYPE,VERTEX_3'   , "3 Vertices"  , "Object is parented to center of 3 vertives face" , 4),
            ('RELATIONS_PARENT_TYPE,BONE'       , "Bone"        , "The object is parented to a bone"                , 5),
        ]
    
    relations_parent_type1 : bpy.props.EnumProperty(
        name        = "Parent Type",
        description = "Indices of vertices in case of a vertex parenting relation",
        items       = relations_parent_type_modes,
        default     = 'RELATIONS_PARENT_TYPE,OBJECT',
        update      = updateNode,
    )
    node_parent_type_apply                : bpy.props.BoolProperty( name = "Parent Type", description = "On - Overwrite Relations settings\nOff - do not overwrite", default = False, update = updateNode)
    relations_parent_type_animation_copy  : bpy.props.BoolProperty( name = "Parent Type", description = "On - Copy Animation\nOff - do not copy animation", default = True, update = updateAnimationProperty, ) # This flag used in the operator so do not need to call update
    relations_parent_type_property_copy   : bpy.props.BoolProperty( name = "Parent Type", description = "On - Copy Relations settings\nOff - do not copy from template", default = False, update = updateNode, )
    relations_parent_type_map_mode        : bpy.props.EnumProperty( name = "Parent Type", description = 'Mapping by "Objects Map" or by Indexes', items = objects_indexes_maps_mode_modes, default = 'OBJECT_INDEX_MAP,MAPPING', update = updateNode, )

    relations_use_parent_final_indices1 : bpy.props.BoolProperty(
        name        = "Use Final Indices",
        description = "On - Use the final evaluated indices rather than the original mesh indices\nOff - disable",
        default     = True,
        update = updateNode)
    node_use_parent_final_indices_apply                 : bpy.props.BoolProperty( name = "Use Final Indices", description = "On - Overwrite Relations settings\nOff - do not overwrite", default = False, update = updateNode)
    relations_use_parent_final_indices_animation_copy   : bpy.props.BoolProperty( name = "Use Final Indices", description = "On - Copy Animation\nOff - do not copy animation", default = True, update = updateAnimationProperty, )
    relations_use_parent_final_indices_property_copy    : bpy.props.BoolProperty( name = "Use Final Indices", description = "On - Copy Relations settings\nOff - do not copy from template", default = False, update = updateNode, )
    relations_use_parent_final_indices_map_mode         : bpy.props.EnumProperty( name = "Use Final Indices", description = "Mapping by 'Objects Map' or by Indexes", items = objects_indexes_maps_mode_modes, default = 'OBJECT_INDEX_MAP,MAPPING', update = updateNode, )

    relations_parent_vertices1 : bpy.props.IntVectorProperty(
        name        = "Parent Vertices",
        description = "On - Indices of vertices in case of a vertex parenting relation\nOff - disable",
        size        = 3,
        default     = (0,0,0),
        update = updateNode)
    node_parent_vertices_apply                 : bpy.props.BoolProperty( name = "Parent Vertices", description = "On - Overwrite Relations settings\nOff - do not overwrite", default = False, update = updateNode)
    relations_parent_vertices_animation_copy   : bpy.props.BoolProperty( name = "Parent Vertices", description = "On - Copy Animation\nOff - do not copy animation", default = True, update = updateAnimationProperty, )
    relations_parent_vertices_property_copy    : bpy.props.BoolProperty( name = "Parent Vertices", description = "On - Copy Relations settings\nOff - do not copy from template", default = False, update = updateNode, )
    relations_parent_vertices_map_mode         : bpy.props.EnumProperty( name = "Parent Vertices", description = "Mapping by 'Objects Map' or by Indexes", items = objects_indexes_maps_mode_modes, default = 'OBJECT_INDEX_MAP,MAPPING', update = updateNode, )

    relations_use_camera_lock_parent1 : bpy.props.BoolProperty(
        name        = "Camera Parent Lock",
        description = "On - View Lock 3D viewport camera transformation affects the object's parent instead\nOff - disable",
        default     = True,
        update = updateNode)
    node_use_camera_lock_parent_apply                 : bpy.props.BoolProperty( name = "Camera Parent Lock", description = "On - Overwrite Relations settings\nOff - do not overwrite", default = False, update = updateNode)
    relations_use_camera_lock_parent_animation_copy   : bpy.props.BoolProperty( name = "Camera Parent Lock", description = "On - Copy Animation\nOff - do not copy animation", default = True, update = updateAnimationProperty, )
    relations_use_camera_lock_parent_property_copy    : bpy.props.BoolProperty( name = "Camera Parent Lock", description = "On - Copy Relations settings\nOff - do not copy from template", default = False, update = updateNode, )
    relations_use_camera_lock_parent_map_mode         : bpy.props.EnumProperty( name = "Camera Parent Lock", description = "Mapping by 'Objects Map' or by Indexes", items = objects_indexes_maps_mode_modes, default = 'OBJECT_INDEX_MAP,MAPPING', update = updateNode, )

    relations_track_axis_modes = [
            ('RELATIONS_TRACK_AXIS,POS_X'   , "+X", "" , 0),
            ('RELATIONS_TRACK_AXIS,POS_Y'   , "+Y", "" , 1),
            ('RELATIONS_TRACK_AXIS,POS_Z'   , "+Z", "" , 2),
            ('RELATIONS_TRACK_AXIS,NEG_X'   , "-X", "" , 3),
            ('RELATIONS_TRACK_AXIS,NEG_Y'   , "-Y", "" , 4),
            ('RELATIONS_TRACK_AXIS,NEG_Z'   , "-Z", "" , 5),
        ]
    
    relations_track_axis1 : bpy.props.EnumProperty(
        name        = "Track Axis",
        description = "Axis that points in the 'forward' direction (applies to Instance Vertices when Align to Vertex Normal is enabled)",
        items       = relations_track_axis_modes,
        default     = 'RELATIONS_TRACK_AXIS,POS_Y',
        update      = updateNode,
    )
    node_track_axis_apply                : bpy.props.BoolProperty( name = "Track Axis", description = "On - Overwrite Relations settings\nOff - do not overwrite", default = False, update = updateNode)
    relations_track_axis_animation_copy  : bpy.props.BoolProperty( name = "Track Axis", description = "On - Copy Animation\nOff - do not copy animation", default = True, update = updateAnimationProperty, ) # This flag used in the operator so do not need to call update
    relations_track_axis_property_copy   : bpy.props.BoolProperty( name = "Track Axis", description = "On - Copy Relations settings\nOff - do not copy from template", default = False, update = updateNode, )
    relations_track_axis_map_mode        : bpy.props.EnumProperty( name = "Track Axis", description = 'Mapping by "Objects Map" or by Indexes', items = objects_indexes_maps_mode_modes, default = 'OBJECT_INDEX_MAP,MAPPING', update = updateNode, )

    relations_up_axis_modes = [
            ('RELATIONS_UP_AXIS,X'   , "X", "" , 0),
            ('RELATIONS_UP_AXIS,Y'   , "Y", "" , 1),
            ('RELATIONS_UP_AXIS,Z'   , "Z", "" , 2),
        ]
    
    relations_up_axis1 : bpy.props.EnumProperty(
        name        = "Up Axis",
        description = "Axis that points in the upward direction (applies to Instance Vertices when Align to Vertex Normal is enabled)",
        items       = relations_up_axis_modes,
        default     = 'RELATIONS_UP_AXIS,Z',
        update      = updateNode,
    )
    node_up_axis_apply                : bpy.props.BoolProperty( name = "Up Axis", description = "On - Overwrite Relations settings\nOff - do not overwrite", default = False, update = updateNode)
    relations_up_axis_animation_copy  : bpy.props.BoolProperty( name = "Up Axis", description = "On - Copy Animation\nOff - do not copy animation", default = True, update = updateAnimationProperty, ) # This flag used in the operator so do not need to call update
    relations_up_axis_property_copy   : bpy.props.BoolProperty( name = "Up Axis", description = "On - Copy Relations settings\nOff - do not copy from template", default = False, update = updateNode, )
    relations_up_axis_map_mode        : bpy.props.EnumProperty( name = "Up Axis", description = 'Mapping by "Objects Map" or by Indexes', items = objects_indexes_maps_mode_modes, default = 'OBJECT_INDEX_MAP,MAPPING', update = updateNode, )

    relations_pass_index1 : bpy.props.IntProperty(
        name        = "Pass Index",
        description = "On - Index number for the 'Object Index' render pass\nOff - disable",
        default     = 0,
        update = updateNode)
    node_pass_index_apply                 : bpy.props.BoolProperty( name = "Pass Index", description = "On - Overwrite Relations settings\nOff - do not overwrite", default = False, update = updateNode)
    relations_pass_index_animation_copy   : bpy.props.BoolProperty( name = "Pass Index", description = "On - Copy Animation\nOff - do not copy animation", default = True, update = updateAnimationProperty, )
    relations_pass_index_property_copy    : bpy.props.BoolProperty( name = "Pass Index", description = "On - Copy Relations settings\nOff - do not copy from template", default = False, update = updateNode, )
    relations_pass_index_map_mode         : bpy.props.EnumProperty( name = "Pass Index", description = "Mapping by 'Objects Map' or by Indexes", items = objects_indexes_maps_mode_modes, default = 'OBJECT_INDEX_MAP,MAPPING', update = updateNode, )

    def sv_draw_buttons(self, context, layout):
        box = layout.box()
        row = box.row(align=True)
        row.prop(self, 'copy_objects_parent', toggle=True, icon='RENDER_RESULT', text='')
        row.prop(self, 'clear_objects_parent', toggle=True, icon='CANCEL', text='')

        elem = box.row(align=True)
        elem.label(text='Rigid Body copy settings:')
        elem.separator()

        row = box.row(align=True)
        #row.prop(self, 'node_in_use', text=('Rigid Body [Activated]' if self.node_in_use==True else 'Rigid Body [Removed]'), icon=('X' if self.node_in_use==True else 'RIGID_BODY') )
        row.label(text="")
        row.separator()
        row.row(align=True).operator(SV_PT_CopyAnimatedPropertiesDialogRelations.bl_idname, icon='KEYTYPE_KEYFRAME_VEC', text="", emboss=True)
        row1 = row.row(align=True)
        if self.some_properties_animated==True:
            row1.alert = True
            op = row1.operator(SV_PT_ClearAnimatedPropertiesDialogRelations.bl_idname, icon='ERROR', text="", emboss=True)
            op.description_text = 'These are animations fcurves data.'
        else:
            op = row1.operator(SV_PT_ClearAnimatedPropertiesDialogRelations.bl_idname, icon='HANDLETYPE_FREE_VEC', text="", emboss=True)
            op.description_text = 'These are no animations fcurves data. You can set up the Relations settings.'

        row = elem.row(align=True)
        row.column(align=True).operator(SV_PT_ViewportDisplayPropertiesDialogRelations.bl_idname, icon='TOOL_SETTINGS', text="", emboss=True)
        row.column(align=True).popover(panel=SV_PT_ViewportDisplayPropertiesRelations.bl_idname, icon='DOWNARROW_HLT', text="")

        pass

    def custom_draw_input_sockets(self, socket, context, layout):
        if socket.is_linked==True:
            layout.label(text=socket.label + f". {socket.objects_number}")
        else:
            layout.prop(self, socket.prop_name, text=self.label or None)
        return

    def custom_draw_input_sockets_targeting_objects(self, socket, context, layout):
        if socket.is_linked==True:
            layout.label(text=socket.label + f". {socket.objects_number or ''}")
        else:
            layout.prop(self, socket.prop_name, text=self.label or None)
        return

    def custom_draw_input_sockets_objects_indexes_maps(self, socket, context, layout):
        row = layout.row(align=True)
        split = row.split(factor=0.6)
        col = split.column(align=True)
        if self.objects_indexes_maps_mode1=='OBJECT_INDEX_MAP,INDEXING': # or self.node_in_use==False or self.node_play_pause1=='RIGID_BODY_NODE_PLAY,PAUSE':
            col.enabled = False
        if socket.is_linked==True:
            col.alignment = "LEFT"
            col.label(text=socket.label + f". {socket.objects_number or ''}")
        else:
            col.prop(self, socket.prop_name, text=self.label or None)
        row2 = split.row(align=True)
        row2.prop(self, 'objects_indexes_maps_mode1', text='',)
        return

    def custom_draw_input_sockets_object_params(self, socket, context, layout):
        # if self.node_in_use==False or self.node_play_pause1=='RIGID_BODY_NODE_PLAY,PAUSE':
        #     layout.enabled = False

        if socket.name in relations_socket_names:
            node_property_name_apply = relations_socket_names[socket.name]['node_property_name_apply']
            if getattr(self, node_property_name_apply)==False:
                layout.enabled = False
            pass
        layout.use_property_decorate = False
        layout.use_property_split = True

        if socket.is_linked==True:
            layout.label(text=socket.label + f". {socket.objects_number or ''}")
        else:
            layout.prop(self, socket.prop_name, text=self.label or None)
        return


    def sv_init(self, context):
        self.width = 260
        self.inputs.new('SvObjectSocket' , 'targeting_objects'                  ).prop_name = 'targeting_objects1'
        self.inputs.new('SvStringsSocket', 'objects_indexes_maps'               ).prop_name = 'objects_indexes_maps1'
        self.inputs.new('SvObjectSocket' , 'parent_objects'                     ).prop_name = 'parent_objects1'
        self.inputs.new('SvStringsSocket', 'relations_parent_type'              ).prop_name = 'relations_parent_type1'
        self.inputs.new('SvStringsSocket', 'relations_use_parent_final_indices' ).prop_name = 'relations_use_parent_final_indices1'
        self.inputs.new('SvStringsSocket', 'relations_parent_vertices'          ).prop_name = 'relations_parent_vertices1'
        self.inputs.new('SvStringsSocket', 'relations_use_camera_lock_parent'   ).prop_name = 'relations_use_camera_lock_parent1'
        self.inputs.new('SvStringsSocket', 'relations_track_axis'               ).prop_name = 'relations_track_axis1'
        self.inputs.new('SvStringsSocket', 'relations_up_axis'                  ).prop_name = 'relations_up_axis1'
        self.inputs.new('SvStringsSocket', 'relations_pass_index'               ).prop_name = 'relations_pass_index1'

        self.inputs['targeting_objects'     ].label = 'Objects'
        self.inputs['objects_indexes_maps'  ].label = 'Objects map'
        self.inputs['parent_objects'        ].label = 'Objects with Relations'
        
        self.outputs.new('SvObjectSocket', 'resulting_objects' ).label = "Objects"

        # Назначить descriptions для сокетов, которым назначены параметры из этого класса:
        for (sn, params) in (object_params | {
                'targeting_objects'     : {'node_property_name': 'targeting_objects1'       , 'socket_name': 'targeting_objects'    , },
                'objects_indexes_maps'  : {'node_property_name': 'objects_indexes_maps1'    , 'socket_name': 'objects_indexes_maps' , },
                'parent_objects'        : {'node_property_name': 'parent_objects1'          , 'socket_name': 'parent_objects'       , }
            }).items() :
            node_property_name = params['node_property_name']
            socket_name = params['socket_name']
            name = None
            type = None
            description=None
            if hasattr(self.__class__, 'bl_rna')==True and node_property_name in self.__class__.bl_rna.properties:
                prop = self.__class__.bl_rna.properties[node_property_name]
                name = prop.name
                type = prop.type
                description = prop.description
            if description:
                self.inputs[socket_name].description = f'{description}'
            if name:
                self.inputs[socket_name].label = f'{name}'
            self.inputs[socket_name].custom_draw = 'custom_draw_input_sockets_object_params'
            pass

        self.inputs['targeting_objects'                 ].custom_draw = 'custom_draw_input_sockets_targeting_objects'
        self.inputs['objects_indexes_maps'              ].custom_draw = 'custom_draw_input_sockets_objects_indexes_maps'

        pass

    def process(self):
        if not any(socket.is_linked for socket in self.inputs):
            return
        
        bpy.context.view_layer.update()
        
        targeting_objects  = self.inputs['targeting_objects' ].sv_get(deepcopy=False, default=[self.targeting_objects1 ])
        if self.inputs['targeting_objects'].is_linked==False:
            targeting_objects = []
            if self.targeting_objects1:
                targeting_objects = [self.targeting_objects1] * len(targeting_objects)

        objects_indexes_maps = self.inputs['objects_indexes_maps'].sv_get(deepcopy=False, default=[self.objects_indexes_maps1      ])
        if self.inputs['objects_indexes_maps'].is_linked==False:
            objects_indexes_maps = [self.objects_indexes_maps1] * len(targeting_objects)

        parent_objects  = self.inputs['parent_objects'].sv_get(deepcopy=False, default=[self.parent_objects1 ])

        if len(targeting_objects)==0:
            pass
        else:
            try:
                objects_indexes_maps = [unwrap_lowest_single_value(val) for val in objects_indexes_maps]
                for I, obj in enumerate(targeting_objects):
                    ID = objects_indexes_maps[I] if self.objects_indexes_maps_mode1=='OBJECT_INDEX_MAP,MAPPING' else I
                    try:
                        parent_objects_ID = parent_objects[ID]
                    except IndexError:
                        raise Exception(f'0001. "Object"[{ID}] out of range. Number of objects in Socket "Rigid Body settings" [{len(objects_indexes_maps)} items] in Indexing mode has to be equals to "Objects" sockets [{len(targeting_objects)}]')
                    except Exception as _ex:
                        raise Exception(f'0002. "Rigid Body settings"[{ID}] exception: {_ex}')

                    if self.copy_objects_animation:
                        if len(parent_objects)==0:
                            self.copy_objects_animation = False
                            raise Exception(f'0003. No Rigid Body settings to copy animation.')
                        try:
                            copy_fcurves(parent_objects[ID], obj, [f'{name}' for name in object_params if getattr(self, object_params[name]['object_property_name_animation_copy']) ])
                        except Exception as ex:
                            print(f"0004. Animation copy error: {ex}")
                            pass
                        pass
                    # Очистить анимацию, если включена опция очистки анимации
                    if self.clear_objects_animation:
                        try:
                            remove_fcurves(obj, [f'{name}' for name in object_params if getattr(self, object_params[name]['object_property_name_animation_copy'])] )
                        except Exception as ex:
                            print(f"0005. Animation clear error: {ex}")
                            pass
                        pass    

                    copy_object_relations(parent_objects_ID, obj)
                    pass
                pass

            except Exception as _ex:
                raise _ex
            # Сбросить признаки копирования и очистки анимации (в принципе из всегда можно сбрасывать независимо от значения).
            self.copy_objects_animation = False
            self.clear_objects_animation = False

            self.copy_objects_parent=False
        pass

        self.outputs['resulting_objects'].sv_set(targeting_objects)
        #bpy.context.view_layer.update()

classes = [SV_PT_CopyAnimatedPropertiesDialogRelations, SV_PT_ClearAnimatedPropertiesDialogRelations, SvUIShowIconRelations, SV_PT_ViewportDisplayPropertiesDialogRelations, SV_PT_ViewportDisplayPropertiesRelations, SvSetObjectsReleationNode, ]
register, unregister = bpy.utils.register_classes_factory(classes)
