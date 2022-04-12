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
from sverchok.utils.nodes_mixins.sv_animatable_nodes import SvAnimatableNode


class SvCopyModifiersNode(SvAnimatableNode, SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: modifiers
    Tooltip:
    """
    bl_idname = 'SvCopyModifiersNode'
    bl_label = 'Copy Modifiers'
    bl_icon = 'MODIFIER_DATA'

    def sv_init(self, context):
        self.inputs.new('SvObjectSocket', 'Object To')
        self.inputs.new('SvObjectSocket', 'Object From')
        self.outputs.new('SvObjectSocket', 'Object')

    def draw_buttons(self, context, layout):
        self.draw_animatable_buttons(layout)

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
                for prop in (p for p in mod_from.bl_rna.properties if not p.is_readonly):
                    if getattr(mod_to, prop.identifier) != getattr(mod_from, prop.identifier):
                        is_valid = False
                        break
            else:
                if len(to.modifiers) != len(_from.modifiers):
                    is_valid = False

            # reapply modifiers
            if not is_valid:
                to.modifiers.clear()
                for mod_from in _from.modifiers:
                    new_mod = to.modifiers.new(mod_from.name, mod_from.type)
                    for prop in (p for p in mod_from.bl_rna.properties if not p.is_readonly):
                        setattr(new_mod, prop.identifier, getattr(mod_from, prop.identifier))

        self.outputs['Object'].sv_set(obj_to)


register, unregister = bpy.utils.register_classes_factory([SvCopyModifiersNode])
