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
from bpy.props import IntProperty, FloatProperty
import numpy as np
from node_tree import SverchCustomTreeNode
from data_structure import updateNode, SvSetSocketAnyType, SvGetSocketAnyType


class Hilbert3dNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Hilbert3d line '''
    bl_idname = 'Hilbert3dNode'
    bl_label = 'Hilbert3d'
    bl_icon = 'OUTLINER_OB_EMPTY'

    level_ = IntProperty(name='level', description='Level',
                         default=2, min=1, max=5,
                         options={'ANIMATABLE'}, update=updateNode)
    size_ = FloatProperty(name='size', description='Size',
                          default=1.0, min=0.1,
                          options={'ANIMATABLE'}, update=updateNode)

    def init(self, context):
        self.inputs.new('StringsSocket', "Level", "Level").prop_name = 'level_'
        self.inputs.new('StringsSocket', "Size", "Size").prop_name = 'size_'
        self.outputs.new('VerticesSocket', "Vertices", "Vertices")
        self.outputs.new('StringsSocket', "Edges", "Edges")

    def draw_buttons(self, context, layout):
        pass

    def update(self):

        if not ('Edges' in self.outputs):
            return

        # inputs
        if self.outputs['Edges'].links or self.outputs['Vertices'].links:
            if self.inputs['Level'].links:
                Integer = int(SvGetSocketAnyType(self, self.inputs['Level'])[0][0])
            else:
                Integer = self.level_

            if self.inputs['Size'].links:
                Step = SvGetSocketAnyType(self, self.inputs['Size'])[0][0]
            else:
                Step = self.size_

        # outputs
        if self.outputs['Vertices'].links:
            verts = self.hilbert(Step, Integer)
            SvSetSocketAnyType(self, 'Vertices', verts)

        if self.outputs['Edges'].links:
            listEdg = []
            r = len(verts[0])-1
            for i in range(r):
                listEdg.append((i, i+1))

            edg = list(listEdg)
            SvSetSocketAnyType(self, 'Edges', [edg])

    def hilbert(self, step, n):

        def hilbert3(n):
            if (n <= 0):
                x, y, z = 0, 0, 0
            else:
                [xo, yo, zo] = hilbert3(n-1)
                x = step * .5 * np.array([.5+zo, .5+yo, -.5+yo, -.5-xo, -.5-xo, -.5-yo, .5-yo, .5+zo])
                y = step * .5 * np.array([.5+xo, .5+zo, .5+zo, .5+yo, -.5+yo, -.5-zo, -.5-zo, -.5-xo])
                z = step * .5 * np.array([.5+yo, -.5+xo, -.5+xo, .5-zo, .5-zo, -.5+xo, -.5+xo, .5-yo])
            return [x, y, z]

        vx, vy, vz = hilbert3(n)
        vx = vx.flatten().tolist()
        vy = vy.flatten().tolist()
        vz = vz.flatten().tolist()
        verts = [list(zip(vx, vy, vz))]
        return verts

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(Hilbert3dNode)


def unregister():
    bpy.utils.unregister_class(Hilbert3dNode)

if __name__  == '__main__':
    register()

