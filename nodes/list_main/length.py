# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import itertools

import bpy
from bpy.props import IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode


class ListLengthNode(bpy.types.Node, SverchCustomTreeNode):
    ''' List Length '''
    bl_idname = 'ListLengthNode'
    bl_label = 'List Length'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_LIST_LEN'

    level: IntProperty(name='level_to_count', default=1, min=0, update=updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, "level", text="level")

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "Data")
        self.outputs.new('SvStringsSocket', "Length")

    def process(self):

        if 'Length' in self.outputs and self.outputs['Length'].is_linked:
            if 'Data' in self.inputs and self.inputs['Data'].is_linked:
                data = self.inputs['Data'].sv_get(deepcopy=False)

                if not self.level:
                    out = [[len(data)]]
                elif self.level == 1:
                    out = [self.count(data, self.level)]
                else:
                    out = self.count(data, self.level)

                self.outputs['Length'].sv_set(out)

    def count(self, data, level):
        if isinstance(data, (float, int)):
            return 1
        if level == 1:
            return [self.count(obj, level-1) for obj in data]
        elif level == 2:
            out = [self.count(obj, level-1) for obj in data]
            return out
        elif level > 2:  # flatten all but last level, we should preserve more detail than this
            out = [self.count(obj, level-1) for obj in data]
            return [list(itertools.chain.from_iterable(obj)) for obj in out]
        else:
            return len(data)

    def draw_label(self):
        if self.hide:
            return f"{self.name} Lv={self.level}" 
        return self.label or self.name

def register():
    bpy.utils.register_class(ListLengthNode)


def unregister():
    bpy.utils.unregister_class(ListLengthNode)
