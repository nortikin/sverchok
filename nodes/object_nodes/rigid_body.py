# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import numpy as np

import bpy
from bpy.props import IntProperty, FloatProperty, BoolProperty, EnumProperty, BoolVectorProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode, match_long_repeat, fullList, get_data_nesting_level, describe_data_shape)

from itertools import zip_longest

rigid_body_params = {
        'type'                          : {'node_property_name': 'rigid_body_type1'                        , 'socket_name': 'rigid_body_type'                       , 'node_property_name_apply': 'node_type_apply'                          , 'object_rb_property_name_animation_copy': 'object_rb_type_animation_copy'                          , 'node_property_map_mode' : 'rigid_body_type_map_mode'                         , },
        'mass'                          : {'node_property_name': 'rigid_body_mass1'                        , 'socket_name': 'rigid_body_mass'                       , 'node_property_name_apply': 'node_mass_apply'                          , 'object_rb_property_name_animation_copy': 'object_rb_mass_animation_copy'                          , 'node_property_map_mode' : 'rigid_body_mass_map_mode'                         , },
        'enabled'                       : {'node_property_name': 'rigid_body_enabled1'                     , 'socket_name': 'rigid_body_enabled'                    , 'node_property_name_apply': 'node_enabled_apply'                       , 'object_rb_property_name_animation_copy': 'object_rb_enabled_animation_copy'                       , 'node_property_map_mode' : 'rigid_body_enabled_map_mode'                      , },
        'kinematic'                     : {'node_property_name': 'rigid_body_kinematic1'                   , 'socket_name': 'rigid_body_kinematic'                  , 'node_property_name_apply': 'node_kinematic_apply'                     , 'object_rb_property_name_animation_copy': 'object_rb_kinematic_animation_copy'                     , 'node_property_map_mode' : 'rigid_body_kinematic_map_mode'                    , },
        'collision_shape'               : {'node_property_name': 'rigid_body_collision_shape1'             , 'socket_name': 'rigid_body_collision_shape'            , 'node_property_name_apply': 'node_collision_shape_apply'               , 'object_rb_property_name_animation_copy': 'object_rb_collision_shape_animation_copy'               , 'node_property_map_mode' : 'rigid_body_collision_shape_map_mode'              , },
        'mesh_source'                   : {'node_property_name': 'rigid_body_mesh_source1'                 , 'socket_name': 'rigid_body_mesh_source'                , 'node_property_name_apply': 'node_mesh_source_apply'                   , 'object_rb_property_name_animation_copy': 'object_rb_mesh_source_animation_copy'                   , 'node_property_map_mode' : 'rigid_body_mesh_source_map_mode'                  , },
        'use_deform'                    : {'node_property_name': 'rigid_body_use_deform1'                  , 'socket_name': 'rigid_body_use_deform'                 , 'node_property_name_apply': 'node_use_deform_apply'                    , 'object_rb_property_name_animation_copy': 'object_rb_use_deform_animation_copy'                    , 'node_property_map_mode' : 'rigid_body_use_deform_map_mode'                   , },
        'friction'                      : {'node_property_name': 'rigid_body_friction1'                    , 'socket_name': 'rigid_body_friction'                   , 'node_property_name_apply': 'node_friction_apply'                      , 'object_rb_property_name_animation_copy': 'object_rb_friction_animation_copy'                      , 'node_property_map_mode' : 'rigid_body_friction_map_mode'                     , },
        'restitution'                   : {'node_property_name': 'rigid_body_restitution1'                 , 'socket_name': 'rigid_body_restitution'                , 'node_property_name_apply': 'node_restitution_apply'                   , 'object_rb_property_name_animation_copy': 'object_rb_restitution_animation_copy'                   , 'node_property_map_mode' : 'rigid_body_restitution_map_mode'                  , },
        'use_margin'                    : {'node_property_name': 'rigid_body_use_margin1'                  , 'socket_name': 'rigid_body_use_margin'                 , 'node_property_name_apply': 'node_use_margin_apply'                    , 'object_rb_property_name_animation_copy': 'object_rb_use_margin_animation_copy'                    , 'node_property_map_mode' : 'rigid_body_use_margin_map_mode'                   , },
        'collision_margin'              : {'node_property_name': 'rigid_body_collision_margin1'            , 'socket_name': 'rigid_body_collision_margin'           , 'node_property_name_apply': 'node_collision_margin_apply'              , 'object_rb_property_name_animation_copy': 'object_rb_collision_margin_animation_copy'              , 'node_property_map_mode' : 'rigid_body_collision_margin_map_mode'             , },
        'collision_collections'         : {'node_property_name': 'rigid_body_collision_collections1'       , 'socket_name': 'rigid_body_collision_collections'      , 'node_property_name_apply': 'node_collision_collections_apply'         , 'object_rb_property_name_animation_copy': 'object_rb_collision_collections_animation_copy'         , 'node_property_map_mode' : 'rigid_body_collision_collections_map_mode'        , },
        'linear_damping'                : {'node_property_name': 'rigid_body_linear_damping1'              , 'socket_name': 'rigid_body_linear_damping'             , 'node_property_name_apply': 'node_linear_damping_apply'                , 'object_rb_property_name_animation_copy': 'object_rb_linear_damping_animation_copy'                , 'node_property_map_mode' : 'rigid_body_linear_damping_map_mode'               , },
        'angular_damping'               : {'node_property_name': 'rigid_body_angular_damping1'             , 'socket_name': 'rigid_body_angular_damping'            , 'node_property_name_apply': 'node_angular_damping_apply'               , 'object_rb_property_name_animation_copy': 'object_rb_angular_damping_animation_copy'               , 'node_property_map_mode' : 'rigid_body_angular_damping_map_mode'              , },
        'use_deactivation'              : {'node_property_name': 'rigid_body_use_deactivation1'            , 'socket_name': 'rigid_body_use_deactivation'           , 'node_property_name_apply': 'node_use_deactivation_apply'              , 'object_rb_property_name_animation_copy': 'object_rb_use_deactivation_animation_copy'              , 'node_property_map_mode' : 'rigid_body_use_deactivation_map_mode'             , },
        'use_start_deactivated'         : {'node_property_name': 'rigid_body_use_start_deactivated1'       , 'socket_name': 'rigid_body_use_start_deactivated'      , 'node_property_name_apply': 'node_use_start_deactivated_apply'         , 'object_rb_property_name_animation_copy': 'object_rb_use_start_deactivated_animation_copy'         , 'node_property_map_mode' : 'rigid_body_use_start_deactivated_map_mode'        , },
        'deactivate_linear_velocity'    : {'node_property_name': 'rigid_body_deactivate_linear_velocity1'  , 'socket_name': 'rigid_body_deactivate_linear_velocity' , 'node_property_name_apply': 'node_deactivate_linear_velocity_apply'    , 'object_rb_property_name_animation_copy': 'object_rb_deactivate_linear_velocity_animation_copy'    , 'node_property_map_mode' : 'rigid_body_deactivate_linear_velocity_map_mode'   , },
        'deactivate_angular_velocity'   : {'node_property_name': 'rigid_body_deactivate_angular_velocity1' , 'socket_name': 'rigid_body_deactivate_angular_velocity', 'node_property_name_apply': 'node_deactivate_angular_velocity_apply'   , 'object_rb_property_name_animation_copy': 'object_rb_deactivate_angular_velocity_animation_copy'   , 'node_property_map_mode' : 'rigid_body_deactivate_angular_velocity_map_mode'  , },
        #{'object': '', 'node': 'rigid_body_', },
    }

rigid_body_socket_names = dict()
for (params, params_settings) in rigid_body_params.items():
    socket_name = params_settings['socket_name']
    rigid_body_socket_names[socket_name] = params_settings

# # tests for copy animation
# def copy_rigid_body_animation(obj, list_target_objects, only_clear=False):
#     if not obj.animation_data or not obj.animation_data.action:
#         return

#     src_action = obj.animation_data.action

#     def is_rb_curve(fcurve):
#         return any(
#             fcurve.data_path == f"rigid_body.{param}"
#             or fcurve.data_path.startswith(f"rigid_body.{param}[")
#             for param in rigid_body_params
#         )

#     src_fcurves = []

#     for slot in src_action.slots:
#         if slot and hasattr(slot, "fcurves"):
#             for fc in slot.fcurves:
#                 if is_rb_curve(fc):
#                     src_fcurves.append(fc)
#                 pass
#         pass

#     for target in list_target_objects:

#         if not target.rigid_body:
#             continue

#         # --- ОЧИСТКА АНИМАЦИИ ---
#         if target.animation_data:
#             if target.animation_data.action:
#                 bpy.data.actions.remove(target.animation_data.action)
#             target.animation_data_clear()
#         if only_clear==True:
#             continue

#         target.animation_data_create()

#         # создаём новый action
#         new_action = bpy.data.actions.new(name=f"{target.name}_RB_Action")
#         target.animation_data.action = new_action

