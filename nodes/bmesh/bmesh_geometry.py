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

import bpy,bmesh,mathutils
from bpy.props import EnumProperty, FloatProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode, enum_item as e, second_as_first_cycle as safc,match_long_repeat)

dict_bmesh = {"intersect_face_point": ['Tests if the projection of a point is inside a face (using the face’s normal).',['face', 'point'],['None','(0,0,0)'],['Tests if the projection of a point is inside a face (using the face’s normal).','Tests if the projection of a point is inside a face (using the face’s normal).'],'Returns True when the projection of the point is in the face.Return type bool']}

operators = []
for i,ops in enumerate(dict_bmesh.keys()):
    operators.append((ops,ops+'()',dict_bmesh[ops][0],i))

class SvBMGeometryNode(SverchCustomTreeNode, bpy.types.Node):
    '''This module provides access to bmesh geometry evaluation functions.'''
    bl_idname = 'SvBMGeometryNode'
    bl_label = 'BMesh Geometry'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_ALPHA'  # 'SV_BMESH_OPS'
    def updata_oper(self,context):
        for key in self.inputs.keys():
            self.safe_socket_remove('inputs',key)
        
        for i,p in enumerate(dict_bmesh[self.oper][1]):
            des = dict_bmesh[self.oper][3][i]
            self.inputs.new('SvStringsSocket',p).description = des
        self.outputs['return'].description = dict_bmesh[self.oper][-1]
        updateNode(self,context)

    oper: EnumProperty(
        name='Operators',
        description = 'Operators for handling bmesh geometry evaluation functions',
        default=operators[0][0],
        items=operators,
        update=updata_oper)
    
    def draw_buttons(self, context, layout):
        layout.prop(self,'oper',text='')

    def sv_init(self, context):
        for i,p in enumerate(dict_bmesh[operators[0][0]][1]):
            des = dict_bmesh[operators[0][0]][3][i]
            self.inputs.new('SvStringsSocket',p).description = des
        self.outputs.new('SvStringsSocket','return').description = dict_bmesh[self.oper][-1]
    def process(self):
        input = []
        for i,p in enumerate(dict_bmesh[self.oper][1]):
            default = dict_bmesh[self.oper][2][i]
            value = self.inputs[p].sv_get(default=[[default]])
            input.append(value)
        input = match_long_repeat(input)

        return_ = []
        for pars in zip(*input):
            pars = match_long_repeat(pars)
            result = []
            for p in zip(*pars):
                for i in range(len(p)):
                    if self.inputs[i].is_linked :
                        name_p = dict_bmesh[self.oper][1][i]
                        exec(name_p + '= p[i]')
                        exec(name_p + '= p[i]')
                    else :
                        name_p = p[i]
                    if i == 0:
                        parameters = name_p
                    else:
                        parameters = parameters + ',' + name_p
                fun = 'bmesh.geometry.' + self.oper + '(' + parameters +')'
                try :
                    result.append(eval(fun))
                except (TypeError) as Argument:
                    print(Argument)
            return_.append(result)
        
        self.outputs['return'].sv_set(return_)


def register():
    bpy.utils.register_class(SvBMGeometryNode)


def unregister():
    bpy.utils.unregister_class(SvBMGeometryNode)
