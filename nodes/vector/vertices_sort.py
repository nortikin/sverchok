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
from bpy.props import EnumProperty, BoolProperty
from mathutils import Matrix, Vector
from mathutils.geometry import intersect_point_line

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (repeat_last, Matrix_generate, Vector_generate,
                                     updateNode)


# distance between two points without sqrt, for comp only
def distK(v1, v2):
    return sum((i[0]-i[1])**2 for i in zip(v1, v2))


def pop_lower_level(a, index):
    for co in a:
        co.pop(index)


def find_limits(verts_in, edges_in):
    v_count = [[0, 0, 0] for i in range(len(verts_in))]
    limits = []
    for i, e in enumerate(edges_in):
        v_count[e[0]][0] += 1
        v_count[e[0]][1] = 0
        v_count[e[0]][2] = i
        v_count[e[1]][0] += 1
        v_count[e[1]][1] = 1
        v_count[e[1]][2] = i
    for i, v in enumerate(v_count):
        if v[0] == 1:
            limits.append((i, v[1], v[2]))
    return limits


def sort_vertices_by_connexions(verts_in, edges_in, limit_mode):

    # prepare data and arrays
    verts_out = []
    edges_out = []
    index = []

    edges_len = len(edges_in)
    edges_index = [j for j in range(edges_len)]
    edges0 = [j[0] for j in edges_in]
    edges1 = [j[1] for j in edges_in]
    edges_copy = [edges0, edges1, edges_index]

    # start point
    limiting = False
    if limit_mode:
        limits = find_limits(verts_in, edges_in)
        limiting = len(limits) > 0
    if limiting:
        ed_index = limits[0][2]
        or_side = limits[0][1]
        limits.pop(0)
    else:
        ed_index = 0
        or_side = 0  # direction of the edge

    pop_lower_level(edges_copy, ed_index)

    for j in range(edges_len):
        e = edges_in[ed_index]
        ed = []
        if or_side == 1:
            e = [e[1], e[0]]

        for side in e:
            if verts_in[side] in verts_out:
                ed.append(verts_out.index(verts_in[side]))
            else:
                verts_out.append(verts_in[side])
                ed.append(verts_out.index(verts_in[side]))
                index.append(side)

        edges_out.append(ed)
        # find next edge
        ed_index_old = ed_index
        v_index = e[1]
        if v_index in edges_copy[0]:
            k = edges_copy[0].index(v_index)
            ed_index = edges_copy[2][k]
            or_side = 0
            pop_lower_level(edges_copy, k)

        elif v_index in edges_copy[1]:
            k = edges_copy[1].index(v_index)
            ed_index = edges_copy[2][k]
            or_side = 1
            pop_lower_level(edges_copy, k)

        # if not found take next point or next limit
        if ed_index == ed_index_old and len(edges_copy[0]) > 0:
            if not limiting:
                ed_index = edges_copy[2][0]
                or_side = 0
                pop_lower_level(edges_copy, 0)
            else:
                for lim in limits:
                    if not lim[0] in index:
                        ed_index = lim[2]
                        or_side = lim[1]
                        k = edges_copy[0].index(lim[0]) if lim[0] in edges_copy[0] else edges_copy[1].index(lim[0])
                        pop_lower_level(edges_copy, k)

                        break
    # add unconnected vertices
    if len(verts_out) != len(verts_in):
        for verts, i in zip(verts_in, range(len(verts_in))):
            if verts not in verts_out:
                verts_out.append(verts)
                index.append(i)

    return verts_out, edges_out, index


# function taken from poligons_to_edges.py
def pols_edges(obj, unique_edges=False):
    out = []
    for faces in obj:
        out_edges = []
        seen = set()
        for face in faces:
            for edge in zip(face, list(face[1:]) + list([face[0]])):
                if unique_edges and tuple(sorted(edge)) in seen:
                    continue
                if unique_edges:
                    seen.add(tuple(sorted(edge)))
                out_edges.append(edge)
        out.append(out_edges)
    return out


