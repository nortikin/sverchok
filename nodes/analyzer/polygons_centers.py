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
from mathutils import Vector, Matrix, geometry

from node_tree import SverchCustomTreeNode
from data_structure import SvSetSocketAnyType, SvGetSocketAnyType, \
                        Vector_generate, Vector_degenerate


class CentersPolsNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Centers of polygons of mesh (not including matrixes, so apply scale-rot-loc ctrl+A) '''
    bl_idname = 'CentersPolsNode'
    bl_label = 'Centers polygons'
    bl_icon = 'OUTLINER_OB_EMPTY'

    def init(self, context):
        self.inputs.new('VerticesSocket', "Vertices", "Vertices")
        self.inputs.new('StringsSocket', "Polygons", "Polygons")
        self.outputs.new('VerticesSocket', "Normals", "Normals")
        self.outputs.new('VerticesSocket', "Norm_abs", "Norm_abs")
        self.outputs.new('VerticesSocket', "Origins", "Origins")
        self.outputs.new('MatrixSocket', "Centers", "Centers")

    def update(self):
        # достаём два слота - вершины и полики
        if self.outputs['Centers'].links or self.outputs['Normals'].links or \
                self.outputs['Origins'].links or self.outputs['Norm_abs'].links:
            if 'Polygons' in self.inputs and 'Vertices' in self.inputs \
                and self.inputs['Polygons'].links and self.inputs['Vertices'].links:

                pols_ = SvGetSocketAnyType(self, self.inputs['Polygons'])
                vers_tupls = SvGetSocketAnyType(self, self.inputs['Vertices'])
                vers_vects = Vector_generate(vers_tupls)
                
                # make mesh temp утилитарно - удалить в конце
                mat_collect = []
                normals_out = []
                origins = []
                norm_abs_out = []
                for verst, versv, pols in zip(vers_tupls, vers_vects, pols_):
                    # medians в векторах
                    medians = []
                    normals = []
                    centrs = []
                    norm_abs = []
                    for p in pols:
                        # medians
                        # it calcs middle point of opposite edges, 
                        # than finds length vector between this two points
                        v0 = versv[p[0]]
                        v1 = versv[p[1]]
                        v2 = versv[p[2]]
                        lp=len(p)
                        if lp >= 4:
                            l = ((lp-2)//2) + 2
                            v3 = versv[p[l]]
                            poi_2 = (v2+v3)/2
                            # normals
                            norm = geometry.normal(v0, v1, v3)
                            normals.append(norm)
                        else:
                            poi_2 = v2
                            # normals
                            norm = geometry.normal(v0, v1, v2)
                            normals.append(norm)
                        poi_1 = (v0+v1)/2.1
                        vm = poi_2 - poi_1
                        medians.append(vm)
                        # centrs
                        x,y,z = zip(*[verst[poi] for poi in p])
                        x,y,z = sum(x)/len(x), sum(y)/len(y), sum(z)/len(z)
                        current_center = Vector((x,y,z))
                        centrs.append(current_center)
                        # normal absolute !!!
                        # это совершенно нормально!!! ;-)
                        norm_abs.append(current_center+norm)
                        
                    norm_abs_out.append(norm_abs)    
                    origins.append(centrs)
                    normals_out.extend(normals)
                    mat_collect_ = []
                    for c, med, nor in zip(centrs, medians, normals):
                        mat_loc = Matrix.Translation(c)
                        # need better solution for Y vector 
                        aa = Vector((0, 1e-6, 1))
                        bb = nor #Vector((nor[:]))

                        vec = aa
                        q_rot = vec.rotation_difference(bb).to_matrix().to_4x4()

                        vec2 = bb
                        q_rot2 = vec2.rotation_difference(aa).to_matrix().to_4x4()

                        a = Vector((1e-6, 1, 0)) * q_rot2
                        b = med
                        vec1 = a
                        q_rot1 = vec1.rotation_difference(b).to_matrix().to_4x4()

                        M = mat_loc*q_rot1*q_rot
                        lM = []

                        for j in M:
                            lM.append((j[:]))
                        # отдаётся параметр матрицы на сокет. просто присвоение матрицы
                        mat_collect_.append(lM)
                    mat_collect.extend(mat_collect_)
                
                if 'Centers' in self.outputs and self.outputs['Centers'].links:
                    SvSetSocketAnyType(self, 'Centers', mat_collect)
                SvSetSocketAnyType(self, 'Norm_abs', Vector_degenerate(norm_abs_out))
                SvSetSocketAnyType(self, 'Origins', Vector_degenerate(origins))
                SvSetSocketAnyType(self, 'Normals', Vector_degenerate([normals_out]))

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(CentersPolsNode)


def unregister():
    bpy.utils.unregister_class(CentersPolsNode)
if __name__ == '__main__':
    register()

