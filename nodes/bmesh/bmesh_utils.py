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

import bpy,bmesh,mathutils
from bpy.props import EnumProperty, FloatProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode, enum_item as e, second_as_first_cycle as safc,match_long_repeat)

dict_bmesh = {"edge_rotate": ["Rotate the edge and return the newly created edge. If rotating the edge fails, None will be returned.\n", ["edge", "ccw"], ["bmesh.types.BMEdge", "False"], ["edge (bmesh.types.BMEdge) \u2013 The edge to rotate.\n", "ccw (boolean) \u2013 When True the edge will be rotated counter clockwise.\n"], "Returns\nThe newly rotated edge.\nReturn type\nbmesh.types.BMEdge\n"], "edge_split": ["Split an edge, return the newly created data.\n", ["edge", "vert", "fac"], ["bmesh.types.BMEdge", "bmesh.types.BMVert", "0"], ["edge (bmesh.types.BMEdge) \u2013 The edge to split.\n", "vert (bmesh.types.BMVert) \u2013 One of the verts on the edge, defines the split direction.\n", "fac (float) \u2013 The point on the edge where the new vert will be created [0 - 1].\n"], "Returns\nThe newly created (edge, vert) pair.\nReturn type\ntuple\n"], "face_flip": ["Flip the faces direction.\n", ["faces"], ['None'], ['face (bmesh.types.BMFace) - Face to flip'], "None"], "face_join": ["Joins a sequence of faces.\n", ["faces", "remove"], ["bmesh.types.BMFace", "False"], ["faces (bmesh.types.BMFace) \u2013 Sequence of faces.\n", "remove (boolean) \u2013 Remove the edges and vertices between the faces.\n"], "Returns\nThe newly created face or None on failure.\nReturn type\nbmesh.types.BMFace\n"], "face_split": ["Face split with optional intermediate points.\n", ["face", "vert_a", "vert_b", "coords", "use_exist", "example"], ["bmesh.types.BMFace", "bmesh.types.BMVert", "bmesh.types.BMVert", "(0,0,0)", "False", "bmesh.types.BMEdge"], ["face (bmesh.types.BMFace) \u2013 The face to cut.\n", "vert_a (bmesh.types.BMVert) \u2013 First vertex to cut in the face (face must contain the vert).\n", "vert_b (bmesh.types.BMVert) \u2013 Second vertex to cut in the face (face must contain the vert).\n", "coords (sequence of float triplets) \u2013 Optional argument to define points in between vert_a and vert_b.\n", "use_exist (boolean) \u2013 .Use an existing edge if it exists (Only used when coords argument is empty or omitted)\n", "example (bmesh.types.BMEdge) \u2013 Newly created edge will copy settings from this one.\n"], "Returns\nThe newly created face or None on failure.\nReturn type\n(bmesh.types.BMFace, bmesh.types.BMLoop) pair\n"], "face_split_edgenet": ["Splits a face into any number of regions defined by an edgenet.\n", ["face", "edgenet"], ["bmesh.types.BMFace", "None", "bmesh.types.BMEdge"], ["face (bmesh.types.BMFace) \u2013 The face to split.\n", "face \u2013 The face to split.\n", "edgenet (bmesh.types.BMEdge) \u2013 Sequence of edges.\n"], "Returns\nThe newly created faces.\nReturn type\ntuple of (bmesh.types.BMFace)\nNote\nRegions defined by edges need to connect to the face, otherwise they\u2019re ignored as loose edges.\n"], "face_vert_separate": ["Rip a vertex in a face away and add a new vertex.\n", ["face", "vert"], ["bmesh.types.BMFace", "bmesh.types.BMVert"], ["face (bmesh.types.BMFace) \u2013 The face to separate.\n", "vert (bmesh.types.BMVert) \u2013 A vertex in the face to separate.\n"], "None"], "loop_separate": ["Rip a vertex in a face away and add a new vertex.\n", ["loop"], ["None"], ["loop (bmesh.types.BMLoop) \u2013 The loop to separate.\n"], "None"], "vert_collapse_edge": ["Collapse a vertex into an edge.\n", ["vert", "edge"], ["bmesh.types.BMVert", "bmesh.types.BMEdge"], ["vert (bmesh.types.BMVert) \u2013 The vert that will be collapsed.\n", "edge (bmesh.types.BMEdge) \u2013 The edge to collapse into.\n"], "Returns\nThe resulting edge from the collapse operation.\nReturn type\nbmesh.types.BMEdge\n"], "vert_collapse_faces": ["Collapses a vertex that has only two manifold edges onto a vertex it shares an edge with.\n", ["vert", "edge", "fac", "join_faces"], ["bmesh.types.BMVert", "bmesh.types.BMEdge", "0", "False"], ["vert (bmesh.types.BMVert) \u2013 The vert that will be collapsed.\n", "edge (bmesh.types.BMEdge) \u2013 The edge to collapse into.\n", "fac (float) \u2013 The factor to use when merging customdata [0 - 1].\n", "join_faces (bool) \u2013 When true the faces around the vertex will be joined otherwise collapse the vertex by merging the 2 edges this vertex connects to into one.\n"], "Returns\nThe resulting edge from the collapse operation.\nReturn type\nbmesh.types.BMEdge\n"], "vert_dissolve": ["Dissolve this vertex (will be removed).\n", ["vert"], ["bmesh.types.BMVert"], ["vert (bmesh.types.BMVert) \u2013 The vert to be dissolved.\n"], "Returns\nTrue when the vertex dissolve is successful.\nReturn type\nboolean\n"], "vert_separate": ["Separate this vertex at every edge.\n", ["vert", "edges"], ["bmesh.types.BMVert", "bmesh.types.BMEdge"], ["vert (bmesh.types.BMVert) \u2013 The vert to be separated.\n", "edges (bmesh.types.BMEdge) \u2013 The edges to separated.\n"], "Returns\nThe newly separated verts (including the vertex passed).\nReturn type\ntuple of bmesh.types.BMVert\n"], "vert_splice": ["Splice vert into vert_target.\n", ["vert", "vert_target"], ["bmesh.types.BMVert", "bmesh.types.BMVert"], ["vert (bmesh.types.BMVert) \u2013 The vertex to be removed.\n", "vert_target (bmesh.types.BMVert) \u2013 The vertex to use.\n"], "None"]}