class SvVertSortNode(bpy.types.Node, SverchCustomTreeNode):
    '''Vector sort'''
    bl_idname = 'SvVertSortNode'
    bl_label = 'Vector Sort'
    bl_icon = 'SORTSIZE'
    sv_icon = 'SV_VECTOR_SORT'

    def mode_change(self, context):
        if self.mode == 'XYZ':
            while len(self.inputs) > 2:
                self.inputs.remove(self.inputs[-1])
        if self.mode == 'DIST':
            while len(self.inputs) > 2:
                self.inputs.remove(self.inputs[-1])
            self.inputs.new('SvVerticesSocket', 'Base Point')

        if self.mode == 'AXIS':
            while len(self.inputs) > 2:
                self.inputs.remove(self.inputs[-1])
            self.inputs.new('SvMatrixSocket', 'Mat')

        if self.mode == 'CONNEX':
            while len(self.inputs) > 2:
                self.inputs.remove(self.inputs[-1])

        if self.mode == 'USER':
            while len(self.inputs) > 2:
                self.inputs.remove(self.inputs[-1])
            self.inputs.new('SvStringsSocket', 'Index Data')

        updateNode(self, [])

    modes = [("XYZ",    "XYZ", "X Y Z Sort",    1),
             ("DIST",   "Dist", "Distance",     2),
             ("AXIS",   "Axis", "Axial sort",   3),
             ("CONNEX", "Connect", "Sort by connections",   4),
             ("USER",   "User", "User defined", 10)]

    mode: EnumProperty(
        default='XYZ', items=modes, name='Mode', description='Sort Mode', update=mode_change)
    limit_mode: BoolProperty(
        default=False, name='Search for limits', description='Find discontinuities first', update=updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, "mode", expand=False)
        if self.mode == "XYZ":
            pass
        elif self.mode == "CONNEX":
            layout.prop(self, "limit_mode")

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Vertices')
        self.inputs.new('SvStringsSocket', 'PolyEdge')

        self.outputs.new('SvVerticesSocket', 'Vertices')
        self.outputs.new('SvStringsSocket', 'PolyEdge')
        self.outputs.new('SvStringsSocket', 'Item order')

    def process(self):
        verts = self.inputs['Vertices'].sv_get()

        if self.inputs['PolyEdge'].is_linked:
            poly_edge = self.inputs['PolyEdge'].sv_get()
            poly_in = True
        else:
            poly_in = False
            poly_edge = repeat_last([[]])

        verts_out = []
        poly_edge_out = []
        item_order = []

        poly_output = poly_in and self.outputs['PolyEdge'].is_linked
        order_output = self.outputs['Item order'].is_linked
        vert_output = self.outputs['Vertices'].is_linked

        if not any((vert_output, order_output, poly_output)):
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

                if poly_output:
                    v_index = {item[-1]: j for j, item in enumerate(s_v)}
                    poly_edge_out.append([list(map(lambda n:v_index[n], pe)) for pe in p])
                if order_output:
                    item_order.append([i[-1] for i in s_v])

        if self.mode == 'DIST':
            if self.inputs['Base Point'].is_linked:
                base_points = self.inputs['Base Point'].sv_get()
                bp_iter = repeat_last(base_points[0])
            else:
                bp = [(0, 0, 0)]
                bp_iter = repeat_last(bp)

            for v, p, v_base in zip(verts, poly_edge, bp_iter):
                s_v = sorted(((v_c, i) for i, v_c in enumerate(v)), key=lambda v: distK(v[0], v_base))
                verts_out.append([vert[0] for vert in s_v])

                if poly_output:
                    v_index = {item[-1]: j for j, item in enumerate(s_v)}
                    poly_edge_out.append([list(map(lambda n:v_index[n], pe)) for pe in p])
                if order_output:
                    item_order.append([i[-1] for i in s_v])

        if self.mode == 'AXIS':
            if self.inputs['Mat'].is_linked:
                mat = Matrix_generate(self.inputs['Mat'].sv_get())
            else:
                mat = [Matrix. Identity(4)]
            mat_iter = repeat_last(mat)

            def f(axis, q):
                if axis.dot(q.axis) > 0:
                    return q.angle
                else:
                    return -q.angle

            for v, p, m in zip(Vector_generate(verts), poly_edge, mat_iter):
                axis = m @ Vector((0, 0, 1))
                axis_norm = m @ Vector((1, 0, 0))
                base_point = m @ Vector((0, 0, 0))
                intersect_d = [intersect_point_line(v_c, base_point, axis) for v_c in v]
                rotate_d = [f(axis, (axis_norm + v_l[0]).rotation_difference(v_c)) for v_c, v_l in zip(v, intersect_d)]
                s_v = ((data[0][1], data[1], i) for i, data in enumerate(zip(intersect_d, rotate_d)))
                s_v = sorted(s_v, key=itemgetter(0, 1))

                verts_out.append([v[i[-1]].to_tuple() for i in s_v])

                if poly_output:
                    v_index = {item[-1]: j for j, item in enumerate(s_v)}
                    poly_edge_out.append([list(map(lambda n:v_index[n], pe)) for pe in p])
                if order_output:
                    item_order.append([i[-1] for i in s_v])

        if self.mode == 'USER':
            if self.inputs['Index Data'].is_linked:
                index = self.inputs['Index Data'].sv_get()
            else:
                return

            for v, p, i in zip(verts, poly_edge, index):

                s_v = sorted([(data[0], data[1], i) for i, data in enumerate(zip(i, v))], key=itemgetter(0))

                verts_out.append([obj[1] for obj in s_v])

                if poly_output:
                    v_index = {item[-1]: j for j, item in enumerate(s_v)}
                    poly_edge_out.append([[v_index[k] for k in pe] for pe in p])
                if order_output:
                    item_order.append([i[-1] for i in s_v])

        if self.mode == 'CONNEX':
            if self.inputs['PolyEdge'].is_linked:
                edges = self.inputs['PolyEdge'].sv_get()
                for v, p in zip(verts, edges):
                    pols = []
                    if len(p[0]) > 2:
                        pols = [p[:]]
                        p = pols_edges([p], True)[0]

                    vect_new, pol_edge_new, index_new = sort_vertices_by_connexions(v, p, self.limit_mode)
                    if len(pols) > 0:
                        new_pols = []
                        for pol in pols[0]:
                            new_pol = []
                            for i in pol:
                                new_pol.append(index_new.index(i))
                            new_pols.append(new_pol)
                        pol_edge_new = [new_pols]

                    verts_out.append(vect_new)
                    poly_edge_out.append(pol_edge_new)
                    item_order.append(index_new)

        if vert_output:
            self.outputs['Vertices'].sv_set(verts_out)
        if poly_output:
            self.outputs['PolyEdge'].sv_set(poly_edge_out)
        if order_output:
            self.outputs['Item order'].sv_set(item_order)


def register():
    bpy.utils.register_class(SvVertSortNode)


def unregister():
    bpy.utils.unregister_class(SvVertSortNode)
