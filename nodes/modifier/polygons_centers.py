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
from mathutils import Vector, Matrix

from node_tree import SverchCustomTreeNode
from data_structure import SvSetSocketAnyType, SvGetSocketAnyType


class CentersPolsNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Centers of polygons of mesh (not including matrixes, so apply scale-rot-loc ctrl+A) '''
    bl_idname = 'CentersPolsNode'
    bl_label = 'Centers polygons'
    bl_icon = 'OUTLINER_OB_EMPTY'

    def init(self, context):
        self.inputs.new('VerticesSocket', "Vertices", "Vertices")
        self.inputs.new('StringsSocket', "Polygons", "Polygons")
        self.outputs.new('VerticesSocket', "Normals", "Normals")
        self.outputs.new('MatrixSocket', "Centers", "Centers")

    def update(self):
        # достаём два слота - вершины и полики
        if 'Centers' in self.outputs and self.outputs['Centers'].links or self.outputs['Normals'].links:
            if 'Polygons' in self.inputs and 'Vertices' in self.inputs \
                and self.inputs['Polygons'].links and self.inputs['Vertices'].links:

                pols_ = SvGetSocketAnyType(self, self.inputs['Polygons'])
                #else:
                #    pols = []

                #if type(self.inputs['Vertices'].links[0].from_socket) == VerticesSocket:
                vers_ = SvGetSocketAnyType(self, self.inputs['Vertices'])
                #else:
                #    vers = []

                #print ('Центрист.  полики, верики: ', pols, vers)

                # output

                # make mesh temp утилитарно - удалить в конце
                mat_collect = []
                normalsFORout = []
                for i_obj, vers in enumerate(vers_):
                    pols = pols_[i_obj]
                    mesh_temp = bpy.data.meshes.new('temp')
                    mesh_temp.from_pydata(vers, [], pols)
                    mesh_temp.update(calc_edges=True)

                    # medians в векторах
                    medians = []
                    for p in pols:
                        v0 = Vector(vers[p[0]][:])
                        v1 = Vector(vers[p[1]][:])
                        v2 = Vector(vers[p[2]][:])
                        if len(p) > 3:
                            v3 = Vector(vers[p[3]][:])
                            poi_2 = (v2+v3)/2
                        else:
                            poi_2 = v2

                        poi_1 = (v0+v1)/2
                        vm = poi_2 - poi_1
                        medians.append(vm)

                    # centers, normals - делает векторы из mesh temp
                    centrs = []
                    normals = []
                    normalsFORout_ = []
                    for p in mesh_temp.polygons:
                        centrs.append(Vector(p.center[:]))
                        normals.append(p.normal)
                        normalsFORout_.append(p.normal[:])
                    normalsFORout.append(normalsFORout_)
                    #print ('norm', normals, normalsFORout)
                    # centrs = mathutils.geometry.normal( lambda(vers[p[0]], vers[p[1]], vers[p[2]] for p in pols) ) # альтернатива
                    mat_collect_ = []
                    for i, c in enumerate(centrs):
                        mat_loc = Matrix.Translation(c)
                        aa = Vector((0, 1e-6, 1))
                        bb = Vector((normals[i][:]))

                        vec = aa
                        q_rot = vec.rotation_difference(bb).to_matrix().to_4x4()

                        vec2 = bb
                        q_rot2 = vec2.rotation_difference(aa).to_matrix().to_4x4()

                        a = Vector((1e-6, 1, 0)) * q_rot2
                        b = medians[i]
                        vec1 = a
                        q_rot1 = vec1.rotation_difference(b).to_matrix().to_4x4()

                        M = mat_loc*q_rot1*q_rot
                        lM = []

                        for j in M:
                            lM.append((j[:]))
                        # отдаётся параметр матрицы на сокет. просто присвоение матрицы
                        mat_collect_.append(lM)
                    mat_collect.extend(mat_collect_)
                        #print ( 'M'+ str(M) + '\n' + 'lM' + str(lM) + '\n' + 'qrot' + str(q_rot1) + '\n' )
                #print ( 'matrix: ' + str(mat_collect) )
                SvSetSocketAnyType(self, 'Centers', mat_collect)
                # удаляем временный мусор
                bpy.data.meshes.remove(mesh_temp)
                if 'Normals' in self.outputs and len(self.outputs['Normals'].links) > 0:
                    SvSetSocketAnyType(self, 'Normals', normalsFORout)

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(CentersPolsNode)


def unregister():
    bpy.utils.unregister_class(CentersPolsNode)
