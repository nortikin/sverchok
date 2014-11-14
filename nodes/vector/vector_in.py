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
from bpy.props import FloatProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode, StringsSocket
from sverchok.data_structure import updateNode, fullList, SvGetSocketAnyType, SvSetSocketAnyType
from sverchok.utils.sv_itertools import sv_zip_longest

class GenVectorsNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Generator vectors '''
    bl_idname = 'GenVectorsNode'
    bl_label = 'Vectors in'
    bl_icon = 'OUTLINER_OB_EMPTY'


    x_ = FloatProperty(name='X', description='X',
                       default=0.0, precision=3,
                       update=updateNode)
    y_ = FloatProperty(name='Y', description='Y',
                       default=0.0, precision=3,
                       update=updateNode)
    z_ = FloatProperty(name='Z', description='Z',
                       default=0.0, precision=3,
                       update=updateNode)

    def sv_init(self, context):
        self.inputs.new('StringsSocket', "X").prop_name = 'x_'
        self.inputs.new('StringsSocket', "Y").prop_name = 'y_'
        self.inputs.new('StringsSocket', "Z").prop_name = 'z_'
        self.width = 100
        self.outputs.new('VerticesSocket', "Vectors")
        
    
    def process(self):
        if not self.outputs['Vectors'].is_linked:
            return
        inputs = self.inputs
        X_ = inputs['X'].sv_get()
        Y_ = inputs['Y'].sv_get()
        Z_= inputs['Z'].sv_get()
        series_vec = []
        max_obj = max(map(len,(X_,Y_,Z_)))
        fullList(X_, max_obj)
        fullList(Y_, max_obj)
        fullList(Z_, max_obj)
        for i in range(max_obj):
                
            max_v = max(map(len,(X_[i],Y_[i],Z_[i])))
            fullList(X_[i], max_v)
            fullList(Y_[i], max_v)
            fullList(Z_[i], max_v)
            series_vec.append(list(zip(X_[i], Y_[i], Z_[i])))
        
        self.outputs['Vectors'].sv_set(series_vec)
    
    
def register():
    bpy.utils.register_class(GenVectorsNode)


def unregister():
    bpy.utils.unregister_class(GenVectorsNode)