operators = []
for i,ops in enumerate(dict_bmesh.keys()):
    operators.append((ops,ops+'()',dict_bmesh[ops][0],i))

class SvBMUtilsNode(SverchCustomTreeNode, bpy.types.Node):
    '''Processing operators for bmesh data structures(vert,edge,face)'''
    bl_idname = 'SvBMUtilsNode'
    bl_label = 'BMesh Utils'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_ALPHA'  # 'SV_BMESH_OPS'
    def updata_oper(self,context):
        for key in self.inputs.keys():
            self.safe_socket_remove('inputs',key)
        
        for i,p in enumerate(dict_bmesh[self.oper][1]):
            des = dict_bmesh[self.oper][3][i]
            self.inputs.new('SvStringsSocket',p).description = des
        self.outputs['return'].description = dict_bmesh[self.oper][-1]
        updateNode(self,context)

    oper: EnumProperty(
        name='Operators',
        description = 'Operators for handling bmesh data structures(vert,edge,face)',
        default=operators[0][0],
        items=operators,
        update=updata_oper)
    
    def draw_buttons(self, context, layout):
        layout.prop(self,'oper',text='')

    def sv_init(self, context):
        for i,p in enumerate(dict_bmesh[operators[0][0]][1]):
            des = dict_bmesh[operators[0][0]][3][i]
            self.inputs.new('SvStringsSocket',p).description = des
        self.outputs.new('SvStringsSocket','return').description = 'None'
    def process(self):
        input = []
        for i,p in enumerate(dict_bmesh[self.oper][1]):
            default = dict_bmesh[self.oper][2][i]
            value = self.inputs[p].sv_get(default=[[default]])
            input.append(value)
        input = match_long_repeat(input)

        return_ = []
        for pars in zip(*input):
            pars = match_long_repeat(pars)
            result = []
            for p in zip(*pars):
                for i in range(len(p)):
                    if self.inputs[i].is_linked :
                        name_p = dict_bmesh[self.oper][1][i]
                        exec(name_p + '= p[i]')
                    else :
                        name_p = p[i]
                    if i == 0:
                        parameters = name_p
                    else:
                        parameters = parameters + ',' + name_p
                fun = 'bmesh.utils.' + self.oper + '(' + parameters +')'
                try :
                    result.append(eval(fun))
                except (TypeError) as Argument:
                    print(Argument)
            return_.append(result)
        
        self.outputs['return'].sv_set(return_)


def register():
    bpy.utils.register_class(SvBMUtilsNode)


def unregister():
    bpy.utils.unregister_class(SvBMUtilsNode)
