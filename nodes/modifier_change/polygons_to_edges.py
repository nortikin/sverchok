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

from sv_node_tree import SverchCustomTreeNode
from sv_data_structure import dataCorrect, SvSetSocketAnyType, SvGetSocketAnyType


class Pols2EdgsNode(bpy.types.Node, SverchCustomTreeNode):
    ''' take polygon and to edges '''
    bl_idname = 'Pols2EdgsNode'
    bl_label = 'Polygons 2 Edges'
    bl_icon = 'OUTLINER_OB_EMPTY'

    def init(self, context):
        self.inputs.new('StringsSocket', "pols", "pols")
        self.outputs.new('StringsSocket', "edgs", "edgs")

    def update(self):
        if 'edgs' in self.outputs and len(self.outputs['edgs'].links) > 0:
            if 'pols' in self.inputs and len(self.inputs['pols'].links) > 0:
                X_ = SvGetSocketAnyType(self, self.inputs['pols'])
                X = dataCorrect(X_)
                #print('p2e-X',str(X))
                result = self.pols_edges(X)
                #result = self.polstoedgs(X)
                SvSetSocketAnyType(self, 'edgs', result)

    def pols_edges(self, obj):
        out = []
        for faces in obj:
            out_edges = [] #set() #[]
            for face in faces:
                for edge in zip(face, face[1:]+[face[0]]):
                    #out_edges.add(tuple(sorted(edge)))
                    out_edges.append(list(edge))
            out.append(out_edges)
        return out

    def polstoedgs(self, pols):
        out = []
        for obj in pols:
            object = []
            for pols in obj:
                edgs = []
                for i, ind in enumerate(pols):
                    #print('p2e',str(i%2), str(ind))
                    this = [ind, pols[i-1]]
                    this.sort()
                    if this not in edgs and this not in object:
                        edgs.append(this)
                object.extend(edgs)
            out.append(object)
        #print('p2e',str(out))
        return out


def register():
    bpy.utils.register_class(Pols2EdgsNode)


def unregister():
    bpy.utils.unregister_class(Pols2EdgsNode)

if __name__ == '__main__':
    register()

