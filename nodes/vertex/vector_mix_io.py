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
from bpy.props import FloatProperty, EnumProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import dataCorrect
from sverchok.data_structure import updateNode

mode_options = [(n, n, '', idx) for idx, n in enumerate("XYZ")]

class SvVectorMixIO(bpy.types.Node, SverchCustomTreeNode):
    ''' Vectors out '''
    bl_idname = 'SvVectorMixIO'
    bl_label = 'Vector Mix I/O'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    selected_mode = EnumProperty(
        items=mode_options,
        description="offers....",
        default="X", update=updateNode
    )
    
    co_value = FloatProperty(
        default=0.0, update=updateNode
    )

    def sv_init(self, context):
        self.inputs.new('VerticesSocket', "Vectors")
        self.inputs.new('StringsSocket', "co replace").prop_name = 'co_value'
        self.outputs.new('VerticesSocket', "Vectors")

    def draw_buttons(self, context, layout):
        layout.prop(self, 'selected_mode', expand=True)

    def process(self):
        vectors_out = self.outputs[0]
        vectors_in, co_replace_in = self.inputs

        if not all(vectors_out.is_linked, vectors_in.is_linked):
            return
        
        xyz = vectors_in.sv_get()
        co_replace = co_replace_in.sv_get()
        index = ['XYZ'].find(self.selected_mode)

        series_vec = []
        # data = dataCorrect(xyz)
        # X, Y, Z = [], [], []
        # for obj in data:
        #     x_, y_, z_ = (list(x) for x in zip(*obj))
        #     X.append(x_)
        #     Y.append(y_)
        #     Z.append(z_)

        self.outputs['Vectors'].sv_set(series_vec)                    

    # def process2(self):

    #     max_obj = max(map(len, (X_, Y_, Z_)))
    #     fullList(X_, max_obj)
    #     fullList(Y_, max_obj)
    #     fullList(Z_, max_obj)
    #     for i in range(max_obj):

    #         max_v = max(map(len, (X_[i], Y_[i], Z_[i])))
    #         fullList(X_[i], max_v)
    #         fullList(Y_[i], max_v)
    #         fullList(Z_[i], max_v)
    #         series_vec.append(list(zip(X_[i], Y_[i], Z_[i])))



def register():
    bpy.utils.register_class(SvVectorMixIO)


def unregister():
    bpy.utils.unregister_class(SvVectorMixIO)
