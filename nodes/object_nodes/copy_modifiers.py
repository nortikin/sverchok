# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE
from operator import attrgetter

import bpy
from sverchok.data_structure import repeat_last

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.handle_blender_data import BlModifier


class SvCopyModifiersNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: modifiers
    Tooltip:
    """
    bl_idname = 'SvCopyModifiersNode'
    bl_label = 'Copy Modifiers'
    bl_icon = 'MODIFIER_DATA'

    @property
    def is_scene_dependent(self):
        return self.inputs['Object To'].is_linked \
               or self.inputs['Object To'].object_ref_pointer

    @property
    def is_animation_dependent(self):
        return self.inputs['Object To'].is_linked \
               or self.inputs['Object To'].object_ref_pointer

    def sv_init(self, context):
        self.inputs.new('SvObjectSocket', 'Object To')
        self.inputs.new('SvObjectSocket', 'Object From')
        self.outputs.new('SvObjectSocket', 'Object')

    def process(self):
        obj_to = self.inputs['Object To'].sv_get(deepcopy=False, default=[])
        obj_from = self.inputs['Object From'].sv_get(deepcopy=False, default=[])

        for to, _from in zip(obj_to, repeat_last(obj_from)):

            # test changes, should prevent from useless mesh reevaluations presumably
            is_valid = True
            for mod_from in _from.modifiers:
                if mod_from.name not in to.modifiers:
                    is_valid = False
                    break
                mod_to = to.modifiers[mod_from.name]
                if BlModifier(mod_to) != BlModifier(mod_from):
                    is_valid = False
                    break
            else:
                if len(to.modifiers) != len(_from.modifiers):
                    is_valid = False

            # reapply modifiers
            if not is_valid:
                to.modifiers.clear()
                for mod_from in _from.modifiers:
                    mod_to = to.modifiers.new(mod_from.name, mod_from.type)

                    # apply modifier properties
                    for prop in (p for p in mod_from.bl_rna.properties if not p.is_readonly):
                        setattr(mod_to, prop.identifier, getattr(mod_from, prop.identifier))
                    if mod_from.type == 'NODES' and mod_from.node_group:
                        for tree_inp in mod_from.node_group.inputs[1:]:
                            prop_name = tree_inp.identifier
                            mod_to[prop_name] = mod_from[prop_name]
                            mod_to[f"{prop_name}_use_attribute"] = mod_from[f"{prop_name}_use_attribute"]
                            mod_to[f"{prop_name}_attribute_name"] = mod_from[f"{prop_name}_attribute_name"]
                        for tree_out in mod_from.node_group.outputs[1:]:
                            prop_name = tree_out.identifier
                            mod_to[f"{prop_name}_attribute_name"] = mod_from[f"{prop_name}_attribute_name"]

        self.outputs['Object'].sv_set(obj_to)


register, unregister = bpy.utils.register_classes_factory([SvCopyModifiersNode])
