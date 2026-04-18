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

# def copy_object_relations(src_obj, target_obj):
#     """
#     Копирует relations (parent, parent_type, parent_bone),
#     сохраняя мировую трансформацию target_obj (даже если у него уже был parent).
#     """

#     # сохраняем мировую матрицу ДО изменений
#     world_matrix = target_obj.matrix_world.copy()

#     new_parent = src_obj.parent

#     if False and target_obj.parent == new_parent:
#         pass
#     else:

#         # назначаем parent
#         target_obj.parent = new_parent
#         target_obj.parent_type = src_obj.parent_type
#         target_obj.parent_bone = src_obj.parent_bone

#         # КЛЮЧЕВОЙ МОМЕНТ:
#         if new_parent:
#             # сразу задаём корректный inverse
#             target_obj.matrix_parent_inverse = new_parent.matrix_world.inverted() @ world_matrix
#         else:
#             target_obj.matrix_parent_inverse.identity()

#         # теперь восстанавливаем world (уже стабильно)
#         target_obj.matrix_world = world_matrix
#         pass

#     return



# def copy_object_relations(src_obj, target_obj):
#     """
#     Копирует parent/relations,
#     сохраняя ЛОКАЛЬНУЮ трансформацию target_obj
#     (независимо от наличия parent).
#     """

#     # --- 1. сохраняем локальную матрицу
#     local_matrix = target_obj.matrix_local.copy()

#     # new_parent = src_obj.parent
#     # new_parent_type = src_obj.parent_type
#     # new_parent_bone = src_obj.parent_bone
#     new_parent = src_obj.parent
#     new_parent_type = src_obj.parent_type
#     new_parent_bone = src_obj.parent_bone

#     # --- 2. проверка: если ничего не меняется — выходим
#     if (
#         target_obj.parent == new_parent and
#         target_obj.parent_type == new_parent_type and
#         target_obj.parent_bone == new_parent_bone
#     ):
#         return

#     # --- 3. назначаем parent
#     target_obj.parent = new_parent
#     target_obj.parent_type = new_parent_type
#     target_obj.parent_bone = new_parent_bone

#     # --- 4. восстанавливаем локальную трансформацию
#     target_obj.matrix_local = local_matrix

import bpy
from datetime import datetime

