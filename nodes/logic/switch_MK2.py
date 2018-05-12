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
from bpy.props import IntProperty, EnumProperty, BoolProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import get_other_socket, updateNode, replace_socket, match_long_repeat

SPECIAL_SOCKETS = ['MatrixSocket', 'SvObjectSocket']

def get_bool(soc):
    #convert string type to bool
            
    state = soc.sv_get()[0][0]
    vars = {'True':[True], 'False':[False], 'None':[]}
    return [vars[state]]

def check_data_in(soc):
    #puts data in nested list if necessary
            
    if type(soc.sv_get()[0]) == list:
        return soc.sv_get()
    elif get_other_socket(soc).bl_idname in SPECIAL_SOCKETS:
        return [soc.sv_get()]
    else:
        print('Switch mk2 node did not expect such type of input socket')

class SvSwitchNodeMK2(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Switch MK2
    Tooltip: This version is more clever of previous one
    
    You can deal with empty data connected to input sockets (True or False)
    """
    bl_idname = 'SvSwitchNodeMK2'
    bl_label = 'Switch mk2'
    bl_icon = 'ACTION_TWEAK'
    
    input_items = [
            ("True", "True", "", 0),
            ("False", "False", "", 1),
            ("None", "None", "", 2)
        ]
    
    def change_sockets(self, context):
        pre_num = len(self.inputs)//2
        diff = self.socket_number - pre_num
        if diff > 0:
            for i in range(diff):
                num = pre_num + i
                name_A = 'A_{}'.format(num)
                name_B = 'B_{}'.format(num)
            
                self.inputs.new("StringsSocket", name_A).prop_name = name_A
                self.inputs.new("StringsSocket", name_B).prop_name = name_B
                self.outputs.new("StringsSocket", "Out_{}".format(num))
            
        elif diff < 0:
            for i in range(abs(diff)):
                self.inputs.remove(self.inputs[-1])
                self.inputs.remove(self.inputs[-1])
                self.outputs.remove(self.outputs[-1])

    switch_state  = EnumProperty(items=input_items[:2], name="state", default="False", update=updateNode)
    socket_number = IntProperty(name="count", min=1, max=10, default=1, update=change_sockets)
    flatten_list  = BoolProperty(name='Flatten list', description='for matrixes and objects only',
                                 default=False, update=updateNode)
        
    for i in range(10):
        name_A = 'A_{}'.format(i)
        name_B = 'B_{}'.format(i)
        locals()[name_A] = EnumProperty(items=input_items, name=name_A, default="True", update=updateNode)
        locals()[name_B] = EnumProperty(items=input_items, name=name_B, default="False", update=updateNode)
    
    def sv_init(self, context):        
        self.inputs.new("StringsSocket", "State").prop_name = 'switch_state'
        self.inputs.new("StringsSocket", "A_0").prop_name   = 'A_0'
        self.inputs.new("StringsSocket", "B_0").prop_name   = 'B_0'
        self.outputs.new("StringsSocket", "Out_0")
    
    def draw_buttons_ext(self, context, layout):
        layout.prop(self, 'socket_number', text="in/out number")
        layout.prop(self, 'flatten_list')
        
    def rclick_menu(self, context, layout):
        layout.prop(self, 'socket_number', text="in/out number")
        layout.prop(self, 'flatten_list')
    
    def update(self):
        inputs_A = [i for i in self.inputs if i.name[0] == 'A']
        for in_soc, out_soc in zip(inputs_A, self.outputs):
            
            if not in_soc.links:
                new_type = in_soc.bl_idname
            else:
                in_other = get_other_socket(in_soc)
                new_type = in_other.bl_idname
                
            if new_type == out_soc.bl_idname:
                continue
            
            replace_socket(out_soc, new_type)
            
    def check_data_out(self, data, i_soc):
        #Flatten list if necessary
            
        if self.flatten_list and self.outputs[i_soc].bl_idname in SPECIAL_SOCKETS:
            return [n2 for n1 in data for n2 in n1]
        else:
            return data
        
    def process(self):
        
        state_lists = self.inputs[0].sv_get() if self.inputs[0].is_linked else get_bool(self.inputs[0])
        count = self.socket_number
        data_a = [check_data_in(soc) if soc.is_linked else get_bool(soc)
                  for soc in self.inputs[1:] if soc.name[0] == 'A']
        data_b = [check_data_in(soc) if soc.is_linked else get_bool(soc)
                  for soc in self.inputs[1:] if soc.name[0] == 'B']
        
        #iteration of additional socket
        for i_soc,(state_lists,A,B) in enumerate(zip(*[[state_lists]*count,data_a,data_b])):
            data = []
            for params in zip(*match_long_repeat([state_lists, A, B])):
                S_obj, A_obj, B_obj = params
                
                A_empty = len(A_obj) == 0
                B_empty = len(B_obj) == 0
                
                if A_empty and B_empty:
                    data.append([])
                
                elif A_empty:
                    data.append([b for state, b in zip(*match_long_repeat([S_obj,B_obj])) if not bool(state)])
                    
                elif B_empty:
                    data.append([a for state, a in zip(*match_long_repeat([S_obj,A_obj])) if bool(state)])
                
                else:    
                    data.append([[a, b][[1,0][bool(state)]] for state, a, b in zip(*match_long_repeat(params))])
                    
            self.outputs[i_soc].sv_set(self.check_data_out(data,i_soc))
            
        
def register():
    bpy.utils.register_class(SvSwitchNodeMK2)

def unregister():
    bpy.utils.unregister_class(SvSwitchNodeMK2)
