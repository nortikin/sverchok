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


class SvCopyMaterialSlotsNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: modifiers
    Tooltip:
    """
    bl_idname = 'SvCopyMaterialSlotsNode'
    bl_label = 'Copy Material Slots (Objects)'
    bl_icon = 'MATERIAL'
    is_scene_dependent = True
    is_animation_dependent = True

    object_target_pointer: bpy.props.PointerProperty(
        name="Target Object",
        description = "Where to copy material slots",
        type=bpy.types.Object,
    )

    object_source_id : bpy.props.IntProperty(
        name = "Original Object Id",
        description = "Original Object Id of Material slots",
        default = 0,
        min = 0,
        update = updateNode)


    object_source_pointer: bpy.props.PointerProperty(
        name="Source Object",
        description = "Source Object of material slots",
        type=bpy.types.Object,
    )

    def sv_init(self, context):
        self.inputs.new('SvObjectSocket' , 'object_target_pointers' ).prop_name  = 'object_target_pointer'
        self.inputs.new('SvStringsSocket', 'object_source_ids'      ).prop_name  = 'object_source_id'
        self.inputs.new('SvObjectSocket' , 'object_source_pointers' ).prop_name  = 'object_source_pointer'

        self.inputs['object_target_pointers' ].label  = 'Objects'
        self.inputs['object_source_ids'      ].label  = 'Object Id of Objects with Materials'
        self.inputs['object_source_pointers' ].label  = 'Objects with Materials'
        
        self.outputs.new('SvObjectSocket', 'objects'                ).label = "Objects"

    def process(self):
        if not any(socket.is_linked for socket in self.inputs):
            return
        
        object_target_pointers  = self.inputs['object_target_pointers' ].sv_get(deepcopy=False, default=[self.object_target_pointer ])
        object_source_ids       = self.inputs['object_source_ids'      ].sv_get(deepcopy=False, default=[self.object_source_id      ])
        if self.inputs['object_source_ids'].is_linked==False:
            object_source_ids = [self.object_source_id] * len(object_target_pointers)
        object_source_pointers  = self.inputs['object_source_pointers' ].sv_get(deepcopy=False, default=[self.object_source_pointer ])

        if len(object_target_pointers)==0:
            pass
        else:
            if len(object_target_pointers)!=len(object_source_ids):
                raise Exception(f'Lengths of lists of Object Target and Objects Source Id are not equals ({len(object_target_pointers)}!={len(object_source_ids)})')
            else:
                for I, (object_target, object_source_id) in enumerate(zip(object_target_pointers, object_source_ids)):
                    if object_source_id<0 or object_source_id>len(object_source_pointers)-1:
                        raise Exception(f'No Object Source with [{object_source_id}] in [{I}]th elem of list Original Object Id')
                    object_target.data.materials.clear()
                    object_source = object_source_pointers[object_source_id]
                    for I in range(len(object_source.data.materials)):
                        object_target.data.materials.append(object_source.data.materials[I])
                        pass
                    pass
                pass
            pass
        pass

        self.outputs['objects'].sv_set(object_target_pointers)

classes = [SvCopyMaterialSlotsNode, ]
register, unregister = bpy.utils.register_classes_factory(classes)