#         for fc in src_fcurves:
#             new_fc = new_action.fcurves.new(
#                 data_path=fc.data_path,
#                 index=fc.array_index
#             )

#             new_fc.keyframe_points.add(len(fc.keyframe_points))

#             for i, kp in enumerate(fc.keyframe_points):
#                 new_kp = new_fc.keyframe_points[i]

#                 new_kp.co = kp.co[:]
#                 new_kp.handle_left = kp.handle_left[:]
#                 new_kp.handle_right = kp.handle_right[:]

#                 new_kp.handle_left_type = kp.handle_left_type
#                 new_kp.handle_right_type = kp.handle_right_type
#                 new_kp.interpolation = kp.interpolation

#             new_fc.update()
#         pass
#     pass

# def get_fcurves(obj):
#     """
#     Возвращает список всех FCurve, связанных с объектом:
#     - активный Action
#     - NLA (если используется)
#     Поддерживает Blender 3.x–5.x
#     """

#     ad = obj.animation_data
#     if not ad:
#         return []

#     fcurves = []

#     # --- 1. Активный Action
#     action = ad.action
#     if action:
#         # Новый API (Blender 5.x)
#         if hasattr(action, "slots"):
#             for slot in action.slots:
#                 if hasattr(slot, "fcurves"):
#                     fcurves.extend(slot.fcurves)

#         # Старый API
#         elif hasattr(action, "fcurves"):
#             fcurves.extend(action.fcurves)

#     # --- 2. NLA (если есть)
#     for track in ad.nla_tracks:
#         for strip in track.strips:
#             act = strip.action
#             if not act:
#                 continue

#             if hasattr(act, "slots"):
#                 for slot in act.slots:
#                     if hasattr(slot, "fcurves"):
#                         fcurves.extend(slot.fcurves)

#             elif hasattr(act, "fcurves"):
#                 fcurves.extend(act.fcurves)

#     return fcurves

def show_popup(message, title="Info", icon='INFO'):

    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)

def get_action(ad):
    if hasattr(ad, "action_slot") and ad.action_slot:
        return ad.action_slot
    elif hasattr(ad, "action"):
        return ad.action
    else:
        raise Exception("0021. Unknown property action for animation operations. ")

def get_fcurves(obj):
    """
    Blender 5.x:
    Возвращает список FCurve для obj из active Action/Slot.
    """

    ad = obj.animation_data
    if not ad or not ad.action:
        return []

    action = ad.action
    slot = get_action(ad)
    if action is None or slot is None:
        return []

    result = []

    if hasattr(action, "fcurves"):
        # Blender 3.0
        result.extend( [fcurve for fcurve in action.fcurves] )
    else:
        for layer in action.layers:
            for strip in layer.strips:
                # Нас интересует keyframe strip, который умеет вернуть channelbag для slot.
                bag = None

                # На разных сборках/переходных API имя может отличаться,
                # поэтому пробуем несколько вариантов.
                if hasattr(strip, "channelbag"):
                    try:
                        bag = strip.channelbag(slot, ensure=False)
                    except TypeError:
                        bag = strip.channelbag(slot)
                elif hasattr(strip, "channelbag_for_slot"):
                    bag = strip.channelbag_for_slot(slot)
                elif hasattr(strip, "channelbag_slot"):
                    bag = strip.channelbag_slot(slot)

                if bag and hasattr(bag, "fcurves"):
                    result.extend(list(bag.fcurves))
        pass

    return result

def remove_fcurves(obj, data_path):
    """
    Blender 5.x:
    Возвращает список FCurve для obj из active Action/Slot.
    """

    ad = obj.animation_data
    if not ad or not ad.action:
        return []

    action = ad.action
    slot = get_action(ad)
    if action is None or slot is None:
        return []

    result = []
    if hasattr(action, "fcurves"):
        # Blender 3.0
        for fcurve in list(action.fcurves):
            action.fcurves.remove(fcurve)
            #result.append(fcurve) # В Blender 3.0 нельзя обращаться к кривой после удаления. Возникает исключение An exception was raised: ReferenceError('StructRNA of type FCurve has been removed'). Если требуется прочитать свойства, то это нужно делать заранее.
    else:
        for layer in action.layers:
            for strip in layer.strips:
                # Нас интересует keyframe strip, который умеет вернуть channelbag для slot.
                bag = None

                # На разных сборках/переходных API имя может отличаться,
                # поэтому пробуем несколько вариантов.
                if hasattr(strip, "channelbag"):
                    try:
                        bag = strip.channelbag(slot, ensure=False)
                    except TypeError:
                        bag = strip.channelbag(slot)
                elif hasattr(strip, "channelbag_for_slot"):
                    bag = strip.channelbag_for_slot(slot)
                elif hasattr(strip, "channelbag_slot"):
                    bag = strip.channelbag_slot(slot)

                if bag and hasattr(bag, "fcurves"):
                    for fc_to_remove in bag.fcurves:
                        if fc_to_remove.data_path in data_path:
                            bag.fcurves.remove(fc_to_remove)
                            #result.append(fcurve)
                        pass
                    pass
            pass
        pass

    return result


def copy_fcurves(src_obj, target_obj, data_paths, only_clear=False):
    """
    Копирует FCurves с src_obj на target_obj только для указанных data_paths.
    """

    # --- Проверка источника
    if not src_obj.animation_data or not src_obj.animation_data.action:
        #print("[ERROR] Source has no animation")
        return

    src_fcurves = get_fcurves(src_obj,)

    # --- Проверка доступных путей
    available_paths = {fc.data_path for fc in src_fcurves}
    #print(f'available_paths={available_paths}')

    valid_paths = []
    invalid_paths = []
    no_animation_paths = []

    for path in data_paths:
        # --- 1. Проверяем, что параметр вообще существует у target
        try:
            target_obj.path_resolve(path)
        except Exception:
            #print(f"[WARN] Path not valid for target object: {path}")
            invalid_paths.append(path)
            continue

        # --- 2. Проверяем, есть ли анимация у source
        if path not in available_paths:
            #print(f"[INFO] No animation for path (skipped): {path}")
            no_animation_paths.append(path)
            continue

        # --- 3. Всё ок
        valid_paths.append(path)

    #print(f'invalid_paths={invalid_paths}')
    #print(f'no_animation_paths={no_animation_paths}')

    # --- если есть реально невалидные параметры — останавливаемся
    if invalid_paths:
        #print(f"[ERROR] Invalid paths: {invalid_paths}")
        return

    # --- Подготовка target
    if not target_obj.animation_data:
        target_obj.animation_data_create()

    if not target_obj.animation_data.action:
        target_obj.animation_data.action = bpy.data.actions.new(
            name=f"{target_obj.name}_Action"
        )

    dst_action = target_obj.animation_data.action
    dst_fcurves = remove_fcurves(target_obj, valid_paths,)

    ## --- Удаление старых FCurves (ВАЖНО: через list)
    # 
    # fcurves_to_remove = [
    #     fc for fc in list(dst_fcurves)
    #     if fc.data_path in valid_paths
    # ]

    # #print(f'Количество fcurves_to_remove: {len(fcurves_to_remove)}, {fcurves_to_remove}')

    # for fc in fcurves_to_remove:
    #     dst_fcurves.remove(fc)

    if only_clear==True:
        return

    # --- Копирование
    if hasattr(dst_action, "fcurve_ensure_for_datablock")==False:
        # Blender 3.0
        for fc in src_fcurves:
            if fc.data_path not in valid_paths:
                continue

            # В 3.0 нет fcurve_ensure_for_datablock
            new_fc = dst_action.fcurves.find(fc.data_path, index=fc.array_index)

            if new_fc is None:
                new_fc = dst_action.fcurves.new(
                    data_path=fc.data_path,
                    index=fc.array_index
                )

            # очищаем существующие ключи (если были)
            kps = new_fc.keyframe_points
            if hasattr(kps, "clear"):
                kps.clear()
            else:
                for kp in list(kps):
                    kps.remove(kp)

            new_fc.keyframe_points.add(len(fc.keyframe_points))

            for i, kp in enumerate(fc.keyframe_points):
                new_kp = new_fc.keyframe_points[i]

                new_kp.co = kp.co.copy()
                new_kp.handle_left = kp.handle_left.copy()
                new_kp.handle_right = kp.handle_right.copy()

                new_kp.interpolation = kp.interpolation
                new_kp.handle_left_type = kp.handle_left_type
                new_kp.handle_right_type = kp.handle_right_type

            # В 3.0 лучше обновлять так:
            new_fc.keyframe_points.update()
        pass
    else:
        for fc in src_fcurves:
            if fc.data_path not in valid_paths:
                continue

            new_fc = dst_action.fcurve_ensure_for_datablock(
                target_obj,
                data_path=fc.data_path,
                index=fc.array_index
            )

            # очищаем существующие ключи (если были)
            new_fc.keyframe_points.clear()

            new_fc.keyframe_points.add(len(fc.keyframe_points))

            for i, kp in enumerate(fc.keyframe_points):
                new_kp = new_fc.keyframe_points[i]

                new_kp.co = kp.co.copy()
                new_kp.handle_left = kp.handle_left.copy()
                new_kp.handle_right = kp.handle_right.copy()

                new_kp.interpolation = kp.interpolation
                new_kp.handle_left_type = kp.handle_left_type
                new_kp.handle_right_type = kp.handle_right_type

            new_fc.update()
            pass
        pass

    return

