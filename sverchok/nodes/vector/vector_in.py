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
from bpy.props import FloatProperty
from node_tree import SverchCustomTreeNode, StringsSocket
from data_structure import (updateNode, fullList,
                            SvSetSocketAnyType, SvGetSocketAnyType)


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

    def init(self, context):
        self.inputs.new('StringsSocket', "X").prop_name = 'x_'
        self.inputs.new('StringsSocket', "Y").prop_name = 'y_'
        self.inputs.new('StringsSocket', "Z").prop_name = 'z_'
        self.width = 100
        self.outputs.new('VerticesSocket', "Vectors", "Vectors")

    def update(self):
        # inputs
        if 'X' in self.inputs and self.inputs['X'].links and \
           type(self.inputs['X'].links[0].from_socket) == StringsSocket:
            X_ = SvGetSocketAnyType(self, self.inputs['X'])
        else:
            X_ = [[self.x_]]

        if 'Y' in self.inputs and self.inputs['Y'].links and \
           type(self.inputs['Y'].links[0].from_socket) == StringsSocket:
            Y_ = SvGetSocketAnyType(self, self.inputs['Y'])
        else:
            Y_ = [[self.y_]]

        if 'Z' in self.inputs and self.inputs['Z'].links and \
           type(self.inputs['Z'].links[0].from_socket) == StringsSocket:
            Z_ = SvGetSocketAnyType(self, self.inputs['Z'])
        else:
            Z_ = [[self.z_]]

        # outputs
        if 'Vectors' in self.outputs and self.outputs['Vectors'].links:

            max_obj = max(len(X_), len(Y_), len(Z_))
            self.fullList(X_, max_obj)
            self.fullList(Y_, max_obj)
            self.fullList(Z_, max_obj)

            series_vec = []
            for i in range(max_obj):
                X = X_[i]
                Y = Y_[i]
                Z = Z_[i]

                max_num = max(len(X), len(Y), len(Z))

                fullList(X, max_num)
                fullList(Y, max_num)
                fullList(Z, max_num)

                series_vec.append(list(zip(X, Y, Z)))

            SvSetSocketAnyType(self, 'Vectors', series_vec)
            #print (series_vec)

    def fullList(self, l, count):
        d = count - len(l)
        if d > 0:
            l.extend([l[-1] for a in range(d)])
        return

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(GenVectorsNode)


def unregister():
    bpy.utils.unregister_class(GenVectorsNode)
