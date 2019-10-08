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

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.avl_tree import AVLTree


x, y, z = 0, 1, 2
global_event_point = None


def cross_product(v1, v2):
    """
    Cross product of two any dimension vectors
    :param v1: any massive
    :param v2: any massive
    :return: list
    """
    out = []
    l = len(v1)
    for i in range(l):
        out.append(v1[(i + 1) % l] * v2[(i + 2) % l] - v1[(i + 2) % l] * v2[(i + 1) % l])
    return out


def convert_homogeneous_to_cartesian(v):
    """
    Convert from homogeneous to cartesian system coordinate
    :param v: massive of any length
    :return: list
    """
    w = v[-1]
    out = []
    for s in v[:-1]:
        out.append(s / w)
    return out


def intersect_lines_2d(a1, a2, b1, b2):
    """
    Find intersection of two lines determined by two coordinates
    :param a1: point 1 of line a - any massive
    :param a2: point 2 of line a - any massive
    :param b1: point 1 of line b - any massive
    :param b2: point 2 of line b - any massive
    :return: returns intersection point (list) if lines are not parallel else returns False
    """
    cross_a = cross_product((a1[x], a1[y], 1), (a2[x], a2[y], 1))
    cross_b = cross_product((b1[x], b1[y], 1), (b2[x], b2[y], 1))
    hom_v = cross_product(cross_a, cross_b)
    if hom_v[2] != 0:
        return convert_homogeneous_to_cartesian(hom_v)
    elif not any(hom_v):
        return False  # two lines ara overlaping
    else:
        return False  # two lines are parallel


def dot_product(v1, v2):
    """
    Calculate dot product of two vectors
    :param v1: massive of any length
    :param v2: massive of any length
    :return: float
    """
    out = 0
    for i in range(len(v1)):
        out += v1[i] * v2[i]
    return out


def almost_equal(v1, v2, epsilon=1e-5):
    """
    Compare floating values
    :param v1: int, float
    :param v2: int, float
    :param epsilon: value of accuracy
    :return: True if values are equal else False
    """
    return abs(v1 - v2) < epsilon


def is_ccw(a, b, c):
    """
    Tests whether the turn formed by A, B, and C is counter clockwise
    :param a: 2d point - any massive
    :param b: 2d point - any massive
    :param c: 2d point - any massive
    :return: True if turn is counter clockwise else False
    """
    return (b[x] - a[x]) * (c[y] - a[y]) > (b[y] - a[y]) * (c[x] - a[x])


def is_edges_intersect_2d(a1, b1, a2, b2):
    """
    Returns True if line segments a1b1 and a2b2 intersect
    If point of one edge lays on another edge this recognize like intersection
    :param a1: first 2d point of fist segment - any massive
    :param b1: second 2d point of fist segment - any massive
    :param a2: first 2d point of second segment - any massive
    :param b2: second 2d point of second segment - any massive
    :return: True if edges are intersected else False
    """
    return ((is_ccw(a1, b1, a2) != is_ccw(a1, b1, b2) or is_ccw(b1, a1, a2) != is_ccw(b1, a1, b2)) and
            (is_ccw(a2, b2, a1) != is_ccw(a2, b2, b1) or is_ccw(b2, a2, a1) != is_ccw(b2, a2, b1)))