def run_op_with_override(op, obj):
    '''Backward compatibility of operator context for Blender 3.0'''
    if hasattr(bpy.context, "temp_override"):
        with bpy.context.temp_override(
            object=obj,
            active_object=obj,
            selected_objects=[obj],
            selected_editable_objects=[obj],
        ):
            op()
    else:
        override = {
            "object": obj,
            "active_object": obj,
            "selected_objects": [obj],
            "selected_editable_objects": [obj],
            "view_layer": bpy.context.view_layer,
        }
        op(override)

class SvRigidBodyPrioritySocketsOnOff(bpy.types.Operator):
    '''Set On or Off Rigid Body parameters'''
    bl_idname = "node.sv_rigid_body_objects_priority_sockets_onoff"
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

class SvRigidBodyUIShowIcon(bpy.types.Operator):
    '''Filled - socket connected, Circle - socket is not connected'''
    bl_idname = "node.sv_rigid_body_ui_show_icon"
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

class SvRigidBodyClearFCurvesOperator(bpy.types.Operator):
    '''Filled - socket connected, Circle - socket is not connected'''
    bl_idname = "node.sv_rigid_body_clear_animation_operator"
    bl_label = "Clear Animations fcurves"

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
        node = context.node
        if node:
            #if node.some_properties_animated==True:
            node.clear_objects_animation = True
            node.process()
            pass
        return {'FINISHED'}

def draw_properties(layout, node_group, node_name):
    node = bpy.data.node_groups[node_group].nodes[node_name]
    #layout.use_property_split = True https://blender.stackexchange.com/questions/161581/how-to-display-the-animate-property-diamond-keyframe-insert-button-2-8x
    #layout.alignment = 'LEFT'
    root_grid = layout.column(align=True).grid_flow(row_major=True, columns=3, align=True, even_columns=False)
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

    # row_op = grid2.row(align=True)
    # row_op.alignment = "LEFT"
    # op = row_op.operator(SvRigidBodyPrioritySocketsOnOff.bl_idname, icon='GP_CAPS_FLAT', text='Hide unlinked sockets', emboss=True)
    # op.node_group = node_group
    # op.node_name  = node_name

    for (param_name, param_settings) in rigid_body_params.items():
        prop_enabled = True
        if 'node_property_name_apply' in param_settings:
            node_property_name_apply = param_settings['node_property_name_apply']
            if getattr(node, node_property_name_apply)==False:
                prop_enabled = False

        # if 'socket_name' in param_settings:
        #     socket_name = param_settings['socket_name']
        #     row = root_grid.row(align=True)
        #     row.enabled = prop_enabled
        #     row.alignment='RIGHT'
        #     #row.template_icon(icon_value=2 if node.inputs[socket_name].is_linked else 3)
        #     row.operator(SvRigidBodyUIShowIcon.bl_idname, icon='RADIOBUT_ON' if node.inputs[socket_name].is_linked else 'RADIOBUT_OFF', text='', emboss=False)

        if 'node_property_map_mode' in param_settings:
            node_property_map_mode = param_settings['node_property_map_mode']
            socket_name = param_settings['socket_name']
            row = root_grid.row(align=True)
            #row.enabled = prop_enabled
            row.alignment='RIGHT'

            op = row.operator(SvRigidBodyUIShowIcon.bl_idname, icon='FORWARD' if node.inputs[socket_name].is_linked else 'RADIOBUT_OFF', text='', emboss=False)
            op.description_text = 'Socket is connected.' if node.inputs[socket_name].is_linked==True else 'Socket is not connected.'

            row = root_grid.row(align=True)
            row.enabled = prop_enabled
            row.prop(node, node_property_map_mode, expand=True)

        # if 'object_rb_property_name_animation_copy' in param_settings:
        #     object_rb_property_name_animation_copy = param_settings['object_rb_property_name_animation_copy']
        #     row = root_grid.row(align=False)
        #     row.alignment='LEFT'
        #     row.prop(node, object_rb_property_name_animation_copy, text='', toggle=True, icon='ANIM')

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

    for (param_name, param_settings) in rigid_body_params.items():
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

            op = row.operator(SvRigidBodyUIShowIcon.bl_idname, icon='FORWARD' if node.inputs[socket_name].is_linked else 'RADIOBUT_OFF', text='', emboss=False)
            op.description_text = 'Socket is connected.' if node.inputs[socket_name].is_linked==True else 'Socket is not connected.'

        if 'object_rb_property_name_animation_copy' in param_settings:
            object_rb_property_name_animation_copy = param_settings['object_rb_property_name_animation_copy']
            row = root_grid.row(align=False)
            row.alignment='LEFT'
            row.prop(node, object_rb_property_name_animation_copy, icon='KEYTYPE_KEYFRAME_VEC' if getattr(node, object_rb_property_name_animation_copy)==True else 'HANDLETYPE_FREE_VEC' )
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

class SV_PT_ViewportDisplayPropertiesDialogRigidBody(bpy.types.Operator):
    '''Overwrite Settings of Rigid Body properties node values and sockets'''
    # this combination do not show this panel on the right side panel
    bl_idname="sv.viewport_display_properties_dialog_rigid_body_objects"
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
        # Прочитать и определить здесь, какие парамерны аниммированы и вывести в окне
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

class SV_PT_CopyAnimatedPropertiesDialogRigidBody(bpy.types.Operator):
    '''Copy Animated Properties of Rigid Body settings (FCurve)'''
    # this combination do not show this panel on the right side panel
    bl_idname="sv.copy_animation_properties_dialog_rigid_body"
    bl_label = "Copy Animated Properties of Rigid Body settings"

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

class SV_PT_ClearAnimatedPropertiesDialogRigidBody(bpy.types.Operator):
    '''Clear Animated Properties of Rigid Body (FCurve)'''
    bl_idname="sv.clear_animation_properties_dialog_rigid_body"
    bl_label = "Clear Animated Properties of Rigid Body"

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

class SV_PT_ViewportDisplayPropertiesRigidBody(bpy.types.Panel):
    '''Additional node properties'''
    # this combination do not show this panel on the right side panel
    bl_idname="SV_PT_ViewportDisplayPropertiesRigidBody"
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

def updateNodeCopy(self, context):
    if self.copy_objects_animation or self.clear_objects_animation:
        self.process_node(context)
    pass

def updateAnimationProperty(self, context):
    # skip node process
    pass

