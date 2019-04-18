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

from itertools import chain
import bpy
from bpy.props import EnumProperty
from mathutils import Matrix, Vector
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat

maskTypeItems = [("VERTICES", "Verts", "Mask refers to Vertices", 0), ("POLY_EDGE", "PolyEdge", "Mask refers to PolyEdge", 1), ]


class SvTransformSelectNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Apply matrix w. mask.
    Tooltip: Transform part of geometry.
    """
    bl_idname = 'SvTransformSelectNode'
    bl_label = 'Transform Select'
    bl_icon = 'EDITMODE_HLT'

    maskType = EnumProperty(
        name="Mask Type", description="Mask various mesh components",
        default="VERTICES", items=maskTypeItems, update=updateNode)

    def draw_buttons(self, context, layout):
        '''draw ui buttons'''
        layout.prop(self, 'maskType', expand=True)

    def sv_init(self, context):
        '''define input and output sockets'''
        sin = self.inputs.new
        son = self.outputs.new
        sin('StringsSocket', "Mask")
        sin('VerticesSocket', "Vertices")
        sin('StringsSocket', "PolyEdge")
        sin('MatrixSocket', "Matrix T")
        sin('MatrixSocket', "Matrix F")

        son('VerticesSocket', "Vertices")
        son('StringsSocket', "PolyEdge")
        son('StringsSocket', "PolyEdge O")
        son('VerticesSocket', "Vertices T")
        son('StringsSocket', "PolyEdge T")
        son('VerticesSocket', "Vertices F")
        son('StringsSocket', "PolyEdge F")

    def get_data(self):
        '''get data from inputs and match it'''
        inputs = self.inputs
        polys_linked = inputs['PolyEdge'].is_linked
        input_verts = inputs['Vertices'].sv_get()[0]
        n = len(input_verts)
        input_polys = inputs['PolyEdge'].sv_get(default=[[]])[0]
        matrix_true = inputs['Matrix T'].sv_get(default=[Matrix()])
        matrix_false = inputs['Matrix F'].sv_get(default=[Matrix()])

        input_mask = self.get_mask(n, input_polys, polys_linked)
        matrix_false = matrix_false[:n]
        matrix_true = matrix_true[:n]

        params = match_long_repeat([input_mask, input_verts, matrix_true, matrix_false])

        return params, input_polys, polys_linked

    def get_mask(self, n, input_polys, polys_linked):
        '''get mask and convert it to vertices mask if needed'''
        inputs = self.inputs
        if self.maskType == "VERTICES" or not polys_linked:
            if inputs['Mask'].is_linked:
                input_mask = inputs['Mask'].sv_get()[0][:n]
                input_mask = list(map(lambda x: int(x) % 2, input_mask))
            else:  # if no mask input, generate a 0,1,0,1 mask
                input_mask = ([1, 0] * (int((n + 1) / 2)))[:n]
        else:
            len_poly_edge = len(input_polys)
            if inputs['Mask'].is_linked:
                input_mask = inputs['Mask'].sv_get()[0][:len_poly_edge]
                input_mask = list(map(lambda x: int(x) % 2, input_mask))
            else:  # if no mask input, generate a 0,1,0,1 mask
                input_mask = ([1, 0] * (int((n + 1) / 2)))[:len_poly_edge]

            masked_pe = [pe for i, pe in enumerate(input_polys) if input_mask[i] == 1]
            verts_in_pe = set(chain(*masked_pe))
            input_mask = [(i in verts_in_pe) for i in range(n)]

        return input_mask

    def process_vertices(self, params):
        '''apply matrices to vertices'''
        vert_all, vert_true, vert_false = [[], [], []]
        for ma, v, mt, mf in zip(*params):
            if ma == 1:  # do some processing using Matrix T here
                v = (mt * Vector(v))[:]
                vert_true.append(v)
            else:  # do some processing using Matrix F here
                v = (mf * Vector(v))[:]
                vert_false.append(v)
            vert_all.append(v)

        return  vert_all, vert_true, vert_false

    def process_poly_edge(self, polys_linked, input_polys, input_mask):
        '''split poly_edge data'''
        poly_edge_true, poly_edge_false, poly_edge_other = [[], [], []]
        if polys_linked:
            vert_index_true = [i for i, m in enumerate(input_mask) if m]
            vert_index_false = [i for i, m in enumerate(input_mask) if not m]
            vt = {j: i for i, j in enumerate(vert_index_true)}
            vf = {j: i for i, j in enumerate(vert_index_false)}

            vext = set(vert_index_true)
            vexf = set(vert_index_false)

            in_set_true, in_set_false = vext.issuperset, vexf.issuperset
            for pe in input_polys:
                pex = set(pe)
                if in_set_true(pex):
                    poly_edge_true.append([vt[i] for i in pe])
                elif in_set_false(pex):
                    poly_edge_false.append([vf[i] for i in pe])
                else:
                    poly_edge_other.append(pe)

        return poly_edge_true, poly_edge_false, poly_edge_other

    def process(self):
        # return if no outputs are connected
        if not any(s.is_linked for s in self.outputs):
            return

        params, input_polys, polys_linked = self.get_data()

        vert_all, vert_true, vert_false = self.process_vertices(params)

        poly_edge_all = input_polys
        poly_edge_true, poly_edge_false, poly_edge_other = self.process_poly_edge(polys_linked, input_polys, params[0])

        so = self.outputs
        so['Vertices'].sv_set([vert_all])
        so['PolyEdge'].sv_set([poly_edge_all])
        so['PolyEdge O'].sv_set([poly_edge_other])
        so['Vertices T'].sv_set([vert_true])
        so['PolyEdge T'].sv_set([poly_edge_true])
        so['Vertices F'].sv_set([vert_false])
        so['PolyEdge F'].sv_set([poly_edge_false])


def register():
    bpy.utils.register_class(SvTransformSelectNode)


def unregister():
    bpy.utils.unregister_class(SvTransformSelectNode)
