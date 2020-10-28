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
from bpy.props import BoolProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import dataCorrect_np, updateNode, levels_of_list_or_np
from numpy import ndarray, array

def unpack_np(obj):
    return (obj[:, 0], obj[:, 1], obj[:, 2])


def unpack_list(obj):
    return (list(x) for x in zip(*obj))


def unpack_list_to_np(obj):
    return (array(x) for x in zip(*obj))


def unpack(data, output_numpy):
    X, Y, Z = [], [], []
    if output_numpy:
        unpack_func = unpack_np if isinstance(data[0], ndarray) else unpack_list_to_np
    else:
        unpack_func = unpack_list
    for obj in data:
        print(obj)
        x_, y_, z_ = unpack_func(obj)
        X.append(x_)
        Y.append(y_)
        Z.append(z_)
    return X, Y, Z


def unpack_multilevel(data, level, output_numpy):
    if level > 3:
        X, Y, Z = [], [], []
        for obj in data:

            x,y,z = unpack_multilevel(obj, level-1, output_numpy)
            X.append(x)
            Y.append(y)
            Z.append(z)
    elif level < 3:
        X, Y, Z = unpack_multilevel([data], level+1, output_numpy)
    else:
        X,Y,Z = unpack(data, output_numpy)

    return X,Y,Z


class VectorsOutNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Separate XYZ
    Tooltip:  Split X, Y and Z components from vector.
    """
    bl_idname = 'VectorsOutNode'
    bl_label = 'Vector out'
    sv_icon = 'SV_VECTOR_OUT'

    output_numpy: BoolProperty(
        name='Output NumPy',
        description='Output NumPy arrays',
        default=False, update=updateNode)
    correct_output_modes = [
        ('NONE', 'None', 'Leave at multi-object level (Advanced)', 0),
        ('FLAT', 'Flat Output', 'Flat to object level', 2),
    ]
    correct_output: EnumProperty(
        name="Simplify Output",
        description="Behavior on different list lengths, object level",
        items=correct_output_modes, default="FLAT",
        update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vectors")
        self.outputs.new('SvStringsSocket', "X")
        self.outputs.new('SvStringsSocket', "Y")
        self.outputs.new('SvStringsSocket', "Z")
        self.width = 100

    def draw_buttons_ext(self, ctx, layout):
        layout.prop(self, "output_numpy", toggle=False)
        layout.prop(self, "correct_output")

    def rclick_menu(self, context, layout):
        layout.prop(self, "output_numpy", toggle=True)
        layout.prop_menu_enum(self, 'correct_output')

    def process(self):
        if not (self.inputs['Vectors'].is_linked and any(s.is_linked for s in self.outputs)):
            return

        vectors = self.inputs['Vectors'].sv_get(deepcopy=False)

        if self.correct_output == 'FLAT':
            data = dataCorrect_np(vectors)
            xyz = unpack(data, self.output_numpy)
        else:
            input_level = levels_of_list_or_np(vectors)
            xyz = unpack_multilevel(vectors, input_level, self.output_numpy)

        for i, name in enumerate(['X', 'Y', 'Z']):
            if self.outputs[name].is_linked:
                self.outputs[name].sv_set(xyz[i])


def register():
    bpy.utils.register_class(VectorsOutNode)


def unregister():
    bpy.utils.unregister_class(VectorsOutNode)