class EdgeSweepLine:
    # Special class for storing in status data structure

    def __init__(self, v1, v2, i1, i2):
        self.v1 = v1
        self.v2 = v2
        self.i1 = i1
        self.i2 = i2

        self.last_event = None
        self.last_intersection = None
        self.last_product = None

        self.cross = cross_product((self.v1[x], self.v1[y], 1), (self.v2[x], self.v2[y], 1))
        self.up_i = self.i1 if self.get_low_index() == 1 else self.i2
        self.low_i = self.i2 if self.up_i == self.i1 else self.i1
        self.up_v = self.v1 if self.get_low_index() == 1 else self.v2
        self.low_v = self.v1 if self.get_low_index() == 0 else self.v2
        self.is_horizontal = self.up_v[y] == self.low_v[y]
        self.direction = self.get_direction()

    def __str__(self):
        return 'Edge({}, {})'.format(self.i1, self.i2)

    def __lt__(self, other):
        #debug("~~~~~~~~Start to compare {} < {}".format(self, other))
        # when edge are inserting to the three
        if isinstance(other, EdgeSweepLine):
            # if two edges intersect in one point less edge will be with bigger angle with X coordinate
            if almost_equal(self.intersection, other.intersection):
                #debug("Edges are equal, self angle: {} < other angle: {}".format(self.product, other.product))
                if almost_equal(self.product, other.product):
                    # two edges are overlapping each other, oder is does not matter
                    # input can have equal edges, this algorithm will take in account only one of them
                    return True if (self.i1, self.i2) not in [(other.i1, other.i2), (other.i2, other.i1)] else False
                else:
                    return self.product < other.product
            else:
                #debug("Self.intersection: {} < other.intersection: {}".format(self.intersection, other.intersection))
                return self.intersection < other.intersection
        # this part is for searching edges by value of x coordinate of event point
        else:
            #debug("Edge is compared with value {}, intersection: {} < {}".format(self, self.intersection, other))
            if almost_equal(self.intersection, other):
                #debug("Edge and value are equal")
                return False
            else:
                #debug("Edge < value ?")
                return self.intersection < other

    def __gt__(self, other):
        #debug("~~~~~~~~~Start to compare {} > {}".format(self, other))
        # when edge are inserting to the three
        if isinstance(other, EdgeSweepLine):
            # if two edges intersect in one point bigger edge will be with less angle with X coordinate
            if almost_equal(self.intersection, other.intersection):
                # debug("Edges are equal, self angle: {} > other angle: {}".format(self.product, other.product))
                if almost_equal(self.product, other.product):
                    # two edges are overlapping each other, oder is does not matter
                    # input can have equal edges, this algorithm will take in account only one of them
                    return True if (self.i1, self.i2) not in [(other.i1, other.i2), (other.i2, other.i1)] else False
                else:
                    return self.product > other.product
            else:
                #debug("Self.intersection: {} > other.intersection: {}".format(self.intersection, other.intersection))
                return self.intersection > other.intersection
        # this part is for searching edges by value of x coordinate of event point
        else:
            #debug("Edge is compared with value {}, intersection: {} > {}".format(self, self.intersection, other))
            if almost_equal(self.intersection, other):
                #debug("Edge and value are equal")
                return False
            else:
                #debug("Edge < value ?")
                return self.intersection > other

    @property
    def intersection(self):
        # find intersection current edge with sweeping line
        if self.is_horizontal:
            return self.event_point[x]
        if self.event_point != self.last_event:
            self.update_params()
        return self.last_intersection

    @property
    def product(self):
        # if edges has same point of intersection with sweep line they are sorting by angle to sweep line
        if self.is_horizontal:
            # if inserting edge is horizontal it always bigger for storing it to the end of sweep line
            return 1
        if self.event_point != self.last_event:
            self.update_params()
        return self.last_product

    def update_params(self):
        # when new event point some parameters should be recalculated
        self.last_intersection = (self.event_point[y] * self.cross[y] + self.cross[z]) / -self.cross[x]
        self.last_product = dot_product(self.direction, (1, 0))
        self.last_event = self.event_point

    def get_low_index(self):
        # find index in edge of index of lowest point
        if self.v1[y] > self.v2[y]:
            out = 1
        elif self.v1[y] < self.v2[y]:
            out = 0
        else:
            if self.v1[x] < self.v2[x]:
                out = 1
            else:
                out = 1
        return out

    @property
    def is_c(self):
        # returns True if current event point is intersection point of current edge
        return not (almost_equal(self.low_v[x], self.event_point[x]) and
                    almost_equal(self.low_v[y], self.event_point[y]))

    @property
    def event_point(self):
        # get actual event point
        if isinstance(global_event_point, (list, tuple)):
            return global_event_point
        else:
            raise Exception('Sweep line should be initialized before')

    def get_direction(self):
        # get downward direction of edge
        vector = (self.low_v[x] - self.up_v[x], self.low_v[y] - self.up_v[y])
        v_len = (vector[x] ** 2 + vector[y] ** 2) ** 0.5
        return (vector[x] / v_len, vector[y] / v_len)


