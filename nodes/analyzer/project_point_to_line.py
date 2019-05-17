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

import numpy as np
from bisect import bisect
from functools import reduce

import bpy
from bpy.props import IntProperty, EnumProperty, BoolProperty, FloatProperty
from mathutils import kdtree, Vector

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import get_other_socket, updateNode, replace_socket, match_long_repeat
from sverchok.data_structure import match_long_repeat

'''
Some explanation of the algorithm can be found here:
https://github.com/nortikin/sverchok/issues/2376
'''


# _________useful functions_________
def is_instance_of_vector(l):
    # Check first nested bunch of coordinates is Vector class or not
    def get_last_iterable_class(l):
        if hasattr(l, '__getitem__'):
            res = get_last_iterable_class(l[0])
            if isinstance(res, bool):
                return type(l)
            else:
                return res
        else:
            return False
    return get_last_iterable_class(l) == Vector


def calc_nestedness(l, deap=0):
    if isinstance(l, (list, tuple)):
        return calc_nestedness(l[0], deap + 1)
    return deap


def flatten_list(l, a=None):
    # make list of lists flatten
    # https://github.com/nortikin/sverchok/issues/2304#issuecomment-438581948
    if a is None:
        a = []
    add = a.append

    _ = [flatten_list(i, a) if isinstance(i, (list, tuple)) else add(i) for i in l]
    return a


# functions related with main process
def creat_tree(line):
    # Create KDTree for line
    tree = kdtree.KDTree(len(line))
    [tree.insert(p, i) for i, p in enumerate(line)]
    tree.balance()
    return tree


def get_closerst_point(tree, points):
    """
    Will find closest line's point to current points
    :param tree:  mathutils.kdtree.KDTree
    :param points: [point 1, point 2, ...]
    point - Vector or (x, y, z)
    :return: indexes of closest points in KDTree to points - [int 1, int 2, ...]
    len(points) == len(inds)
    """
    data = [tree.find(point) for point in points]
    cos, inds, dists = zip(*data)
    return inds


def get_closest_point_to_edge(edge, point):
    """
    Will find closest point on current edge
    :param edge: [Vector 1, Vector 2]
    :param point: Vector
    :return project_point_inside_edge: Vector
    :return coincidence: coincidence projected point with one of points of the edge - bool
    """
    edge_vector = edge[1] - edge[0]
    point = point - edge[0]
    project_point = point.project(edge_vector)
    scalar_mult = project_point.dot(edge_vector)
    if scalar_mult < 0:
        project_point_inside_edge = edge[0]
        coincidence = True
    elif project_point.length > edge_vector.length:
        project_point_inside_edge = edge[1]
        coincidence = True
    else:
        project_point_inside_edge = project_point + edge[0]
        coincidence = False
    return project_point_inside_edge, coincidence


def get_len_edges_line(line):
    # Return  lengths of line's edges
    return [(v2 - v1).length for v1, v2 in zip(line[:-1], line[1:])]


def get_divvec_edge(edge, div_number):
    """
    Return points on given edge created by subdivision
    :param edge: [Vector 1, Vector 2]
    :param div_number: on how many parts edge should be divided - int
    :return: [Vector div_1, Vector div_2, ...]
    """
    factors = np.linspace(0, 1, num=div_number + 2)[1:-1]
    return [edge[0].lerp(edge[1], f) for f in factors]


def divide_line(line, resolution, len_edges):
    """
    Divide line to smaller edges with equal length
    :param line: [Vector 1, Vector 2, ...]
    :param resolution: means maximum length of an edge. If edge is longer it should be divided - float
    :param len_edges: distance between vector 1 and 2, vector 2 and 3 and so on - [float 1, float 2, ...]
    len(line) - 1 == len(len_edges)
    :return new_line: [Vector 1, Vector 1.1, Vector 1.2, Vector 2, Vector 2.1, ...]
    :return edge_indexes: index of position of Vectors from old line on new line - [int1, int2, ...]
    for example, if last vector of an edge has index 1 and this edge is divided on 3 parts new index of last Vector is 3
    """
    len_edges = len_edges if len_edges else get_len_edges_line(line)
    new_line = [line[0]]
    edge_indexes = [0]
    indx = 1
    for (p1, p2), len_e in zip(zip(line[:-1], line[1:]), len_edges):
        div_number = round(len_e / resolution) - 1
        if div_number > 0:
            new_line.extend(get_divvec_edge((p1, p2), div_number))
            indx += div_number

        new_line.append(p2)
        edge_indexes.append(indx)
        indx += 1
    return new_line, edge_indexes


