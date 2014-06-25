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

from node_tree import SverchCustomTreeNode
from data_structure import (fullList, Vector_generate, Vector_degenerate,
                            updateNode, SvSetSocketAnyType, SvGetSocketAnyType)


class EvaluateLine(bpy.types.Node, SverchCustomTreeNode):
    ''' EvaluateLine '''
    bl_idname = 'EvaluateLineNode'
    bl_label = 'EvaluateLine'
    bl_icon = 'OUTLINER_OB_EMPTY'

    factor_ = FloatProperty(name='factor', description='Step length',
                            default=0.5, min=0.0, max=1.0,
                            options={'ANIMATABLE'}, update=updateNode)

    def init(self, context):
        self.inputs.new('StringsSocket', "Factor", "Factor").prop_name = 'factor_'
        self.inputs.new('VerticesSocket', "Vertice A", "Vertice A")
        self.inputs.new('VerticesSocket', "Vertice B", "Vertice B")
        self.outputs.new('VerticesSocket', "EvPoint", "EvPoint")

    def draw_buttons(self, context, layout):
        pass

    def update(self):
        # inputs
        VerticesA = []
        VerticesB = []
        factor = []

        if 'Vertice A' in self.inputs and self.inputs['Vertice A'].links:
            VerticesA = Vector_generate(SvGetSocketAnyType(self, self.inputs['Vertice A']))

        if 'Vertice B' in self.inputs and self.inputs['Vertice B'].links:
            VerticesB = Vector_generate(SvGetSocketAnyType(self, self.inputs['Vertice B']))

        if 'Factor' in self.inputs and self.inputs['Factor'].links:
            factor = SvGetSocketAnyType(self, self.inputs['Factor'])

        if not (VerticesA and VerticesB):
            return

        if not factor:
            factor = [[self.factor_]]

        # outputs
        if 'EvPoint' in self.outputs and self.outputs['EvPoint'].links:
            points = []

# match inputs using fullList, longest list matching on A and B
# extend factor list if necessary, it should not control length of output

            max_obj = max(len(VerticesA), len(VerticesB))
            fullList(VerticesA, max_obj)
            fullList(VerticesB, max_obj)
            if len(factor) < max_obj:
                fullList(factor, max_obj)

            for i in range(max_obj):
                points_ = []
                max_l = max(len(VerticesA[i]), len(VerticesB[i]))
                fullList(VerticesA[i], max_l)
                fullList(VerticesB[i], max_l)
                for j in range(max_l):
                    tmp_pts = [VerticesA[i][j].lerp(VerticesB[i][j], factor[i][k])
                               for k in range(len(factor[i]))]
                    points_.extend(tmp_pts)
                points.append(points_)
            if not points:
                return

            SvSetSocketAnyType(self, 'EvPoint', Vector_degenerate(points))

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(EvaluateLine)


def unregister():
    bpy.utils.unregister_class(EvaluateLine)
