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
from bpy.props import StringProperty

from node_tree import (SverchCustomTreeNode, MatrixSocket,
                       StringsSocket, VerticesSocket)
from data_structure import sv_Vars, updateNode, SvGetSocketAnyType

# Warning, changing this node without modifying the update system might break functionlaity
# bl_idname and var_name is used by the update system


class WifiInNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Wifi Input '''
    bl_idname = 'WifiInNode'
    bl_label = 'Wifi input'
    bl_icon = 'OUTLINER_OB_EMPTY'

    var_name = StringProperty(name='var_name',
                              default='a',
                              update=updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, "var_name", text="var name")

    def init(self, context):
        var_name = self.var_name
        self.inputs.new('StringsSocket', var_name+"[0]", var_name+"[0]")

    def check_slots(self, num):
        l = []
        if len(self.inputs) <= num:
            return False
        for i, sl in enumerate(self.inputs[num:]):
            if len(sl.links) == 0:
                l.append(i+num)
        if l:
            return l
        else:
            return False

    def update(self):
        global sv_Vars
        # inputs
        var_name = self.var_name
        ch = self.check_slots(0)
        if ch:
            for c in ch[:-1]:
                self.inputs.remove(self.inputs[ch[-1]])

        list_mult = []
        for idx, multi in enumerate(self.inputs):
            if multi.links:
                ch = self.check_slots(1)
                if not ch:
                    a_name = var_name + '['+str(len(self.inputs))+']'
                    self.inputs.new('StringsSocket', a_name, a_name)

        flag_links = False
        for fl in self.inputs:
            if fl.links:
                flag_links = True

        if flag_links:
            self.use_custom_color = True
            self.color = (0.4, 0, 0.8)
        else:
            self.use_custom_color = True
            self.color = (0.05, 0, 0.2)

        list_vars = []
        for idx, multi in enumerate(self.inputs):
            a_name = var_name + '['+str(idx)+']'
            typ = 's'
            if multi.links:
                if type(multi.links[0].from_socket) == StringsSocket:
                    try:
                        mult = SvGetSocketAnyType(self, multi)
                    except:
                        print('no data in wifi: '+a_name)
                        mult = [[None]]
                    typ = 's'
                elif type(multi.links[0].from_socket) == VerticesSocket:
                    try:
                        mult = SvGetSocketAnyType(self, multi)
                    except:
                        print('no data in wifi: '+a_name)
                        mult = [[None]]
                    typ = 'v'
                elif type(multi.links[0].from_socket) == MatrixSocket:
                    try:
                        mult = SvGetSocketAnyType(self, multi)
                    except:
                        print('no data in wifi: '+a_name)
                        mult = [[None]]
                    typ = 'm'

            else:
                mult = [[None]]

            list_vars.append(mult)
            multi.name = a_name
            sv_Vars['sv_typ'+var_name+a_name] = typ

        sv_Vars[var_name] = list_vars


def register():
    bpy.utils.register_class(WifiInNode)


def unregister():
    bpy.utils.unregister_class(WifiInNode)
