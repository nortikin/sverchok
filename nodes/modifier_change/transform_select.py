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
import time

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
        self.outputs.new('StringsSocket', "PolyEdge O")
        self.outputs.new('VerticesSocket', "Vertices T")
        self.outputs.new('StringsSocket', "PolyEdge T")
        self.outputs.new('VerticesSocket', "Vertices F")
        self.outputs.new('StringsSocket', "PolyEdge F")

    def process(self):
        startTime = time.time()

        # return if no outputs are connected
        if not any(s.is_linked for s in self.outputs):
            return

        inputs = self.inputs
        outputs = self.outputs

        input_verts = inputs['Vertices'].sv_get()[0]
        input_polys = inputs['PolyEdge'].sv_get()[0]
        input_matrixT = inputs['Matrix T'].sv_get()
        input_matrixF = inputs['Matrix F'].sv_get()

        n = len(input_verts)

        if inputs['Mask'].is_linked:
            input_mask = inputs['Mask'].sv_get()[0]
            input_mask = input_mask[:n]
        else:  # if no mask input, generate a 0,1,0,1 mask
            input_mask = ([1, 0] * (int((n + 1) / 2)))[:n]

        matrixF = Matrix_generate(input_matrixF)
        matrixT = Matrix_generate(input_matrixT)

        matrixF = matrixF[:n]
        matrixT = matrixT[:n]

        # print("Mask: ", input_mask)
        # print("Vertices: ", input_verts)
        # print("Matrix F: ", matrixF)
        # print("Matrix T: ", matrixT)

        params = match_long_repeat([input_mask, input_verts, matrixT, matrixF])
        # print("params: ", params)

        # process vertices
        vertListA, vertListT, vertListF = [[], [], []]
        for ma, v, mt, mf in zip(*params):
            # print('Vertex:', v, " has mask:", ma)
            # print('Matrix T:', mt)
            # print('Matrix F:', mf)
            if ma == 1:  # do some processing using Matrix T here
                v = (mt * Vector(v))[:]
                vertListT.append(v)
            else:  # do some processing using Matrix F here
                v = (mf * Vector(v))[:]
                vertListF.append(v)
            vertListA.append(v)

        # process polyEdges
        vert_indexT = [i for i, m in enumerate(input_mask) if m]
        vert_indexF = [i for i, m in enumerate(input_mask) if not m]
        vt = {j: i for i, j in enumerate(vert_indexT)}
        vf = {j: i for i, j in enumerate(vert_indexF)}
        # vext = set(vt.keys())
        # vexf = set(vf.keys())
        vext = set(vert_indexT)
        vexf = set(vert_indexF)
        # print("vt.k = ", vt.keys())
        # print("vf.k = ", vf.keys())
        # print("vert_indexT = ", vert_indexT)
        # print("vert_indexF = ", vert_indexF)
        # print("vext = ", vext)
        # print("vexf = ", vexf)
        # print("vt = ", vt)
        # print("vf = ", vf)

        polyEdgeListA = input_polys
        polyEdgeListT, polyEdgeListF, polyEdgeListO = [[], [], []]

        # pelT = [[vt[i] for i in pe] for pe in input_polys if isSetT(set(pe))]
        # pelF = [[vf[i] for i in pe] for pe in input_polys if isSetF(set(pe))]

        inSetT, inSetF = vext.issuperset, vexf.issuperset
        addPET, addPEF, addPEO = polyEdgeListT.append, polyEdgeListF.append, polyEdgeListO.append
        for pe in input_polys:
            pex = set(pe)
            # print("pex = ", pex)

            if inSetT(pex):
                # print("pex ", pex, " is in vext ", vext)
                # pet = [vt[i] for i in pe]
                # polyEdgeListT.append(pet)
                addPET([vt[i] for i in pe])
                # polyEdgeListT.append([vt[i] for i in pe])

            elif inSetF(pex):
                # print("pex ", pex, " is in vexf ", vexf)
                # pef = [vf[i] for i in pe]
                # polyEdgeListF.append(pef)
                # polyEdgeListF.append([vf[i] for i in pe])
                addPEF([vf[i] for i in pe])

            else:
                # polyEdgeListO.append(pe)
                addPEO(pe)

        outputs['Vertices'].sv_set([vertListA])
        outputs['PolyEdge'].sv_set([polyEdgeListA])
        outputs['PolyEdge O'].sv_set([polyEdgeListO])
        outputs['Vertices T'].sv_set([vertListT])
        outputs['PolyEdge T'].sv_set([polyEdgeListT])
        outputs['Vertices F'].sv_set([vertListF])
        outputs['PolyEdge F'].sv_set([polyEdgeListF])

        endTime = time.time()
        print("Computing Time: ", endTime - startTime)


def register():
    bpy.utils.register_class(SvTransformSelectNode)


def unregister():
    bpy.utils.unregister_class(SvTransformSelectNode)

if __name__ == '__main__':
    register()
