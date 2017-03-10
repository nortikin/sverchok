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
from bpy.props import IntProperty, FloatProperty, BoolProperty, EnumProperty

from mathutils import Matrix, Vector

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat, Matrix_generate

maskTypeItems = [("VERTICES", "V", ""), ("EDGES", "E", ""), ("POLYGONS", "P", ""), ]

class SvTransformSelectNode(bpy.types.Node, SverchCustomTreeNode):

    ''' Transform Select '''
    bl_idname = 'SvTransformSelectNode'
    bl_label = 'Transform Select'

    maskType = EnumProperty(
        name="Mask Type", description="Mask various mesh components",
        default="VERTICES", items=maskTypeItems,
        update=updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'maskType', expand=True)

    def sv_init(self, context):
        self.inputs.new('StringsSocket', "Mask")
        self.inputs.new('VerticesSocket', "Vertices")
        self.inputs.new('StringsSocket', "PolyEdge")
        self.inputs.new('MatrixSocket', "Matrix T")
        self.inputs.new('MatrixSocket', "Matrix F")

        self.outputs.new('VerticesSocket', "Vertices")
        self.outputs.new('StringsSocket', "PolyEdge")
        self.outputs.new('VerticesSocket', "Vertices T")
        self.outputs.new('StringsSocket', "PolyEdge T")
        self.outputs.new('VerticesSocket', "Vertices F")
        self.outputs.new('StringsSocket', "PolyEdge F")


    def process(self):
        # return if no outputs are connected
        if not any(s.is_linked for s in self.outputs):
            return

        inputs = self.inputs
        outputs = self.outputs

        input_verts = inputs['Vertices'].sv_get()[0]
        input_polys = inputs['PolyEdge'].sv_get()[0]
        input_matrixT = inputs['Matrix T'].sv_get()
        input_matrixF = inputs['Matrix F'].sv_get()

        if inputs['Mask'].is_linked:
            input_mask = inputs['Mask'].sv_get()[0]
        else:
            n = len(input_verts)
            input_mask = ([1,0]*(int((n+1)/2)))[:n]

        matrixF = Matrix_generate(input_matrixF)
        matrixT = Matrix_generate(input_matrixT)

        # print("Mask: ", input_mask)
        # print("Vertices: ", input_verts)
        # print("Matrix F: ", matrixF)
        # print("Matrix T: ", matrixT)

        params = match_long_repeat([input_mask, input_verts, matrixT, matrixF])
        # print("params: ", params)

        vertList = []
        vertListT = []
        vertListF = []
        polyEdgeListT = []
        polyEdgeListF = []
        for i, v, mt, mf in zip(*params):
            # print('Vertex:', v, " has mask:", i)
            # print('Matrix T:', mt)
            # print('Matrix F:', mf)
            if i == 1: # do some processing using Matrix T here
                v = (mt * Vector(v))[:]
                vertListT.append(v)
            else: # do some processing using Matrix F here
                v = (mf * Vector(v))[:]
                vertListF.append(v)
            vertList.append(v)

        # print("Vertices T: ", vertListT)
        # print("Vertices F: ", vertListF)
        outputs['Vertices'].sv_set([vertList])
        outputs['Vertices T'].sv_set([vertListT])
        outputs['PolyEdge T'].sv_set([polyEdgeListT])
        outputs['Vertices F'].sv_set([vertListF])
        outputs['PolyEdge F'].sv_set([polyEdgeListT])

def register():
    bpy.utils.register_class(SvTransformSelectNode)


def unregister():
    bpy.utils.unregister_class(SvTransformSelectNode)

if __name__ == '__main__':
    register()