def preparing_lines(vectors_line, resolution=False):
    # Subdivide and create KDTree for given lines
    if not is_instance_of_vector(vectors_line):
        vectors_line = [[Vector(co) for co in l] for l in vectors_line]
    lens_edges = [get_len_edges_line(line) for line in vectors_line]
    if resolution:
        resolution = resolution if calc_nestedness(resolution) == 1 else flatten_list(resolution)
    else:
        resolution = [min(lens) for lens in lens_edges]
    new_lines, edges_indexes = zip(*[divide_line(line, r, len_e)
                               for line, len_e, r in zip(*match_long_repeat([vectors_line, lens_edges, resolution]))])
    trees = [creat_tree(line) for line in new_lines]
    return new_lines, edges_indexes, trees


def find_closest_index(edges_index, ind):
    """
    find 3 closest indexes of points exist in initial line
    :param edges_index: index of position of Vectors from old line on new line - [int1, int2, ...]
    for example, if last vector of an edge has index 1 and this edge is divided on 3 parts new index of last Vector is 3
    :param ind: index of closest point on new line to project point - int
    :return new_3ind: indexes of closest 3 points exist on old line that correspond to new line - [int1, int2, int3]
    :return old_3ind: indexes of closest 3 points exist on old line that correspond to old line - [int1, int2, int3]
    """
    i = bisect(edges_index, ind)
    # print('edges -', edges_index)
    # print('i -', i)
    if i == len(edges_index):
        new_3ind = edges_index[i - 3], edges_index[i - 2], edges_index[i - 1]
        old_3ind = [i - 3, i - 2, i - 1]
    elif i - 1 == 0:
        new_3ind = edges_index[i - 1], edges_index[i], edges_index[i + 1]
        old_3ind = [i - 1, i, i + 1]
    else:
        new_3ind = edges_index[i - 2], edges_index[i - 1], edges_index[i]
        old_3ind = [i - 2, i - 1, i]
    return new_3ind, old_3ind


def project_points(new_lines, edges_indexes, kdtrees_from_lines, pr_points):
    """
    project points to prepared lines
    :param new_lines: prepared lines - [[Vector 1, Vector 2, ...], [Vector 1, ...], ...]
    :param edges_indexes: indexes of points of new line that exist on old line -[[int 1, int 2, ...], [int 1, ...], ...]
    :param kdtrees_from_lines: KD trees prepared from new_lines - [KDTree 1, KDTree 2, ...]
    :param pr_points: points that should be projected - [[Vector 1, Vector 2, ...], [Vector 1, ...], ...]
    vector can be a list of 3 numbers
    :return project_points: [[Vector 1, Vector 2, ...], [Vector 1, ...], ...]
    :return old_indexes: index of point of old line that located before projected point ->
                         -> [[int 1, int 2, ...], [int 1, ...], ...]
    :return coincidence: coincidence projected points with points of old line - [[False, True, ...], [False, ...], ...]
    """
    if not is_instance_of_vector(new_lines):
        vectors_line = [[Vector(co) for co in l] for l in new_lines]
    if not is_instance_of_vector(pr_points):
        pr_points = [[Vector(co) for co in l] for l in pr_points]

    clos_ind = [get_closerst_point(tree, points) for tree, points in zip(kdtrees_from_lines, pr_points)]

    project_points = []
    old_indexes = []
    coincidence = []
    for line, inds, points, edges_ind in zip(new_lines, clos_ind, pr_points, edges_indexes):
        project_points_nest1 = []
        old_indexes_nest1 = []
        coincidence_nest1 = []
        for ind, point in zip(inds, points):
            (new_i1, new_i2, new_i3), (old_i1, old_i2, old_i3) = find_closest_index(edges_ind, ind)
            clos_p1, coincidence_p1 = get_closest_point_to_edge((line[new_i1], line[new_i2]), point)
            clos_p2, coincidence_p2 = get_closest_point_to_edge((line[new_i2], line[new_i3]), point)
            if clos_p1 - point < clos_p2 - point:
                project_points_nest1.append(clos_p1)
                old_indexes_nest1.append(old_i1)
                coincidence_nest1.append(coincidence_p1)
            else:
                project_points_nest1.append(clos_p2)
                old_indexes_nest1.append(old_i2)
                coincidence_nest1.append(coincidence_p2)
        project_points.append(project_points_nest1)
        old_indexes.append(old_indexes_nest1)
        coincidence.append(coincidence_nest1)

    return project_points, old_indexes, coincidence


