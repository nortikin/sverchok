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
from bpy.props import BoolProperty, IntProperty, FloatProperty

from node_tree import SverchCustomTreeNode
from data_structure import (updateNode, fullList, sv_zip,
                            SvSetSocketAnyType, SvGetSocketAnyType)


class PlaneNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Plane '''
    bl_idname = 'PlaneNode'
    bl_label = 'Plane'
    bl_icon = 'OUTLINER_OB_EMPTY'

    int_X = IntProperty(name='N Vert X', description='Nº Vertices X',
                        default=2, min=2,
                        options={'ANIMATABLE'}, update=updateNode)
    int_Y = IntProperty(name='N Vert Y', description='Nº Vertices Y',
                        default=2, min=2,
                        options={'ANIMATABLE'}, update=updateNode)
    step_X = FloatProperty(name='Step X', description='Step length X',
                           default=1.0, options={'ANIMATABLE'},
                           update=updateNode)
    step_Y = FloatProperty(name='Step Y', description='Step length Y',
                           default=1.0,
                           options={'ANIMATABLE'}, update=updateNode)
    Separate = BoolProperty(name='Separate', description='Separate UV coords',
                            default=False,
                            update=updateNode)

    def init(self, context):
        self.inputs.new('StringsSocket', "Nº Vertices X").prop_name = 'int_X'
        self.inputs.new('StringsSocket', "Nº Vertices Y").prop_name = 'int_Y'
        self.inputs.new('StringsSocket', "Step X").prop_name = 'step_X'
        self.inputs.new('StringsSocket', "Step Y").prop_name = 'step_Y'
        self.outputs.new('VerticesSocket', "Vertices")
        self.outputs.new('StringsSocket', "Edges")
        self.outputs.new('StringsSocket', "Polygons")

    def draw_buttons(self, context, layout):
        layout.prop(self, "Separate", text="Separate")

    def update(self):
        # inputs
        if 'Nº Vertices X' in self.inputs and self.inputs['Nº Vertices X'].links:
            IntegerX = int(SvGetSocketAnyType(self, self.inputs['Nº Vertices X'])[0][0])
        else:
            IntegerX = self.int_X

        if 'Nº Vertices Y' in self.inputs and self.inputs['Nº Vertices Y'].links:
            IntegerY = int(SvGetSocketAnyType(self, self.inputs['Nº Vertices Y'])[0][0])
        else:
            IntegerY = self.int_Y

        if 'Step X' in self.inputs and self.inputs['Step X'].links:
            StepX = SvGetSocketAnyType(self, self.inputs['Step X'])[0]

            listVertX = []
            fullList(StepX, IntegerX)
            for i in range(IntegerY):
                listVertX.append(0.0)
                for j in range(IntegerX-1):
                    listVertX.append(listVertX[j]+StepX[j])

        else:
            StepX = self.step_X
            listVertX = []
            for i in range(IntegerY):
                for j in range(IntegerX):
                    listVertX.append(0.0+j)
            listVertX = [StepX*i for i in listVertX]

        if 'Step Y' in self.inputs and self.inputs['Step Y'].links:
            StepY = SvGetSocketAnyType(self, self.inputs['Step Y'])[0]

            listVertY = []
            fullList(StepY, IntegerY)
            for i in range(IntegerX):
                listVertY.append(0.0)
            for i in range(IntegerY-1):
                for j in range(IntegerX):
                    listVertY.append(listVertY[IntegerX*i]+StepY[i])
        else:
            StepY = self.step_Y
            listVertY = []
            for i in range(IntegerY):
                for j in range(IntegerX):
                    listVertY.append(0.0+i)
            listVertY = [StepY*i for i in listVertY]

        # outputs
        if 'Vertices' in self.outputs and self.outputs['Vertices'].links:

            X = listVertX
            Y = listVertY
            Z = [0.0]

            max_num = max(len(X), len(Y), len(Z))

            fullList(X, max_num)
            fullList(Y, max_num)
            fullList(Z, max_num)

            points = list(sv_zip(X, Y, Z))
            if self.Separate:
                out = []
                for y in range(IntegerY):
                    out_ = []
                    for x in range(IntegerX):
                        out_.append(points[IntegerX*y+x])
                    out.append(out_)
                SvSetSocketAnyType(self, 'Vertices', [out])
            else:
                SvSetSocketAnyType(self, 'Vertices', [points])

        if 'Edges' in self.outputs and self.outputs['Edges'].links:
            listEdg = []
            for i in range(IntegerY):
                for j in range(IntegerX-1):
                    listEdg.append((IntegerX*i+j, IntegerX*i+j+1))
            for i in range(IntegerX):
                for j in range(IntegerY-1):
                    listEdg.append((IntegerX*j+i, IntegerX*j+i+IntegerX))

            edg = list(listEdg)
            SvSetSocketAnyType(self, 'Edges', [edg])

        if 'Polygons' in self.outputs and self.outputs['Polygons'].links:
            listPlg = []
            for i in range(IntegerX-1):
                for j in range(IntegerY-1):
                    listPlg.append((IntegerX*j+i, IntegerX*j+i+1, IntegerX*j+i+IntegerX+1, IntegerX*j+i+IntegerX))
            plg = list(listPlg)
            SvSetSocketAnyType(self, 'Polygons', [plg])

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(PlaneNode)


def unregister():
    bpy.utils.unregister_class(PlaneNode)