class SvRigidBodyCopy(SverchCustomTreeNode, bpy.types.Node):
    '''Copy/Set Rigid Body params per object'''

    bl_idname = 'SvRigidBodyCopy'
    bl_label = "Rigid Body Copy/Set (Objects)"
    bl_icon = 'RIGID_BODY'
    is_scene_dependent = False
    is_animation_dependent = False
    
    copy_objects_animation : BoolProperty(
        name        = "Copy Animation",
        description = "Copy animation keys of mapped objects to objects",
        default     = False,
        options     = {'SKIP_SAVE'},
        update      = updateNodeCopy,
    )
    clear_objects_animation : BoolProperty(
        name        = "Clear Animation",
        description = "Copy animation keys of mapped objects to objects",
        default     = False,
        options     = {'SKIP_SAVE'},
        update      = updateNodeCopy,
    )

    node_in_use : BoolProperty(
        name        = "Enable",
        description = "On - add Rigid Body settings to all objects\nOff - remove Rigid Body settings from all objects.",
        default     = False,
        update      = updateNode,
    )

    some_properties_animated : BoolProperty(
        name        = "Copy Animation",
        description = "Copy animation keys of mapped objects to objects",
        default     = False,
        options     = {'SKIP_SAVE'},
        #update      = updateNodeCopy,
    )

    node_play_pause_modes = [
            ('RIGID_BODY_NODE_PLAY,PLAY' , "Play" , "Rigid Body does its work"        , 'PLAY' , 0),
            ('RIGID_BODY_NODE_PLAY,PAUSE', "Pause", "Rigid Body skips objects through", 'PAUSE', 1),
        ]

    node_play_pause1 : bpy.props.EnumProperty(
        name        = "Play",
        description = "Apply params or skip node execution",
        items       = node_play_pause_modes,
        default     = 'RIGID_BODY_NODE_PLAY,PLAY',
        update      = updateNode,
    )
    
    object_in_pointer1: bpy.props.PointerProperty(
        name        = "Objects",
        description = "Objects where to copy Rigid Body settings",
        type        = bpy.types.Object,
    )
    
    objects_map1 : bpy.props.IntProperty(
        name        = "Objects Index Map",
        description = "Objects Index Mapping of Rigid Body settings",
        default     = 0,
        #min        = 0,
        update      = updateNode,
    )

    rigid_body_settings1: bpy.props.PointerProperty(
        name        = "Rigid Body settings",
        description = "Objects to get Rigid Body settings",
        type        = bpy.types.Object,
    )

    source_object_pointer_data_from_modes = [
            ('RIGID_BODY_DATA_FROM,OBJECTS' , "Only Objects" , "Apply Rigid Body settings only from Objects in the socket Rigid Body Settings"      , 0),
            ('RIGID_BODY_DATA_FROM,SETTINGS', "Node Settings", "Overlap Rigid Body settings with parameters in this node (also use properties dialog to select what settings to overlap)", 1),
        ]

    source_object_pointer_data_from1 : EnumProperty(
        name        = "Type",
        description = "Role of object in Rigid Body Simulations",
        items       = source_object_pointer_data_from_modes,
        default     = 'RIGID_BODY_DATA_FROM,OBJECTS',
        update      = updateNode,
    )

    objects_map_mode_modes = [
            ('RIGID_BODY_MAP,MAPPING' , "Mapping" , "Mapping objects by input socket data"          , 'PARTICLES', 0),
            ('RIGID_BODY_MAP,INDEXING', "Indexing", "Mapping objects by indexes (ignore mapping)"   , 'SORTSIZE' , 1),
        ]

    objects_map_mode1 : EnumProperty(
        name        = "Objects map mode",
        description = "Mappings Objects by map or by Indexes",
        items       = objects_map_mode_modes,
        default     = 'RIGID_BODY_MAP,MAPPING',
        update      = updateNode,
    )

    rigid_body_type_modes = [
            ('RIGID_BODY_TYPE,ACTIVE' , "Active" , "Object is directly controller by simulation results", 0),
            ('RIGID_BODY_TYPE,PASSIVE', "Passive", "Object is directly controller by animation system"  , 1),
        ]

    rigid_body_type1 : EnumProperty(
        name        = "Type",
        description = "Role of object in Rigid Body Simulations",
        items       = rigid_body_type_modes,
        default     = 'RIGID_BODY_TYPE,ACTIVE',
        update      = updateNode,
    )
    node_type_apply                 : BoolProperty( name = "Type", description = "On - Value in input socket overwrite objects Rigid Body property\nOff - do not overwrite", default = False, update = updateNode)
    object_rb_type_animation_copy   : BoolProperty( name = "Type", description = "On - Copy Animation\nOff - do not copy animation", default = True, update = updateAnimationProperty, ) # This flag used in the operator so do not need to call update
    rigid_body_type_map_mode        : EnumProperty( name = "Type", description = 'Mapping by "Objects Map" or by Indexes', items = objects_map_mode_modes, default = 'RIGID_BODY_MAP,MAPPING', update = updateNode, )

    rigid_body_mass1: FloatProperty(
        name        = "Mass",
        description = "How much the object 'weighs' irrespective of gravity",
        default     = 1.0,
        min         = 0.001,
        precision   = 3,
        update      = updateNode,
    )
    node_mass_apply                 : BoolProperty( name = "Mass", description = "On - Value in input socket overwrite objects Rigid Body property\nOff - do not overwrite", default = False, update = updateNode)
    object_rb_mass_animation_copy   : BoolProperty( name = "Mass", description = "On - Copy Animation\nOff - do not copy animation", default = True, update = updateAnimationProperty, )
    rigid_body_mass_map_mode        : EnumProperty( name = "Mass", description = 'Mapping by "Objects Map" or by Indexes', items = objects_map_mode_modes, default = 'RIGID_BODY_MAP,MAPPING', update = updateNode, )
    
    rigid_body_enabled1 : BoolProperty(
        name        = "Dynamic",
        description = "On - enable Simulation of Rigid Body\nOff - disable Simulation\nDisable before remove node. Rigid Body actively participates to the simulation",
        default     = True,
        update = updateNode)
    node_enabled_apply                  : BoolProperty( name = "Dynamic", description = "On - Value in input socket overwrite objects Rigid Body property\nOff - do not overwrite", default = False, update = updateNode)
    object_rb_enabled_animation_copy    : BoolProperty( name = "Dynamic", description = "On - Copy Animation\nOff - do not copy animation", default = True, update = updateAnimationProperty, )
    rigid_body_enabled_map_mode         : EnumProperty( name = "Dynamic", description = 'Mapping by "Objects Map" or by Indexes', items = objects_map_mode_modes, default = 'RIGID_BODY_MAP,MAPPING', update = updateNode, )

    rigid_body_kinematic1 : BoolProperty(
        name        = "Animated",
        description = "Allow rigid Body to be controlled by the animation system",
        default     = False,
        update      = updateNode,
    )
    node_kinematic_apply                : BoolProperty( name = "Animated", description = "On - Value in input socket overwrite objects Rigid Body property\nOff - do not overwrite", default = False, update = updateNode)
    object_rb_kinematic_animation_copy  : BoolProperty( name = "Animated", description = "On - Copy Animation\nOff - do not copy animation", default = True, update = updateAnimationProperty, )
    rigid_body_kinematic_map_mode       : EnumProperty( name = "Animated", description = 'Mapping by "Objects Map" or by Indexes', items = objects_map_mode_modes, default = 'RIGID_BODY_MAP,MAPPING', update = updateNode, )

    rigid_body_collision_shape_modes = [
            ('RIGID_BODY_SHAPE_MODE,BOX'          , "Box"            , "Box-like shapes (i.e. cubes), including planes (i.e. ground planes)"                                      , 'MESH_CUBE'       , 0),
            ('RIGID_BODY_SHAPE_MODE,SPHERE'       , "Sphere"         , "Sphere like shapes"                                                                                       , 'MESH_UVSPHERE'   , 1),
            ('RIGID_BODY_SHAPE_MODE,CAPSULE'      , "Capsule"        , "Capsule like shapes"                                                                                      , 'MESH_CAPSULE'    , 2),
            ('RIGID_BODY_SHAPE_MODE,CYLINDER'     , "Cylinder"       , "Cylinder like shapes"                                                                                     , 'MESH_CYLINDER'   , 3),
            ('RIGID_BODY_SHAPE_MODE,CONE'         , "Cone"           , "Cone like shapes"                                                                                         , 'MESH_CONE'       , 4),
            ('RIGID_BODY_SHAPE_MODE,CONVEX_HULL'  , "Convex Hull"    , "A mesh-like surface encompassing (i.e. shrinkwrap over) all vertices (best results with fewer vertices)"  , 'MESH_ICOSPHERE'  , 5),
            ('RIGID_BODY_SHAPE_MODE,MESH'         , "Mesh"           , "Mesh consisting of triangles only, allowing for more detailed interactions than convex hulls"             , 'MESH_MONKEY'     , 6),
            ('RIGID_BODY_SHAPE_MODE,COMPOUND'     , "Compound Parent", "Combines all of its direct rigid body children into one rigid object"                                     , 'MESH_DATA'       , 7),
        ]

    rigid_body_collision_shape1 : EnumProperty(
        name        = "Shape",
        description = "Collision Shape of object in Rigid Body Simulations",
        items       = rigid_body_collision_shape_modes,
        default     = 'RIGID_BODY_SHAPE_MODE,CONVEX_HULL',
        update      = updateNode,
    )
    node_collision_shape_apply              : BoolProperty( name = "Shape", description = "On - Value in input socket overwrite objects Rigid Body property\nOff - do not overwrite", default = False, update = updateNode)
    object_rb_collision_shape_animation_copy: BoolProperty( name = "Shape", description = "On - Copy Animation\nOff - do not copy animation", default = True, update = updateAnimationProperty, )
    rigid_body_collision_shape_map_mode     : EnumProperty( name = "Shape", description = 'Mapping by "Objects Map" or by Indexes', items = objects_map_mode_modes, default = 'RIGID_BODY_MAP,MAPPING', update = updateNode, )

    rigid_body_mesh_source_modes = [
            ('RIGID_BODY_MESH_SOURCE,BASE'   , "Base"   , "Base mesh"                                  , 0),
            ('RIGID_BODY_MESH_SOURCE,DEFORM' , "Deform" , "Deformations (shape keys, deform modifiers)", 1),
            ('RIGID_BODY_MESH_SOURCE,FINAL'  , "Final"  , "All modifiers"                              , 2),
        ]

    rigid_body_mesh_source1 : EnumProperty(
        name        = "Source",
        description = "Source of the mesh used to create collision shape",
        items       = rigid_body_mesh_source_modes,
        default     = 'RIGID_BODY_MESH_SOURCE,DEFORM',
        update      = updateNode,
    )
    node_mesh_source_apply              : BoolProperty( name = "Source", description = "On - Value in input socket overwrite objects Rigid Body property\nOff - do not overwrite", default = False, update = updateNode)
    object_rb_mesh_source_animation_copy: BoolProperty( name = "Source", description = "On - Copy Animation\nOff - do not copy animation", default = True, update = updateAnimationProperty, )
    rigid_body_mesh_source_map_mode     : EnumProperty( name = "Source", description = 'Mapping by "Objects Map" or by Indexes', items = objects_map_mode_modes, default = 'RIGID_BODY_MAP,MAPPING', update = updateNode, )
    
    rigid_body_use_deform1 : BoolProperty(
        name        = "Deforming",
        description = "Rigid body deforms during simulation",
        default     = False,
        update      = updateNode,
    )
    node_use_deform_apply               : BoolProperty( name = "Deforming", description = "On - Value in input socket overwrite objects Rigid Body property\nOff - do not overwrite", default = False, update = updateNode)
    object_rb_use_deform_animation_copy : BoolProperty( name = "Deforming", description = "On - Copy Animation\nOff - do not copy animation", default = True, update = updateAnimationProperty, )
    rigid_body_use_deform_map_mode      : EnumProperty( name = "Deforming", description = 'Mapping by "Objects Map" or by Indexes', items = objects_map_mode_modes, default = 'RIGID_BODY_MAP,MAPPING', update = updateNode, )

    rigid_body_friction1: FloatProperty(
        name        = "Friction",
        description = "Resistance of object to movement",
        default     = 0.000,
        min         = 0.0,
        max         = 1.0,
        update      = updateNode,
    )
    node_friction_apply                 : BoolProperty( name = "Friction", description = "On - Value in input socket overwrite objects Rigid Body property\nOff - do not overwrite", default = False, update = updateNode)
    object_rb_friction_animation_copy   : BoolProperty( name = "Friction", description = "On - Copy Animation\nOff - do not copy animation", default = True, update = updateAnimationProperty, )
    rigid_body_friction_map_mode        : EnumProperty( name = "Friction", description = 'Mapping by "Objects Map" or by Indexes', items = objects_map_mode_modes, default = 'RIGID_BODY_MAP,MAPPING', update = updateNode, )

    rigid_body_restitution1: FloatProperty(
        name        = "Bounciness",
        default     = 0.000,
        min         = 0.0,
        max         = 1.0,
        description = "Tendency of object to bounce after colliding with another (0 = stays still, 1 = perfectly elastic)",
        update      = updateNode,
    )
    node_restitution_apply              : BoolProperty( name = "Bounciness", description = "On - Value in input socket overwrite objects Rigid Body property\nOff - do not overwrite", default = False, update = updateNode)
    object_rb_restitution_animation_copy: BoolProperty( name = "Bounciness", description = "On - Copy Animation\nOff - do not copy animation", default = True, update = updateAnimationProperty, )
    rigid_body_restitution_map_mode     : EnumProperty( name = "Bounciness", description = 'Mapping by "Objects Map" or by Indexes', items = objects_map_mode_modes, default = 'RIGID_BODY_MAP,MAPPING', update = updateNode, )
    
    rigid_body_use_margin1 : BoolProperty(
        name        = "Collision Margin",
        default     = False,
        description = "Use custom collision margin (some shapes will have a visible gap around them)",
        update      = updateNode,
    )
    node_use_margin_apply               : BoolProperty( name = "Collision Margin", description = "On - Value in input socket overwrite objects Rigid Body property\nOff - do not overwrite", default = False, update = updateNode)
    object_rb_use_margin_animation_copy : BoolProperty( name = "Collision Margin", description = "On - Copy Animation\nOff - do not copy animation", default = True, update = updateAnimationProperty, )
    rigid_body_use_margin_map_mode      : EnumProperty( name = "Collision Margin", description = 'Mapping by "Objects Map" or by Indexes', items = objects_map_mode_modes, default = 'RIGID_BODY_MAP,MAPPING', update = updateNode, )

    rigid_body_collision_margin1: FloatProperty(
        name        = "Margin",
        description = "Threshold of distance near surface where collisions are still considered (best results when non-zero)",
        default     = 0.000,
        min         = 0.0,
        max         = 1.0,
        update      = updateNode,
    )
    node_collision_margin_apply                 : BoolProperty( name = "Margin", description = "On - Value in input socket overwrite objects Rigid Body property\nOff - do not overwrite", default = False, update = updateNode)
    object_rb_collision_margin_animation_copy   : BoolProperty( name = "Margin", description = "On - Copy Animation\nOff - do not copy animation", default = True, update = updateAnimationProperty, )
    rigid_body_collision_margin_map_mode        : EnumProperty( name = "Margin", description = 'Mapping by "Objects Map" or by Indexes', items = objects_map_mode_modes, default = 'RIGID_BODY_MAP,MAPPING', update = updateNode, )

    rigid_body_collision_collections1: BoolVectorProperty(
        name        = "Collision Collection",
        description = "Collision collections rigid body belongs to",
        size=20,
        update      = updateNode,
    )
    node_collision_collections_apply                : BoolProperty( name = "Collision Collection", description = "On - Value in input socket overwrite objects Rigid Body property\nOff - do not overwrite", default = False, update = updateNode)
    object_rb_collision_collections_animation_copy  : BoolProperty( name = "Collision Collection", description = "On - Copy Animation\nOff - do not copy animation", default = True, update = updateAnimationProperty, )
    rigid_body_collision_collections_map_mode       : EnumProperty( name = "Collision Collection", description = 'Mapping by "Objects Map" or by Indexes', items = objects_map_mode_modes, default = 'RIGID_BODY_MAP,MAPPING', update = updateNode, )

    rigid_body_linear_damping1: FloatProperty(
        name        = "Damping Translation",
        description = "Amount of linear velocity that is lost over time",
        default     = 0.000,
        min         = 0.04,
        max         = 1.0,
        precision   = 3,
        update      = updateNode,
    )
    node_linear_damping_apply               : BoolProperty( name = "Damping Translation", description = "On - Value in input socket overwrite objects Rigid Body property\nOff - do not overwrite", default = False, update = updateNode)
    object_rb_linear_damping_animation_copy : BoolProperty( name = "Damping Translation", description = "On - Copy Animation\nOff - do not copy animation", default = True, update = updateAnimationProperty, )
    rigid_body_linear_damping_map_mode      : EnumProperty( name = "Damping Translation", description = 'Mapping by "Objects Map" or by Indexes', items = objects_map_mode_modes, default = 'RIGID_BODY_MAP,MAPPING', update = updateNode, )

    rigid_body_angular_damping1: FloatProperty(
        name        = "Rotation",
        description = "Amount of angular velocity that is lost over time",
        default     = 0.000,
        min         = 0.1,
        max         = 1.0,
        precision   = 3,
        update      = updateNode,
    )
    node_angular_damping_apply              : BoolProperty( name = "Rotation", description = "On - Value in input socket overwrite objects Rigid Body property\nOff - do not overwrite", default = False, update = updateNode)
    object_rb_angular_damping_animation_copy: BoolProperty( name = "Rotation", description = "On - Copy Animation\nOff - do not copy animation", default = True, update = updateAnimationProperty, )
    rigid_body_angular_damping_map_mode     : EnumProperty( name = "Rotation", description = 'Mapping by "Objects Map" or by Indexes', items = objects_map_mode_modes, default = 'RIGID_BODY_MAP,MAPPING', update = updateNode, )
    
    rigid_body_use_deactivation1 : BoolProperty(
        name        = "Deactivation",
        description = "Enable deactivation of resting rigid bodies (increases performance and stability but can cause glitches)",
        default     = False,
        update      = updateNode,
    )
    node_use_deactivation_apply                 : BoolProperty( name = "Deactivation", description = "On - Value in input socket overwrite objects Rigid Body property\nOff - do not overwrite", default = False, update = updateNode)
    object_rb_use_deactivation_animation_copy   : BoolProperty( name = "Deactivation", description = "On - Copy Animation\nOff - do not copy animation", default = True, update = updateAnimationProperty, )
    rigid_body_use_deactivation_map_mode        : EnumProperty( name = "Deactivation", description = 'Mapping by "Objects Map" or by Indexes', items = objects_map_mode_modes, default = 'RIGID_BODY_MAP,MAPPING', update = updateNode, )
    
    rigid_body_use_start_deactivated1 : BoolProperty(
        name        = "Start Deactivated",
        description = "Deactivate rigid body at the start of the simulation",
        default     = False,
        update      = updateNode,
    )
    node_use_start_deactivated_apply                : BoolProperty( name = "Start Deactivated", description = "On - Value in input socket overwrite objects Rigid Body property\nOff - do not overwrite", default = False, update = updateNode)
    object_rb_use_start_deactivated_animation_copy  : BoolProperty( name = "Start Deactivated", description = "On - Copy Animation\nOff - do not copy animation", default = True, update = updateAnimationProperty, )
    rigid_body_use_start_deactivated_map_mode       : EnumProperty( name = "Start Deactivated", description = 'Mapping by "Objects Map" or by Indexes', items = objects_map_mode_modes, default = 'RIGID_BODY_MAP,MAPPING', update = updateNode, )

    rigid_body_deactivate_linear_velocity1: FloatProperty(
        name        = "Velocity Linear",
        description = "Linear Velocity below which simulation stops simulating object",
        default     = 0.4,
        min         = 0.0,
        #max        = 1.0,
        update      = updateNode,
    )
    node_deactivate_linear_velocity_apply               : BoolProperty( name = "Velocity Linear", description = "On - Value in input socket overwrite objects Rigid Body property\nOff - do not overwrite", default = False, update = updateNode)
    object_rb_deactivate_linear_velocity_animation_copy : BoolProperty( name = "Velocity Linear", description = "On - Copy Animation\nOff - do not copy animation", default = True, update = updateAnimationProperty, )
    rigid_body_deactivate_linear_velocity_map_mode      : EnumProperty( name = "Velocity Linear", description = 'Mapping by "Objects Map" or by Indexes', items = objects_map_mode_modes, default = 'RIGID_BODY_MAP,MAPPING', update = updateNode, )

    rigid_body_deactivate_angular_velocity1: FloatProperty(
        name        = "Angular",
        description = "Angular Velocity below which simulation stops simulating object",
        default     = 0.000,
        min         = 0.5,
        #max        = 1.0,
        update      = updateNode,
    )
    node_deactivate_angular_velocity_apply              : BoolProperty( name = "Angular", description = "On - Value in input socket overwrite objects Rigid Body property\nOff - do not overwrite", default = False, update = updateNode)
    object_rb_deactivate_angular_velocity_animation_copy: BoolProperty( name = "Angular", description = "On - Copy Animation\nOff - do not copy animation", default = True, update = updateAnimationProperty, )
    rigid_body_deactivate_angular_velocity_map_mode     : EnumProperty( name = "Angular", description = 'Mapping by "Objects Map" or by Indexes', items = objects_map_mode_modes, default = 'RIGID_BODY_MAP,MAPPING', update = updateNode, )
    
    def custom_draw_collision_collections(self, socket, context, layout):
        if socket.name in rigid_body_socket_names:
            node_property_name_apply = rigid_body_socket_names[socket.name]['node_property_name_apply']
            if getattr(self, node_property_name_apply)==False:
                layout.enabled = False
                #layout.alignment = 'RIGHT'
                # layout.use_property_decorate = False
                # layout.use_property_split = True
            pass

        if self.node_play_pause1=='RIGID_BODY_NODE_PLAY,PAUSE':
            layout.enabled = False

        col = layout.column(align=True)
        col.alignment = 'RIGHT'
        row = col.row(align=True)
        row.alignment = "RIGHT" if layout.enabled==False else "LEFT"
        if self.source_object_pointer_data_from1=='RIGID_BODY_DATA_FROM,OBJECTS':
            row.enabled = False
            
        if socket.is_linked==True:
            row.label(text=socket.label + f". {socket.objects_number or ''}")
        else:
            row.label(text=socket.label)

        row = col.row()
        row.alignment = "RIGHT" if layout.enabled==False else "LEFT"
        if self.source_object_pointer_data_from1=='RIGID_BODY_DATA_FROM,OBJECTS' or self.node_in_use==False:
            row.enabled = False
        grid = row.grid_flow(row_major=True, columns=2, even_columns=True, even_rows=True)
        grid1 = grid.grid_flow(row_major=True, columns=5, even_columns=True, even_rows=True, align=True)
        for I in range(0,5):
            grid1.prop(self, "rigid_body_collision_collections1", index=I, text=str(I), toggle=True)
        for I in range(10,15):
            grid1.prop(self, "rigid_body_collision_collections1", index=I, text=str(I), toggle=True)
        grid2 = grid.grid_flow(row_major=True, columns=5, even_columns=True, even_rows=True, align=True)
        for I in range(5,10):
            grid2.prop(self, "rigid_body_collision_collections1", index=I, text=str(I), toggle=True)
        for I in range(15,20):
            grid2.prop(self, "rigid_body_collision_collections1", index=I, text=str(I), toggle=True)

        pass


    def sv_draw_buttons(self, context, layout):
        col = layout.row(align=True)
        col.alignment = "LEFT"
        col.row(align=True)
        col.prop(self, 'node_play_pause1', text='',expand=True)

        box = layout.box()
        if self.node_play_pause1=='RIGID_BODY_NODE_PLAY,PAUSE':
            #box.enabled = False
            pass
        row = box.row(align=True)
        row.prop(self, 'node_in_use', text=('Rigid Body Activated' if self.node_in_use==True else 'Rigid Body Removed'), icon=('X' if self.node_in_use==True else 'RIGID_BODY') )
        row.separator()
        #row.row().prop(self, 'copy_objects_animation', toggle=True, icon='RENDER_RESULT', text='')
        row.row(align=True).operator(SV_PT_CopyAnimatedPropertiesDialogRigidBody.bl_idname, icon='RENDER_RESULT', text="", emboss=True)
        # row.prop(self, 'clear_objects_animation', toggle=True, icon='CANCEL', text='')
        row1 = row.row(align=True)
        if self.some_properties_animated==True:
            row1.alert = True
            # op = row1.operator(SvRigidBodyUIShowIcon.bl_idname, icon='ERROR', text="", emboss=True, )
            # op.description_text = "Objects contains animation. Some simulation of Rigid body can be broken. Remove animation."
            op = row1.operator(SV_PT_ClearAnimatedPropertiesDialogRigidBody.bl_idname, icon='ERROR', text="", emboss=True)
            #op = row1.operator(SvRigidBodyClearFCurvesOperator.bl_idname, icon='ERROR', text="", emboss=True, )
            op.description_text = 'These are animations fcurves data. Simulation results with Sverchok may be unexpected. It is recommended to clear the animation by clicking this button or deactivate the Sverchok scene in sidebar N/Sverchok tab.'
        else:
            # op = row1.operator(SvRigidBodyUIShowIcon.bl_idname, icon='BLANK1', text="", emboss=True, )
            # op.description_text = "Objects doesn't contains animation."
            op = row1.operator(SV_PT_ClearAnimatedPropertiesDialogRigidBody.bl_idname, icon='ANIM_DATA', text="", emboss=True)
            # op = row1.operator(SvRigidBodyClearFCurvesOperator.bl_idname, icon='ANIM_DATA', text="", emboss=True, )
            op.description_text = 'These are no animations fcurves data. You can set up the Rigid Body settings.'

        elem = box.row(align=True)
        elem.label(text='Apply Rigid Body settings from:')
        
        # elem = box.row(align=True)
        # elem.alignment='RIGHT'
        # elem.label(text='Settings:')

        elem = box.row(align=True)
        elem.prop(self, 'source_object_pointer_data_from1', expand=True)
        elem.separator()
        row = elem.row(align=True)
        row.column(align=True).operator(SV_PT_ViewportDisplayPropertiesDialogRigidBody.bl_idname, icon='TOOL_SETTINGS', text="", emboss=True)
        row.column(align=True).popover(panel=SV_PT_ViewportDisplayPropertiesRigidBody.bl_idname, icon='DOWNARROW_HLT', text="")

        # elem = box.column(align=True)
        # elem.row().label(text='Objects map mode:')
        # elem.row(align=True).prop(self, 'objects_map_mode1', expand=True)

        pass

    def custom_draw_input_sockets_objects(self, socket, context, layout):
        if socket.is_linked==True:
            layout.label(text=socket.label + f". {socket.objects_number or ''}")
        else:
            layout.prop(self, socket.prop_name, text=self.label or None)
        return

    def custom_draw_input_sockets_objects_map(self, socket, context, layout):
        row = layout.row(align=True)
        split = row.split(factor=0.6)
        col = split.column(align=True)
        if self.objects_map_mode1=='RIGID_BODY_MAP,INDEXING' or self.node_in_use==False or self.node_play_pause1=='RIGID_BODY_NODE_PLAY,PAUSE':
            col.enabled = False
        if socket.is_linked==True:
            col.alignment = "LEFT"
            col.label(text=socket.label + f". {socket.objects_number or ''}")
        else:
            col.prop(self, socket.prop_name, text=self.label or None)
        row2 = split.row(align=True)
        row2.prop(self, 'objects_map_mode1', text='',)
        return

    def custom_draw_input_sockets_rigid_body_source_objects(self, socket, context, layout):
        if self.node_in_use==False or self.node_play_pause1=='RIGID_BODY_NODE_PLAY,PAUSE':
            layout.enabled = False
        if socket.is_linked==True:
            layout.alignment = "LEFT"
            layout.label(text=socket.label + f". {socket.objects_number or ''}")
        else:
            layout.prop(self, socket.prop_name, text=self.label or None)
        return

    def custom_draw_input_sockets_rigid_body_params(self, socket, context, layout):
        if self.source_object_pointer_data_from1=='RIGID_BODY_DATA_FROM,OBJECTS' or self.node_in_use==False or self.node_play_pause1=='RIGID_BODY_NODE_PLAY,PAUSE':
            layout.enabled = False

        if socket.name in rigid_body_socket_names:
            node_property_name_apply = rigid_body_socket_names[socket.name]['node_property_name_apply']
            if getattr(self, node_property_name_apply)==False:
                layout.enabled = False
                layout.use_property_decorate = False
                layout.use_property_split = True
            pass

        if socket.is_linked==True:
            layout.label(text=socket.label + f". {socket.objects_number or ''}")
        else:
            layout.prop(self, socket.prop_name, text=self.label or None)
        return

    def sv_init(self, context):
        self.width = 260

        self.inputs.new('SvObjectSocket' , 'objects'                                ).prop_name = 'object_in_pointer1'
        self.inputs.new('SvStringsSocket', 'objects_map'                            ).prop_name = 'objects_map1'
        self.inputs.new('SvObjectSocket' , 'rigid_body_settings'                    ).prop_name = 'rigid_body_settings1'
        self.inputs.new('SvStringsSocket', 'rigid_body_type'                        ).prop_name = 'rigid_body_type1'
        self.inputs.new('SvStringsSocket', 'rigid_body_mass'                        ).prop_name = 'rigid_body_mass1'
        self.inputs.new('SvStringsSocket', 'rigid_body_enabled'                     ).prop_name = 'rigid_body_enabled1'
        self.inputs.new('SvStringsSocket', 'rigid_body_kinematic'                   ).prop_name = 'rigid_body_kinematic1'
        self.inputs.new('SvStringsSocket', 'rigid_body_collision_shape'             ).prop_name = 'rigid_body_collision_shape1'
        self.inputs.new('SvStringsSocket', 'rigid_body_mesh_source'                 ).prop_name = 'rigid_body_mesh_source1'
        self.inputs.new('SvStringsSocket', 'rigid_body_use_deform'                  ).prop_name = 'rigid_body_use_deform1'
        self.inputs.new('SvStringsSocket', 'rigid_body_friction'                    ).prop_name = 'rigid_body_friction1'
        self.inputs.new('SvStringsSocket', 'rigid_body_restitution'                 ).prop_name = 'rigid_body_restitution1'
        self.inputs.new('SvStringsSocket', 'rigid_body_use_margin'                  ).prop_name = 'rigid_body_use_margin1'
        self.inputs.new('SvStringsSocket', 'rigid_body_collision_margin'            ).prop_name = 'rigid_body_collision_margin1'
        self.inputs.new('SvStringsSocket', 'rigid_body_collision_collections'       ).prop_name = 'rigid_body_collision_collections1' # assigned prop_name conflict with custom_draw 
        self.inputs.new('SvStringsSocket', 'rigid_body_linear_damping'              ).prop_name = 'rigid_body_linear_damping1'
        self.inputs.new('SvStringsSocket', 'rigid_body_angular_damping'             ).prop_name = 'rigid_body_angular_damping1'
        self.inputs.new('SvStringsSocket', 'rigid_body_use_deactivation'            ).prop_name = 'rigid_body_use_deactivation1'
        self.inputs.new('SvStringsSocket', 'rigid_body_use_start_deactivated'       ).prop_name = 'rigid_body_use_start_deactivated1'
        self.inputs.new('SvStringsSocket', 'rigid_body_deactivate_linear_velocity'  ).prop_name = 'rigid_body_deactivate_linear_velocity1'
        self.inputs.new('SvStringsSocket', 'rigid_body_deactivate_angular_velocity' ).prop_name = 'rigid_body_deactivate_angular_velocity1'
        
        for (sn, params) in (rigid_body_params | {
                'objects'             : {'node_property_name': 'object_in_pointer1'     , 'socket_name': 'objects'              , },
                'objects_map'         : {'node_property_name': 'objects_map1'           , 'socket_name': 'objects_map'          , },
                'rigid_body_settings' : {'node_property_name': 'rigid_body_settings1'   , 'socket_name': 'rigid_body_settings'  , }
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
            self.inputs[socket_name].custom_draw = 'custom_draw_input_sockets_rigid_body_params'
            pass

        # rewrite some input sockets
        self.inputs['objects'                           ].custom_draw = 'custom_draw_input_sockets_objects'
        self.inputs['objects_map'                       ].custom_draw = 'custom_draw_input_sockets_objects_map'
        self.inputs['rigid_body_collision_collections'  ].custom_draw = 'custom_draw_collision_collections'
        self.inputs['rigid_body_collision_collections'  ].label       = 'Collision Collection'
        self.inputs['rigid_body_settings'               ].custom_draw = 'custom_draw_input_sockets_rigid_body_source_objects'
        
        self.outputs.new('SvObjectSocket', 'objects')
        self.outputs['objects'].label       = 'Objects'
        pass

    def process(self):
        if not any(socket.is_linked for socket in self.inputs):
            return

        #bpy.context.view_layer.update()

        objects             = self.inputs['objects'             ].sv_get(deepcopy=False, default=[self.object_in_pointer1])
        objects_map         = self.inputs['objects_map'         ].sv_get(deepcopy=False, default=[self.objects_map1])
        rigid_body_settings = self.inputs['rigid_body_settings' ].sv_get(deepcopy=False, default=[self.rigid_body_settings1] if self.rigid_body_settings1 else [])
        if self.inputs['rigid_body_settings' ].is_linked==False:
            rigid_body_settings = [self.rigid_body_settings1] if self.rigid_body_settings1 else []

        if self.node_play_pause1=='RIGID_BODY_NODE_PLAY,PLAY':
            if self.node_in_use==True:
                if self.inputs['objects_map'].is_linked==False:
                    objects_map = [self.objects_map1] * len(objects)
                    pass

                if self.objects_map_mode1=='RIGID_BODY_MAP,INDEXING':
                    objects_map = [I for I in range(len(objects))]
                    pass
                set_objects_map = set(objects_map)
                len_objects_map = len(objects_map)
                if len_objects_map==0:
                    raise Exception(f'001. Objects map has no elements: 0')
                
                index_min_settings = min(set_objects_map)
                index_max_settings = max(set_objects_map)
                len_rigid_body_settings = len(rigid_body_settings)
                # indexes can be negative. )))
                if self.source_object_pointer_data_from1=='RIGID_BODY_DATA_FROM,OBJECTS' and self.objects_map_mode1=='RIGID_BODY_MAP,MAPPING' and (index_min_settings<-(len_rigid_body_settings-1) or (len_rigid_body_settings-1)<index_max_settings):
                    raise Exception(f'002. Indexes in Objects map is out of range: [{index_min_settings}:{index_max_settings}] out of Rigid Body settings [{-len_rigid_body_settings}:{len_rigid_body_settings}]')

                input_sockets_settings = dict()
                # read data in general input sockets
                for (name, params) in rigid_body_params.items():
                    node_property_name = params['node_property_name']
                    socket_name = params['socket_name']
                    if socket_name not in self.inputs:
                        raise Exception(f'003. No input socket with name {socket_name}.')

                    node_property_name_apply = params['node_property_name_apply']
                    node_property_priority_value = getattr(self, node_property_name_apply)
                    if node_property_priority_value==True:
                        node_property_map_mode = params['node_property_map_mode']
                        property_map_mode = getattr(self, node_property_map_mode)

                        prop_type = None
                        if hasattr(self.__class__, 'bl_rna')==True and node_property_name in self.__class__.bl_rna.properties:
                            prop = self.__class__.bl_rna.properties[node_property_name]
                            prop_type = prop.type
                        else:
                            # development error.
                            raise Exception(f'004. Unknown property {node_property_name}. Check settings params')
                        
                        default_prop_value = getattr(self, node_property_name)
                        if prop_type=='ENUM':
                            # enum properties of default value has prefix to remove
                            default_prop_value = default_prop_value.split(',')[-1]
                            pass
                        socket = self.inputs[socket_name]
                        if socket.is_linked==True:
                            socket_value = dict()
                            _socket_value        = self.inputs[socket_name].sv_get(deepcopy=False)
                            try:
                                if property_map_mode=='RIGID_BODY_MAP,MAPPING':
                                    for I in objects_map:
                                        socket_value[I] = _socket_value[I]
                                    pass
                                elif property_map_mode=='RIGID_BODY_MAP,INDEXING':
                                    for I in range(len(objects)):
                                        socket_value[I] = _socket_value[I]
                                    pass
                                else:
                                    raise Exception(f'012. unknown map mode: {property_map_mode}.')
                            except IndexError:
                                raise Exception(f'013. {socket_name}[{I}] out of range in mode "{property_map_mode}". Length of data in this socket is {len(_socket_value)}')
                            except Exception as _ex:
                                raise Exception(f'014. Error getting {socket_name}[{I}]. {_ex}')
                            pass
                        else:
                            # if socket is not connected then fill socket with default values
                            socket_value = dict()
                            if property_map_mode=='RIGID_BODY_MAP,MAPPING':
                                for I in objects_map:
                                    socket_value[I] = default_prop_value
                                pass
                            elif property_map_mode=='RIGID_BODY_MAP,INDEXING':
                                for I in range(len(objects)):
                                    socket_value[I] = default_prop_value
                                pass
                            else:
                                raise Exception(f'011. unknown map mode: {property_map_mode}.')
                            pass
                        input_sockets_settings[name] = socket_value
                    else:
                        pass
                    pass

                if len(objects)<len(objects_map):
                    raise Exception(f"005. Number of Objects are less Number of Objects Map")
                else:
                    if bpy.context.mode == 'OBJECT':

                        if self.source_object_pointer_data_from1=='RIGID_BODY_DATA_FROM,OBJECTS':
                            if len_rigid_body_settings==0:
                                raise Exception(f'006. No Rigid Body settings')
                        
                        inputs_settings = []
                        inputs_objects_fcurves = []
                        for I in ( range(len(objects_map)) if self.objects_map_mode1=='RIGID_BODY_MAP,MAPPING' else range(len(objects)) ):
                            rigid_body_settings_ID = dict()
                            ID = objects_map[I] if self.objects_map_mode1=='RIGID_BODY_MAP,MAPPING' else I
                            try:
                                object_rigid_body_settings_ID = rigid_body_settings[ID]
                            except IndexError:
                                raise Exception(f'0015. "Rigid Body settings"[{ID}] out of range. Number of objects in Socket "Rigid Body settings" [{len(objects_map)} items] in Indexing mode has to be equals to "Objects" sockets [{len(objects)}]')
                            except Exception as _ex:
                                raise Exception(f'0016. "Rigid Body settings"[{ID}] exception: {_ex}')
                            
                            if hasattr(object_rigid_body_settings_ID, 'rigid_body')==False:
                                raise Exception(f'0016. No rigid_body attribute in "Rigid Body settings"[{ID}]. Check object can has rigid body settings')
                            inputs_objects_fcurves.append( get_fcurves(object_rigid_body_settings_ID) )
                            rigid_body = object_rigid_body_settings_ID.rigid_body
                            if rigid_body:
                                pass
                            else:
                                raise Exception(f'0017. You are trying to use object named "{object_rigid_body_settings_ID.name}" as Rigid Body [Socket Index Map ID={ID}], but Rigid Body is not enabled. Enable Rigid Body for "{object_rigid_body_settings_ID.name}" in the propery panel')

                            for (name, param) in rigid_body_params.items():
                                rigid_body_settings_ID[name] = getattr(rigid_body, name)

                            if self.source_object_pointer_data_from1=='RIGID_BODY_DATA_FROM,SETTINGS':
                                for (name, param) in rigid_body_params.items():
                                        node_property_name_apply = param['node_property_name_apply']
                                        node_property_map_mode = param['node_property_map_mode']
                                        if getattr(self, node_property_name_apply)==True:
                                            property_map_mode = getattr(self, node_property_map_mode)
                                            if property_map_mode=='RIGID_BODY_MAP,MAPPING':
                                                value = input_sockets_settings[name][ID]
                                            elif property_map_mode=='RIGID_BODY_MAP,INDEXING':
                                                value = input_sockets_settings[name][I]
                                            else:
                                                # developer exception
                                                raise Exception(f'0018. Unknown map mode "{property_map_mode}" for property {name}')
                                            rigid_body_settings_ID[name] = value
                                        else:
                                            pass
                                pass

                            inputs_settings.append(rigid_body_settings_ID)
                            pass
                        pass

                        if not bpy.context.scene.rigidbody_world:
                            bpy.ops.rigidbody.world_add()

                        self.some_properties_animated = False
                        for I, obj in enumerate(objects):
                            ID = objects_map[I] if self.objects_map_mode1=='RIGID_BODY_MAP,MAPPING' else I
                            if obj:
                                # Add active object as Rigid Body
                                if hasattr(obj, 'rigid_body')==False or obj.rigid_body==None:
                                    # bpy.context.view_layer.objects.active = obj
                                    # obj.select_set(True)
                                    # bpy.ops.rigidbody.object_add()

                                    # with bpy.context.temp_override(
                                    #     object                      =  obj,
                                    #     active_object               =  obj,
                                    #     selected_objects            = [obj],
                                    #     selected_editable_objects   = [obj],
                                    #     view_layer=bpy.context.view_layer, ):
                                    #         bpy.ops.rigidbody.object_add()
                                    #         pass
                                    run_op_with_override(bpy.ops.rigidbody.object_add, obj)
                                pass

                                if self.copy_objects_animation:
                                    try:
                                        copy_fcurves(rigid_body_settings[ID], obj, [f'rigid_body.{name}' for name in rigid_body_params if getattr(self, rigid_body_params[name]['object_rb_property_name_animation_copy']) ])
                                    except Exception as ex:
                                        print(f"0019. Произошла ошибка при копировании анимации {ex}")
                                        pass
                                    pass
                                if self.clear_objects_animation:
                                    try:
                                        remove_fcurves(obj, [f'rigid_body.{name}' for name in rigid_body_params if getattr(self, rigid_body_params[name]['object_rb_property_name_animation_copy'])] )
                                    except Exception as ex:
                                        print(f"0020. Произошла ошибка при очистке анимации {ex}")
                                        pass
                                    pass
                                
                                inputs_settings_I = inputs_settings[I]
                                inputs_objects_fcurves_I = inputs_objects_fcurves[I]
                                obj_fcurved = get_fcurves(obj)
                                for (name, value) in inputs_settings_I.items():
                                    inputs_objects_fcurves_I_param = [fc.data_path for fc in inputs_objects_fcurves_I if fc.data_path=='rigid_body.'+name]
                                    obj_fcurved_param = [fc.data_path for fc in obj_fcurved if fc.data_path=='rigid_body.'+name]
                                    
                                    if inputs_objects_fcurves_I_param and obj_fcurved_param:
                                        # if both params are animated they cannot overwrite each other
                                        continue

                                    if not obj_fcurved_param:
                                        # set value if property is not animated
                                        if hasattr(obj.rigid_body, name):
                                            
                                            obj_rigid_body_name_value = getattr( obj.rigid_body, name, value )
                                            comp=True
                                            if isinstance( obj_rigid_body_name_value, bpy.types.bpy_prop_array)==True:
                                                # convert both value to list. bpy.types.bpy_prop_array is look like list, but they are not lists
                                                # this happens with collision collection
                                                value = [v for v in value]
                                                obj_rigid_body_name_value = [v for v in obj_rigid_body_name_value]
                                                comp = (len(obj_rigid_body_name_value)==len(value))
                                                pass
                                            
                                            if comp==True and obj_rigid_body_name_value!=value:
                                                # set value if params are different
                                                setattr( obj.rigid_body, name, value )
                                            else:
                                                pass
                                            pass
                                        else:
                                            # TODO what if no attribute???
                                            pass
                                    else:
                                        # TODO: Alert user if property is animated
                                        self.some_properties_animated = True
                                        pass
                                    pass
                                pass
                            else:
                                #raise Exception(f"Object[{I}] is None")
                                pass
                            pass

                        if self.copy_objects_animation or self.clear_objects_animation:
                            self.copy_objects_animation = False
                            self.clear_objects_animation = False

                        # if selected:
                        #     # # восстановить выделение
                        #     # # TODO: Кажется срабатывает событие изменения сцены при этом. Нужно как-то отключить обработку этого события при восстановлении select
                        #     # bpy.ops.object.select_all(action='DESELECT')
                        #     # for obj in selected:
                        #     #     obj.select_set(True)
                        #     pass

                        # восстановить активный
                        # bpy.context.view_layer.objects.active = active_obj
                        pass
                    pass
                pass
            else:
                for I, obj in enumerate(objects):
                    if obj:
                        # Remove Rigid Body settings from Object
                        if hasattr(obj, 'rigid_body')==True and obj.rigid_body is not None:
                            # bpy.context.view_layer.objects.active = obj
                            # obj.select_set(True)
                            # bpy.ops.rigidbody.object_remove()
                            
                            # with bpy.context.temp_override(
                            #     object                      =  obj,
                            #     active_object               =  obj,
                            #     selected_objects            = [obj],
                            #     selected_editable_objects   = [obj],
                            #     view_layer=bpy.context.view_layer, ):
                            #         bpy.ops.rigidbody.object_remove()
                            #         pass
                            run_op_with_override(bpy.ops.rigidbody.object_remove, obj)
                        pass
                    pass
                pass
            pass
        else:
            pass
        self.outputs['objects'].sv_set(objects)
        #bpy.context.view_layer.update()
        pass

classes = [SvRigidBodyClearFCurvesOperator, SvRigidBodyUIShowIcon, SvRigidBodyPrioritySocketsOnOff, SV_PT_ViewportDisplayPropertiesRigidBody, SV_PT_CopyAnimatedPropertiesDialogRigidBody, SV_PT_ClearAnimatedPropertiesDialogRigidBody, SV_PT_ViewportDisplayPropertiesDialogRigidBody, SvRigidBodyCopy]
register, unregister = bpy.utils.register_classes_factory(classes)