def sort_points_along_line(line, points, position, replace):
    # sort points in order how how they move from start of line to end
    points, position, replace = zip(*sorted(zip(points, position, replace), key=lambda l: l[1]))
    new_p, new_pos, new_rep = [], [], []
    for i in range(len(position)):
        next_i = i + 1
        while len(position) >= next_i and position[i] == position[next_i]:
            next_i += 1
        if next_i - i > 1:
            distance = [(proj - line[position[i]]).length for proj in points[i:next_i]]
            chunk_dist, chunk_p, chunck_pos, chunk_rep = zip(*sorted(
                                                         zip(distance, points, position, replace), key=lambda l: l[0]))
            new_p.append(chunk_p)
            new_pos.append(chunck_pos)
            new_rep.append(chunk_rep)
        else:
            new_p.append(points[i])
            new_pos.append(position[i])
            new_rep.append(replace[i])
    return new_p, new_pos, new_rep


def integrate_points_to_line(line, points, position, replace):
    """
    merge projected points with old line
    :param line: points of old line - [Point 1, Point 2, ...]
    :param points: projected points that should be merged - [Point 1, Point 2, ...]
    :param position: indexes of points of old line after which projected points should be pasted - [int1, int2, ...]
    :param replace: if projected points coincide with existing points of old line they should replace them ->
                    -> [False, True, False, ...]
    order of lists (points, position and replace) should be related with each other
    :return:
    """
    points, position, replace = sort_points_along_line(line, points, position, replace)
    last_pos = 0
    merged_line = []
    number_added_points = 0  # of input line
    for i, p in enumerate(points):
        if last_pos == position[i]:  # position didn't not move
            if replace[i]:
                pass
            else:
                if last_pos <= number_added_points:  # position didn't move first time
                    merged_line.append(line[last_pos:position[i]+1])
                    number_added_points += position[i] + 1 - last_pos
        else:  # position moved
            if replace[i]:
                merged_line.append([line[last_pos:position[i]]])
            else:
                merged_line = [line[position[0] + 1]]

        last_pos = position[i]


class SvProjectPointToLine(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: project point to line
    Tooltip: project point to line

    You can do something
    """
    bl_idname = 'SvProjectPointToLine'
    bl_label = 'Project point to line'
    bl_icon = 'MOD_SHRINKWRAP'

    def switch_res_mode(self, context):
        if self.set_res:
            self.inputs.new('StringsSocket', 'Resolution').prop_name = 'resolution'
        else:
            self.inputs.remove(self.inputs['Resolution'])
        self.process_node(context)

    resolution = FloatProperty(name='resolution',
                               description='the less the more accurate',
                               default=1.0,
                               min=0.01,
                               step=10,
                               unit='LENGTH',
                               update=SverchCustomTreeNode.process_node)

    set_res = BoolProperty(name='Set resolution',
                          description='Add socket for setting resolution value',
                          default=False,
                          update=switch_res_mode)

    def sv_init(self, context):
        self.inputs.new('VerticesSocket', 'Vectors_lines')
        self.inputs.new('VerticesSocket', 'Project_points')
        self.outputs.new('VerticesSocket', 'Points_projected')
        self.outputs.new('StringsSocket', 'Belonging')

    def draw_buttons_ext(self, context, layout):
        layout.row().prop(self, 'set_res', toggle=True)

    def process(self):
        if not (self.inputs['Vectors_lines'].is_linked and self.inputs['Project_points'].is_linked):
            return

        v_lines = self.inputs['Vectors_lines'].sv_get()
        p_points = self.inputs['Project_points'].sv_get()
        if self.set_res:
            resn = self.inputs['Resolution'].sv_get()
        else:
            resn = False

        new_lines, edges_indexes, trees = preparing_lines(v_lines, resn)
        projected_points, indexes, coincidence = project_points(new_lines, edges_indexes, trees, p_points)

        self.outputs['Points_projected'].sv_set([[v[:] for v in l] for l in projected_points])
        self.outputs['Belonging'].sv_set([[[i] if c else (i, i+1) for i, c in zip(ind, coin)]
                                          for ind, coin in zip(indexes, coincidence)])


def register():
    bpy.utils.register_class(SvProjectPointToLine)


def unregister():
    bpy.utils.unregister_class(SvProjectPointToLine)
