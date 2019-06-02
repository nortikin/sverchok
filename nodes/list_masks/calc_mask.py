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

import bpy
from bpy.props import BoolProperty, EnumProperty, IntProperty
from sverchok.node_tree import SverchCustomTreeNode, StringsSocket, VerticesSocket
from sverchok.data_structure import updateNode, match_long_repeat, fullList

class SvCalcMaskNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Calculate Mask
    Tooltip: Calculate mask from two sets of objects
    """
    bl_idname = 'SvCalcMaskNode'
    bl_label = 'Calculate Mask'
    bl_icon = 'OUTLINER_OB_EMPTY'

    level = IntProperty(name = 'Level',
                description = "List level to operate on",
                min = 0, default = 0, update=updateNode)
    
    negate = BoolProperty(name = 'Negate',
                description = 'Negate mask', update=updateNode)

    ignore_order = BoolProperty(name = 'Ignore order',
                    description = "Ignore items order while comparing lists",
                    default = True, update=updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'level')
        layout.prop(self, 'negate')
        layout.prop(self, 'ignore_order')

    def sv_init(self, context):
        self.inputs.new('StringsSocket', "Subset")
        self.inputs.new('StringsSocket', "Set")
        self.outputs.new('StringsSocket', 'Mask')

    def calc(self, subset_data, set_data, level):
        if level == 0:
            if not isinstance(subset_data, (tuple, list)):
                raise Exception("Specified level is too high for given Subset")
            if not isinstance(set_data, (tuple, list)):
                raise Exception("Specified level is too high for given Set")

            if self.ignore_order:
                if self.negate:
                    return [set(item) not in map(set, subset_data) for item in set_data]
                else:
                    return [set(item) in map(set, subset_data) for item in set_data]
            else:
                if self.negate:
                    return [item not in subset_data for item in set_data]
                else:
                    return [item in subset_data for item in set_data]
        else:
            sub_objects = match_long_repeat([subset_data, set_data])
            return [self.calc(subset_item, set_item, level - 1) for subset_item, set_item in zip(*sub_objects)]

    def process(self):

        if not any(output.is_linked for output in self.outputs):
            return

        subset_s = self.inputs['Subset'].sv_get(default=[[]])
        set_s = self.inputs['Set'].sv_get(default=[[]])
        out_masks = []

        objects = match_long_repeat([subset_s, set_s])
        for subset, set in zip(*objects):
            mask = self.calc(subset, set, self.level)
            out_masks.append(mask)

        self.outputs['Mask'].sv_set(out_masks)

def register():
    bpy.utils.register_class(SvCalcMaskNode)

def unregister():
    bpy.utils.unregister_class(SvCalcMaskNode)

