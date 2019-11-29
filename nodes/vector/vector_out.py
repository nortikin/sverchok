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
from bpy.props import BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import dataCorrect_np, updateNode
from numpy import ndarray, array

def unpack_np(obj):
    return (obj[:, 0], obj[:, 1], obj[:, 2])

def unpack_list(obj):
    return (list(x) for x in zip(*obj))

def unpack_list_to_np(obj):
    return (array(x) for x in zip(*obj))

class VectorsOutNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Vectors out '''
    bl_idname = 'VectorsOutNode'
    bl_label = 'Vector out'
    sv_icon = 'SV_VECTOR_OUT'
    output_numpy: BoolProperty(
        name='Output NumPy',
        description='Output NumPy arrays',
        default=False, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vectors")
        self.outputs.new('SvStringsSocket', "X")
        self.outputs.new('SvStringsSocket', "Y")
        self.outputs.new('SvStringsSocket', "Z")
    def draw_buttons_ext(self, ctx, layout):
        layout.prop(self, "output_numpy", toggle=False)

    def rclick_menu(self, context, layout):
        layout.prop(self, "output_numpy", toggle=True)

    def process(self):
        if self.inputs['Vectors'].is_linked:
            xyz = self.inputs['Vectors'].sv_get(deepcopy=False)

            data = dataCorrect_np(xyz)
            X, Y, Z = [], [], []
            if self.output_numpy:
                unpack_func = unpack_np if isinstance(data[0], ndarray) else unpack_list_to_np
            else:
                unpack_func = unpack_list
            for obj in data:
                x_, y_, z_ = unpack_func(obj)
                X.append(x_)
                Y.append(y_)
                Z.append(z_)
            for i, name in enumerate(['X', 'Y', 'Z']):
                if self.outputs[name].is_linked:
                    self.outputs[name].sv_set([X, Y, Z][i])


def register():
    bpy.utils.register_class(VectorsOutNode)


def unregister():
    bpy.utils.unregister_class(VectorsOutNode)
