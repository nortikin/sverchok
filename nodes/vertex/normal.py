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
import bmesh

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import SvSetSocketAnyType, SvGetSocketAnyType
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata


class VectorNormalNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Find Vector's normals '''
    bl_idname = 'VectorNormalNode'
    bl_label = 'Vertex Normal'
    bl_icon = 'OUTLINER_OB_EMPTY'

    def sv_init(self, context):
        self.inputs.new('VerticesSocket', "Vertices", "Vertices")
        self.inputs.new('StringsSocket', "Polygons", "Polygons")
        self.outputs.new('VerticesSocket', "Normals", "Normals")

    def process(self):
        # достаём два слота - вершины и полики
        if 'Centers' in self.outputs and self.outputs['Centers'].links or self.outputs['Normals'].links:
            if 'Polygons' in self.inputs and 'Vertices' in self.inputs and self.inputs['Polygons'].links and self.inputs['Vertices'].links:

                #if type(self.inputs['Poligons'].links[0].from_socket) == StringsSocket:
                pols = SvGetSocketAnyType(self, self.inputs['Polygons'])

                #if type(self.inputs['Vertices'].links[0].from_socket) == VerticesSocket:
                vers = SvGetSocketAnyType(self, self.inputs['Vertices'])
                normalsFORout = []
                for i, obj in enumerate(vers):
                    """
                    mesh_temp = bpy.data.meshes.new('temp')
                    mesh_temp.from_pydata(obj, [], pols[i])
                    mesh_temp.update(calc_edges=True)
                    """
                    bm = bmesh_from_pydata(obj, [], pols[i])

                    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
                    bm.verts.ensure_lookup_table()
                    verts = bm.verts
                    tempobj = []

                    for idx in range(len(verts)):
                        tempobj.append(verts[idx].normal[:])

                    normalsFORout.append(tempobj)

                    bm.free()
                    #bpy.data.meshes.remove(mesh_temp)
                #print (normalsFORout)

                if 'Normals' in self.outputs and self.outputs['Normals'].links:
                    SvSetSocketAnyType(self, 'Normals', normalsFORout)


def register():
    bpy.utils.register_class(VectorNormalNode)


def unregister():
    bpy.utils.unregister_class(VectorNormalNode)