class EventPoint:
    # Special class for storing in queue data structure

    def __init__(self, co, index):
        self.co = co
        self.index = index
        self.up_edges = []

    def __str__(self):
        return "({:.1f}, {:.1f})".format(self.co[x], self.co[y])

    def __lt__(self, other):
        # Sorting of points from upper left point to lowest right point
        if almost_equal(self.co[x], other.co[x]) and almost_equal(self.co[y], other.co[y]):
            return False
        else:
            return (-self.co[y], self.co[x]) < (-other.co[y], other.co[x])

    def __gt__(self, other):
        # Sorting of points from upper left point to lowest right point
        if almost_equal(self.co[x], other.co[x]) and almost_equal(self.co[y], other.co[y]):
            return False
        else:
            return (-self.co[y], self.co[x]) > (-other.co[y], other.co[x])


def get_coincidence_edges(tree, x_position):
    """
    Get from status all edges and their neighbours which go through event point
    :param tree: status data structure - AVLTree
    :param x_position: x position of event point
    :return: tuple(left neighbour, adjacent edges, right neighbour) - (AVL node, [AVL node, ...], AVL node)
    """
    start_node = tree.find(x_position)
    right_part = [start_node] if start_node else []
    left_part = []
    adjacent_right = None
    adjacent_left = None

    next_node = start_node
    while next_node:
        next_node = next_node.next
        if next_node and almost_equal(next_node.key.intersection, x_position):
            right_part.append(next_node)
        elif next_node:
            adjacent_right = next_node.key
            break

    last_node = start_node
    while last_node:
        last_node = last_node.last
        if last_node and almost_equal(last_node.key.intersection, x_position):
            left_part.append(last_node)
        elif last_node:
            adjacent_left = last_node.key
            break

    return adjacent_left, left_part[::-1] + right_part, adjacent_right


def get_upper_vert(verts, edge):
    """
    Get index in edge of index upper point for given edge
    :param verts: vertex which are linked with edge - [(x, y), ...]
    :param edge: indexes to two vertexes - (5, 2)
    :return: 0 if vert[5][y] > vert[2][y] else 1
    """
    if verts[edge[0]][y] > verts[edge[1]][y]:
        upper_vert = 0
    elif verts[edge[0]][y] < verts[edge[1]][y]:
        upper_vert = 1
    else:
        if verts[edge[0]][x] < verts[edge[1]][x]:
            upper_vert = 0
        else:
            upper_vert = 1
    return upper_vert


def find_intersections(verts, edges):
    """
    Initializing of searching intersection algorithm, read Computational Geometry by Mark de Berg
    :param verts: [(x, y) or (x, y, z), ...]
    :param edges: [(1, 5), ...]
    :return: [(3d dimensional intersection point, [edge1 involved in intersection, edge2, ...]), ...]
    """
    status = AVLTree()
    event_queue = AVLTree()
    for edge in edges:
        upper_vert = get_upper_vert(verts, edge)
        lower_vert = (upper_vert + 1) % 2
        up_node = event_queue.insert(EventPoint(verts[edge[upper_vert]], edge[upper_vert]))
        up_node.key.up_edges += [edge]
        event_queue.insert(EventPoint(verts[edge[lower_vert]], edge[lower_vert]))
    # event_queue = AVLTree([(co[y], co[x]) for co in v])
    # print(event_queue.as_list(0))
    out = []
    while event_queue:
        event_node = event_queue.find_smallest()
        intersection = handle_event_point(status, event_queue, event_node.key, verts)
        if intersection:
            out.append(intersection)
        event_queue.remove_node(event_node)
    return out


