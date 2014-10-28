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
from sv_data_structure import SvSetSocketAnyType, SvGetSocketAnyType


class VectorNormalNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Find Vector's normals '''
    bl_idname = 'VectorNormalNode'
    bl_label = 'Vector Normal'
    bl_icon = 'OUTLINER_OB_EMPTY'

    def init(self, context):
        self.inputs.new('VerticesSocket', "Vertices", "Vertices")
        self.inputs.new('StringsSocket', "Polygons", "Polygons")
        self.outputs.new('VerticesSocket', "Normals", "Normals")

    def update(self):
        # достаём два слота - вершины и полики
        if 'Centers' in self.outputs and self.outputs['Centers'].links or self.outputs['Normals'].links:
            if 'Polygons' in self.inputs and 'Vertices' in self.inputs and self.inputs['Polygons'].links and self.inputs['Vertices'].links:

                #if type(self.inputs['Poligons'].links[0].from_socket) == StringsSocket:
                pols = SvGetSocketAnyType(self, self.inputs['Polygons'])

                #if type(self.inputs['Vertices'].links[0].from_socket) == VerticesSocket:
                vers = SvGetSocketAnyType(self, self.inputs['Vertices'])
                normalsFORout = []
                for i, obj in enumerate(vers):
                    mesh_temp = bpy.data.meshes.new('temp')
                    mesh_temp.from_pydata(obj, [], pols[i])
                    mesh_temp.update(calc_edges=True)
                    tempobj = []
                    for v in mesh_temp.vertices:
                        tempobj.append(v.normal[:])
                    normalsFORout.append(tempobj)
                    bpy.data.meshes.remove(mesh_temp)
                #print (normalsFORout)

                if 'Normals' in self.outputs and self.outputs['Normals'].links:
                    SvSetSocketAnyType(self, 'Normals', normalsFORout)

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(VectorNormalNode)


def unregister():
    bpy.utils.unregister_class(VectorNormalNode)
