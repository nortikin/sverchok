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

from node_tree import SverchCustomTreeNode
from data_structure import sv_Vars, updateNode, SvSetSocketAnyType

# Warning, changing this node without modifying the update system might break functionlaity
# bl_idname and var_name is used by the update system


class WifiOutNode(bpy.types.Node, SverchCustomTreeNode):
    ''' WifiOutNode '''
    bl_idname = 'WifiOutNode'
    bl_label = 'Wifi output'
    bl_icon = 'OUTLINER_OB_EMPTY'

    var_name = StringProperty(name='var_name',
                              default='a',
                              update=updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, "var_name", text="var name")

    def init(self, context):
        self.outputs.new('StringsSocket', "a[0]", "a[0]")

    def update(self):
        global sv_Vars
        # outputs
        var_name = self.var_name
        list_vars = []
        if var_name in sv_Vars.keys():
            dest = []
            for v in sv_Vars.keys():
                fs = v.find('sv_typ'+var_name)
                if fs >= 0:
                    iv = v.find('[')
                    sv = int(v[iv+1:-1])
                    # dest - (index, typ)
                    dest.append((sv, sv_Vars[v]))
                    dest.sort()

            lsvn = len(var_name)
            if len(self.outputs) > 0 and \
               self.var_name != self.outputs[self.outputs.keys()[0]].name[:lsvn]:
                    self.outputs.clear()
                    self.outputs.new('StringsSocket', str(var_name)+"[0]", str(var_name)+"[0]")

            # без цветовой дифференциации штанов цивилизация обречена (c)
            flag_links = False
            for fl in self.outputs:
                if fl.links:
                    flag_links = True

            if flag_links:
                self.use_custom_color = True
                self.color = (0.4, 0, 0.8)
            else:
                self.use_custom_color = True
                self.color = (0.05, 0, 0.2)

            if dest:
                dic_typ = {'s': 'StringsSocket', 'v': 'VerticesSocket', 'm': 'MatrixSocket'}
                for i, dst in enumerate(dest):
                    if dst[0] > len(sv_Vars[var_name])-1:
                        break
                    typ = dst[1]
                    var = sv_Vars[var_name][dst[0]]
                    flag = True
                    flag2 = True
                    while(flag):
                        flag = False
                        louts = len(self.outputs)
                        a_name = var_name + '['+str(dst[0])+']'
                        if dst[0] == louts:
                            self.outputs.new(dic_typ[typ], a_name, a_name)
                            SvSetSocketAnyType(self, a_name, var)
                        else:
                            if a_name in self.outputs and louts <= len(sv_Vars[var_name]) and \
                                str(type(self.outputs[a_name]))[15:-2] == dic_typ[typ]:
                                SvSetSocketAnyType(self, a_name, var)

                            elif flag2:
                                flag2 = False
                                flag = True
                                if louts > len(sv_Vars[var_name]):
                                    flag2 = True

                                cl = min(louts-1, len(sv_Vars[var_name])-1)
                                for c in self.outputs[cl:]:
                                    self.outputs.remove(c)
        else:
            if len(sv_Vars) > 0:
                self.outputs.clear()
                self.outputs.new('StringsSocket', str(var_name)+"[0]", str(var_name)+"[0]")


def register():
    bpy.utils.register_class(WifiOutNode)


def unregister():
    bpy.utils.unregister_class(WifiOutNode)