def handle_event_point(status, event_queue, event_point, verts):
    # Read Computational Geometry by Mark de Berg
    global global_event_point
    # print(event_point.index)
    global_event_point = event_point.co
    left_neighbor, coincidence, right_neighbor = get_coincidence_edges(status, event_point.co[x])
    # print(adjacent_left, '-', *[node for node in intersected], '-', adjacent_right)
    c = [node for node in coincidence if node.key.is_c]
    l = [node for node in coincidence if not node.key.is_c]
    # print('c -', *c)
    # print('l -', *l)
    [status.remove_node(node) for node in c]
    [status.remove_node(node) for node in l]
    u = [status.insert(EdgeSweepLine(verts[edge[0]], verts[edge[1]], edge[0], edge[1]))
         for edge in event_point.up_edges]
    c = [status.insert(node.key) for node in c]
    if not any(u + c):
        if left_neighbor and right_neighbor:
            find_new_event(left_neighbor, right_neighbor, event_queue, event_point)
    else:
        leftmost_node = min([node for node in u + c], key=lambda node: node.key)
        rightmost_node = max([node for node in u + c], key=lambda node: node.key)
        left_neighbor = leftmost_node.last
        right_neighbor = rightmost_node.next
        #print('leftmost_node', leftmost_node)
        #print('rightmost_node', rightmost_node)
        #print('left_neighbor', left_neighbor)
        #print('right_neighbor', right_neighbor)
        if left_neighbor:
            find_new_event(leftmost_node.key, left_neighbor.key, event_queue, event_point)
        if right_neighbor:
            find_new_event(rightmost_node.key, right_neighbor.key, event_queue, event_point)
    #print(status.out())
    if c or len(set([node.key.up_i for node in u] + [node.key.low_i for node in l])) > 1:
        point = tuple(list(event_point.co) + [0]) if len(event_point.co) == 2 else tuple(event_point.co)
        edges = [(node.key.i1, node.key.i2) for node in u + c + l]
        return point, edges


def find_new_event(edge1, edge2, event_queue, event_point):
    # Read Computational Geometry by Mark de Berg
    if is_edges_intersect_2d(edge1.v1, edge1.v2, edge2.v1, edge2.v2):
        intersection = intersect_lines_2d(edge1.v1, edge1.v2, edge2.v1, edge2.v2)
        if intersection:
            new_event_point = EventPoint(intersection, None)
            if new_event_point > event_point:
                event_queue.insert(new_event_point)


class SvIntersectEdges2D(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Intersect edges 2d
    Returns information about intersection points only, if such exists

    Better performance is with large number of edges and small number of intersection
    """
    bl_idname = 'SvIntersectEdges2D'
    bl_label = 'Intersect edges 2D'
    sv_icon = 'SV_XALL'

    def sv_init(self, context):
        self.inputs.new('VerticesSocket', 'Verts')
        self.inputs.new('StringsSocket', 'Edges')
        self.outputs.new('VerticesSocket', 'Intersections')
        self.outputs.new('StringsSocket', 'Involved edges')

    def process(self):
        if not all([sock.is_linked for sock in self.inputs]) and not any([sock.is_linked for sock in self.outputs]):
            return

        verts = []
        edges = []
        for v_obj, e_obj in zip(self.inputs['Verts'].sv_get(), self.inputs['Edges'].sv_get()):
            intersection = find_intersections(v_obj, e_obj)
            if intersection:
                co, edg = zip(*intersection)
                verts.append(co)
                edges.append(edg)

        self.outputs['Intersections'].sv_set(verts)
        self.outputs['Involved edges'].sv_set(edges)


classes = [SvIntersectEdges2D]


def register():
    [bpy.utils.register_class(cl) for cl in classes]


def unregister():
    [bpy.utils.unregister_class(cl) for cl in classes]
