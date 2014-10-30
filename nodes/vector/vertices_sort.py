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

from operator import itemgetter

import bpy
from bpy.props import EnumProperty
from mathutils import Matrix, Vector
from mathutils.geometry import intersect_point_line

from node_tree import SverchCustomTreeNode
from data_structure import (repeat_last, Matrix_generate, Vector_generate,
                            updateNode, SvSetSocketAnyType, SvGetSocketAnyType)


# distance between two points without sqrt, for comp only
def distK(v1, v2):
    return sum((i[0]-i[1])**2 for i in zip(v1, v2))


class SvVertSortNode(bpy.types.Node, SverchCustomTreeNode):
    '''Vector sort'''
    bl_idname = 'SvVertSortNode'
    bl_label = 'Vector Sort'
    bl_icon = 'OUTLINER_OB_EMPTY'

    def mode_change(self, context):
        if self.mode == 'XYZ':
            while len(self.inputs) > 2:
                self.inputs.remove(self.inputs[-1])
        if self.mode == 'DIST':
            while len(self.inputs) > 2:
                self.inputs.remove(self.inputs[-1])
            self.inputs.new('VerticesSocket', 'Base Point', 'Base Point')

        if self.mode == 'AXIS':
            while len(self.inputs) > 2:
                self.inputs.remove(self.inputs[-1])
            self.inputs.new('MatrixSocket', 'Mat')

        if self.mode == 'USER':
            while len(self.inputs) > 2:
                self.inputs.remove(self.inputs[-1])
            self.inputs.new('StringsSocket', 'Index Data', 'Index Data')

        updateNode(self, [])

    modes = [("XYZ",    "XYZ", "X Y Z Sort",    1),
             ("DIST",   "Dist", "Distance",     2),
             ("AXIS",   "Axis", "Axial sort",   3),
             ("USER",   "User", "User defined", 10)]

    mode = EnumProperty(default='XYZ', items=modes,
                        update=mode_change)

    def draw_buttons(self, context, layout):
        layout.label("Sort mode:")
        layout.prop(self, "mode", expand=True)
        if self.mode == "XYZ":
            pass

    def init(self, context):
        self.inputs.new('VerticesSocket', 'Vertices', 'Vertices')
        self.inputs.new('StringsSocket', 'PolyEdge', 'PolyEdge')

        self.outputs.new('VerticesSocket', 'Vertices')
        self.outputs.new('StringsSocket', 'PolyEdge')
        self.outputs.new('StringsSocket', 'Item order')

    def update(self):

        if 'Vertices' in self.inputs and self.inputs['Vertices'].links:
            verts = SvGetSocketAnyType(self, self.inputs['Vertices'])

            if 'PolyEdge' in self.inputs and self.inputs['PolyEdge'].links:
                poly_edge = SvGetSocketAnyType(self, self.inputs['PolyEdge'])
                polyIn = True
            else:
                polyIn = False
                poly_edge = repeat_last([[]])

            verts_out = []
            poly_edge_out = []
            item_order = []

            polyOutput = bool(polyIn and 'PolyEdge' in self.outputs and self.outputs['PolyEdge'].links)
            orderOutput = bool('Item order' in self.outputs and self.outputs['Item order'].links)
            vertOutput = bool('Vertices' in self.outputs and self.outputs['Vertices'].links)

            if not any((vertOutput, orderOutput, polyOutput)):
                return

            if self.mode == 'XYZ':
                # should be user settable
                op_order = [(0, False),
                            (1, False),
                            (2, False)]

                for v, p in zip(verts, poly_edge):
                    s_v = ((e[0], e[1], e[2], i) for i, e in enumerate(v))

                    for item_index, rev in op_order:
                        s_v = sorted(s_v, key=itemgetter(item_index), reverse=rev)

                    verts_out.append([v[:3] for v in s_v])

                    if polyOutput:
                        v_index = {item[-1]: j for j, item in enumerate(s_v)}
                        poly_edge_out.append([list(map(lambda n:v_index[n], pe)) for pe in p])
                    if orderOutput:
                        item_order.append([i[-1] for i in s_v])

            if self.mode == 'DIST':
                if 'Base Point' in self.inputs and self.inputs['Base Point'].links:
                    base_points = SvGetSocketAnyType(self, self.inputs['Base Point'])
                    bp_iter = repeat_last(base_points[0])
                else:
                    bp = [(0, 0, 0)]
                    bp_iter = repeat_last(bp)

                for v, p, v_base in zip(verts, poly_edge, bp_iter):
                    s_v = sorted(((v_c, i) for i, v_c in enumerate(v)), key=lambda v: distK(v[0], v_base))
                    verts_out.append([vert[0] for vert in s_v])

                    if polyOutput:
                        v_index = {item[-1]: j for j, item in enumerate(s_v)}
                        poly_edge_out.append([list(map(lambda n:v_index[n], pe)) for pe in p])
                    if orderOutput:
                        item_order.append([i[-1] for i in s_v])

            if self.mode == 'AXIS':
                if 'Mat' in self.inputs and self.inputs['Mat'].links:
                    mat = Matrix_generate(SvGetSocketAnyType(self, self.inputs['Mat']))
                else:
                    mat = [Matrix. Identity(4)]
                mat_iter = repeat_last(mat)

                def f(axis, q):
                    if axis.dot(q.axis) > 0:
                        return q.angle
                    else:
                        return -q.angle

                for v, p, m in zip(Vector_generate(verts), poly_edge, mat_iter):
                    axis = m * Vector((0, 0, 1))
                    axis_norm = m * Vector((1, 0, 0))
                    base_point = m * Vector((0, 0, 0))
                    intersect_d = [intersect_point_line(v_c, base_point, axis) for v_c in v]
                    rotate_d = [f(axis, (axis_norm+v_l[0]).rotation_difference(v_c)) for v_c, v_l in zip(v, intersect_d)]
                    s_v = ((data[0][1], data[1], i) for i, data in enumerate(zip(intersect_d, rotate_d)))
                    s_v = sorted(s_v, key=itemgetter(0, 1))

                    verts_out.append([v[i[-1]].to_tuple() for i in s_v])

                    if polyOutput:
                        v_index = {item[-1]: j for j, item in enumerate(s_v)}
                        poly_edge_out.append([list(map(lambda n:v_index[n], pe)) for pe in p])
                    if orderOutput:
                        item_order.append([i[-1] for i in s_v])

            if self.mode == 'USER':
                if 'Index Data' in self.inputs and self.inputs['Index Data'].links:
                    index = SvGetSocketAnyType(self, self.inputs['Index Data'])
                else:
                    return

                for v, p, i in zip(verts, poly_edge, index):

                    s_v = sorted([(data[0], data[1], i) for i, data in enumerate(zip(i, v))], key=itemgetter(0))

                    verts_out.append([obj[1] for obj in s_v])

                    if polyOutput:
                        v_index = {item[-1]: j for j, item in enumerate(s_v)}
                        poly_edge_out.append([[v_index[k] for k in pe] for pe in p])
                    if orderOutput:
                        item_order.append([i[-1] for i in s_v])

            if vertOutput:
                SvSetSocketAnyType(self, 'Vertices', verts_out)
            if polyOutput:
                SvSetSocketAnyType(self, 'PolyEdge', poly_edge_out)
            if orderOutput:
                SvSetSocketAnyType(self, 'Item order', item_order)

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(SvVertSortNode)


def unregister():
    bpy.utils.unregister_class(SvVertSortNode)
