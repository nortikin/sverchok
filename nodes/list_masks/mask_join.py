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

from itertools import cycle
import bpy
from bpy.props import BoolProperty, IntProperty, StringProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import changable_sockets, updateNode, list_match_modes, list_match_func


class SvMaskJoinNodeMK2(SverchCustomTreeNode, bpy.types.Node):
    '''Mix two data list together by mask:
    mask: [1,0,0,1,1], data True: [10,11,12], data False: [20,21] => [10,20,21,11,12]
    '''
    bl_idname = 'SvMaskJoinNodeMK2'
    bl_label = 'List Mask Join (In)'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_MASK_JOIN'

    level: IntProperty(name="Level", default=1, min=1, update=updateNode)
    choice: BoolProperty(name="Choice", default=False, update=updateNode)
    typ: StringProperty(name='typ', default='')
    newsock: BoolProperty(name='newsock', default=False)
    
    list_match_global : EnumProperty(
    name="Match Global",
    description="Behavior on different list lengths, multiple objects level",
    items=list_match_modes, default="REPEAT",
    update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', 'Mask')
        self.inputs.new('SvStringsSocket', 'Data True')
        self.inputs.new('SvStringsSocket', 'Data False')
        self.outputs.new('SvStringsSocket', 'Data')

    def draw_buttons(self, context, layout):
        layout.prop(self, 'level')
        layout.prop(self, 'choice')
        
    def draw_buttons_ext(self, context, layout):
        '''draw buttons on the N-panel'''
        layout.label(text="List Match:")
        layout.prop(self, "list_match_global", text="Global Match", expand=False)

    def rclick_menu(self, context, layout):
        '''right click sv_menu items'''
        layout.prop_menu_enum(self, "list_match_global", text="List Match Global")
    
    def sv_update(self):
        inputsocketname = 'Data True'
        outputsocketname = ['Data']
        changable_sockets(self, inputsocketname, outputsocketname)

    def process(self):
        Ouso = self.outputs[0]
        if Ouso.is_linked:
            mask = self.inputs['Mask'].sv_get([[1, 0]])
            data_t = self.inputs['Data True'].sv_get()
            data_f = self.inputs['Data False'].sv_get()

            data_out = self.get_level(mask, data_t, data_f, self.level-1)

            Ouso.sv_set(data_out)

    def apply_choice_mask(self, mask, data_t, data_f):
        out = []
        if len(data_t) == 0:
            data_t = [None] * len(data_f)
        elif len(data_f) == 0:
            data_f = [None] * len(data_t)
            
        param = list_match_func[self.list_match_global]([mask, data_t, data_f])      
        for m, t, f in zip(*param):
            if m:
                out.append(t)
            else:
                out.append(f)
        return out

    def apply_mask(self, mask, data_t, data_f):
        ind_t, ind_f = 0, 0
        out = []
        for m in cycle(mask):
            if m:
                if ind_t == len(data_t):
                    return out
                out.append(data_t[ind_t])
                ind_t += 1
            else:
                if ind_f == len(data_f):
                    return out
                out.append(data_f[ind_f])
                ind_f += 1
        return out

    def get_level(self, mask, data_t, data_f, level):
        if self.choice:
            apply_mask = self.apply_choice_mask
        else:
            apply_mask = self.apply_mask
            
        if level == 1:
            out = []
            param = list_match_func[self.list_match_global]([mask, data_t, data_f])
            if not all((isinstance(p, (list, tuple)) for p in param)):
                return

            for m, t, f in zip(*param):
                out.append(apply_mask(m, t, f))
            return out
        elif level >= 2:
            out = []
            param = list_match_func[self.list_match_global]([data_t, data_f])
            for t, f in zip(*param):
                out.append(self.get_level(mask, t, f, level - 1))
            return out
        else:
            return apply_mask(mask[0], data_t, data_f)


def register():
    bpy.utils.register_class(SvMaskJoinNodeMK2)


def unregister():
    bpy.utils.unregister_class(SvMaskJoinNodeMK2)