def copy_object_relations(src_obj, target_obj):
    #bpy.context.view_layer.update()

    new_parent = src_obj
    # if target_obj.parent == new_parent and target_obj.parent_type == 'OBJECT' and target_obj.parent_bone == "":
    #     return
    
    world_matrix = target_obj.matrix_world.copy()

    target_obj.matrix_world = new_parent.matrix_world.inverted() @ target_obj.matrix_world
    target_obj.parent = new_parent
    target_obj.parent_type = 'OBJECT'
    target_obj.parent_bone = ""
    target_obj.matrix_parent_inverse = new_parent.matrix_world.inverted()
    # target_obj.matrix_world = world_matrix
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


    object_target_pointer1: bpy.props.PointerProperty(
        name="Objects",
        description = "Where to copy material slots",
        type=bpy.types.Object,
    )

    objects_map1 : bpy.props.IntProperty(
        name = "Objects map",
        description = "Original Object Id of Objects Parent list",
        default = 0,
        min = 0,
        update = updateNode)


    object_source_pointer1: bpy.props.PointerProperty(
        name="Objects Parent",
        description = "Objects Parent of Objects",
        type=bpy.types.Object,
    )

    objects_map_mode_modes = [
            ('RIGID_BODY_MAP,MAPPING' , "Mapping" , "Mapping objects by input socket data", 0),
            ('RIGID_BODY_MAP,INDEXING', "Indexing", "Mapping objects by indexes (ignore mapping)"  , 1),
        ]

    objects_map_mode1 : bpy.props.EnumProperty(
        name        = "Objects map mode",
        description = "Mappings Objects by map or by Indexes",
        items       = objects_map_mode_modes,
        default     = 'RIGID_BODY_MAP,MAPPING',
        update      = updateNode,
    )

    def sv_draw_buttons(self, context, layout):
        box = layout.box()
        box.row(align=True).prop(self, 'objects_map_mode1', expand=True)
        row = box.row(align=True)
        row.prop(self, 'copy_objects_parent', toggle=True, icon='RENDER_RESULT', text='')
        row.prop(self, 'clear_objects_parent', toggle=True, icon='CANCEL', text='')
        pass

    def custom_draw_input_sockets(self, socket, context, layout):
        if socket.is_linked==True:
            layout.label(text=socket.label + f". {socket.objects_number}")
        else:
            layout.prop(self, socket.prop_name, text=self.label or None)
        return


    def sv_init(self, context):
        self.inputs.new('SvObjectSocket' , 'object_target_pointers' ).prop_name  = 'object_target_pointer1'
        self.inputs.new('SvStringsSocket', 'objects_maps'           ).prop_name  = 'objects_map1'
        self.inputs.new('SvObjectSocket' , 'object_source_pointers' ).prop_name  = 'object_source_pointer1'

        self.inputs['object_target_pointers'].label  = 'Objects'
        self.inputs['objects_maps'          ].label  = 'Objects map'
        self.inputs['object_source_pointers'].label  = 'Objects with Relations'
        
        self.outputs.new('SvObjectSocket', 'objects'                ).label = "Objects"

        for si in self.inputs:
        # for (sn, params) in ({
        #         '1' : {'node_property_name': 'object_target_pointer1' , 'socket_name': 'object_target_pointers'   , },
        #         '2' : {'node_property_name': 'objects_map1'           , 'socket_name': 'objects_maps'              , },
        #         '3' : {'node_property_name': 'object_source_pointer1' , 'socket_name': 'object_source_pointers'   , }
        #     }).items():
            # node_property_name = si.prop_name
            # socket_name = params['socket_name']
            prop_name = None
            type = None
            description=None
            if hasattr(self.__class__, 'bl_rna')==True and si.prop_name in self.__class__.bl_rna.properties:
                prop = self.__class__.bl_rna.properties[si.prop_name]
                prop_name = prop.name
                type = prop.type
                description = prop.description
            if description:
                si.description = f'{description}'
            if prop_name:
                si.label = f'{prop_name}'
            si.custom_draw = 'custom_draw_input_sockets'
            pass

        pass

    def process(self):
        if not any(socket.is_linked for socket in self.inputs):
            return
        
        bpy.context.view_layer.update()
        
        object_target_pointers  = self.inputs['object_target_pointers' ].sv_get(deepcopy=False, default=[self.object_target_pointer1 ])
        if self.inputs['object_target_pointers'].is_linked==False:
            object_target_pointers = []
            if self.object_target_pointer1:
                object_target_pointers = [self.object_target_pointer1] * len(object_target_pointers)

        objects_maps       = self.inputs['objects_maps'      ].sv_get(deepcopy=False, default=[self.objects_map1      ])
        if self.inputs['objects_maps'].is_linked==False:
            objects_maps = [self.objects_map1] * len(object_target_pointers)

        object_source_pointers  = self.inputs['object_source_pointers' ].sv_get(deepcopy=False, default=[self.object_source_pointer1 ])

        if len(object_target_pointers)==0:
            pass
        else:
            try:
                t1 = datetime.now()-datetime.now()
                for I, obj in enumerate(object_target_pointers):
                    ID = objects_maps[I] if self.objects_map_mode1=='RIGID_BODY_MAP,MAPPING' else I
                    try:
                        object_source_pointers_ID = object_source_pointers[ID]
                    except IndexError:
                        raise Exception(f'0001. "Object"[{ID}] out of range. Number of objects in Socket "Rigid Body settings" [{len(objects_maps)} items] in Indexing mode has to be equals to "Objects" sockets [{len(objects)}]')
                    except Exception as _ex:
                        raise Exception(f'0002. "Rigid Body settings"[{ID}] exception: {_ex}')

                    #if self.copy_objects_parent==True:
                    t2 = datetime.now()
                    copy_object_relations(object_source_pointers_ID, obj)
                    t2 = datetime.now()-t2
                    t1 += t2
                    pass
                pass
                #t1 = datetime.now()-t1
                print(f"t1 = {t1}")
            except Exception as _ex:
                pass
            self.copy_objects_parent=False
        pass

        self.outputs['objects'].sv_set(object_target_pointers)
        #bpy.context.view_layer.update()

classes = [SvSetObjectsReleationNode, ]
register, unregister = bpy.utils.register_classes_factory(classes)
