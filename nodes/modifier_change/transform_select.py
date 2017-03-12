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

        # endTime = time.time()
        # print("Computing Time: ", endTime-startTime)
        # return

        params = match_long_repeat([input_mask, input_verts, matrixT, matrixF])
        # print("params: ", params)

        vert_indexT = [i for i, m in enumerate(input_mask) if m]
        vert_indexF = [i for i, m in enumerate(input_mask) if not m]
        vt1 = { j:i for i, j in enumerate(vert_indexT) }
        vf1 = { j:i for i, j in enumerate(vert_indexF) }

        vertListA = []
        vertListT = []
        vertListF = []
        polyEdgeListA = []
        polyEdgeListT = []
        polyEdgeListF = []
        polyEdgeListO = []
        # vt = {}
        # vf = {}
        # vid = 0
        for ma, v, mt, mf in zip(*params):
            # print('Vertex:', v, " has mask:", ma)
            # print('Matrix T:', mt)
            # print('Matrix F:', mf)
            if ma == 1:  # do some processing using Matrix T here
                v = (mt * Vector(v))[:]
                vertListT.append(v)
                # vt[vid] = len(vertListT) - 1
            else:  # do some processing using Matrix F here
                v = (mf * Vector(v))[:]
                vertListF.append(v)
                # vf[vid] = len(vertListF) - 1
            vertListA.append(v)
            # vid = vid + 1

        # print("vt = ", vt)
        # print("vf = ", vf)
        # print("vt1 = ", vt1)
        # print("vf1 = ", vf1)

        polyEdgeListA = input_polys

        # vert_indexT = [i for i, m in enumerate(input_mask) if m]
        # vert_indexF = [i for i, m in enumerate(input_mask) if not m]

        # vert1_indexT = [vt[i] for i, m in enumerate(input_mask) if m]
        # vert1_indexF = [vf[i] for i, m in enumerate(input_mask) if not m]

        # print("vert_indexT = ", vert_indexT)
        # print("vert_indexF = ", vert_indexF)
        # print("vt.k = ", vt.keys())
        # print("vf.k = ", vf.keys())
        # print("vert1_indexT = ", vert1_indexT)
        # print("vert1_indexF = ", vert1_indexF)

        vext = set(vt1.keys())
        vexf = set(vf1.keys())
        # vext = set(vert_indexT)
        # vexf = set(vert_indexF)
        # print("vext = ", vext)
        # print("vexf = ", vexf)
        for pe in input_polys:
            # i1, i2 = pe

            pex = set(pe)
            # print("pex = ", pex)

            if vext.issuperset(pex):
                # print("pex ", pex, " is in vext ", vext)
                pet = [vt1[i] for i in pe]
                # pet = [vt[i] for i in pe]
                polyEdgeListT.append(pet)
                # polyEdgeListT.append([vt[i1], vt[i2]])

            elif vexf.issuperset(pex):
                # print("pex ", pex, " is in vexf ", vexf)
                pef = [vf1[i] for i in pe]
                # pef = [vf[i] for i in pe]
                polyEdgeListF.append(pef)
                # polyEdgeListT.append([vf[i1], vf[i2]])

            else:
                polyEdgeListO.append(pe)
            # print("pe=", pe, " i1 = ", i1, " i2 = ", i2)
            # if i1 in vt and i2 in vt:
            #     # print("i1 = ", i1, " i2 = ", i2, " is in vt =", vt)
            #     polyEdgeListT.append([vt[i1], vt[i2]])
            # if i1 in vf and i2 in vf:
            #     # print("i1 = ", i1, " i2 = ", i2, " is in vf =", vf)
            #     polyEdgeListF.append([vf[i1], vf[i2]])

            # if i1 in vt and i2 in vf or i1 in vf and i2 in vt:
            #     polyEdgeListO.append([i1, i2])

        # print("Vertices T: ", vertListT)
        # print("Vertices F: ", vertListF)
        outputs['Vertices'].sv_set([vertListA])
        outputs['PolyEdge'].sv_set([polyEdgeListA])
        outputs['PolyEdge O'].sv_set([polyEdgeListO])
        outputs['Vertices T'].sv_set([vertListT])
        outputs['PolyEdge T'].sv_set([polyEdgeListT])
        outputs['Vertices F'].sv_set([vertListF])
        outputs['PolyEdge F'].sv_set([polyEdgeListF])

        endTime = time.time()
        print("Computing Time: ", endTime-startTime)

def register():
    bpy.utils.register_class(SvTransformSelectNode)


def unregister():
    bpy.utils.unregister_class(SvTransformSelectNode)

if __name__ == '__main__':
    register()
