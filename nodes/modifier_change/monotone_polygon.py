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


from itertools import zip_longest

import bpy

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.avl_tree import AVLTree


x, y, z = 0, 1, 2


def is_ccw(a, b, c):
    """
    Tests whether the turn formed by A, B, and C is counter clockwise
    :param a: 2d point - any massive
    :param b: 2d point - any massive
    :param c: 2d point - any massive
    :return: True if turn is counter clockwise else False
    """
    return (b[x] - a[x]) * (c[y] - a[y]) > (b[y] - a[y]) * (c[x] - a[x])


def is_ccw_polygon(verts):
    """
    Returns True if order of points are in counterclockwise
    :param all_verts: [(x, y, z) or (x, y), ...]
    :return: bool
    """
    x_min = min(range(len(verts)), key=lambda i: verts[i][x])
    return True if is_ccw(verts[(x_min - 1) % len(verts)], verts[x_min], verts[(x_min + 1) % len(verts)]) else False


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


def almost_equal(v1, v2, epsilon=1e-6):
    """
    Compare floating values
    :param v1: int, float
    :param v2: int, float
    :param epsilon: value of accuracy
    :return: True if values are equal else False
    """
    return abs(v1 - v2) < epsilon


def is_less(v1, v2, epsilon=1e-6):
    """
    Compare floating values
    :param v1: float
    :param v2: float
    :param epsilon: value of accuracy
    :return: True if v1 is less then v2
    """
    return v2 - v1 > epsilon


def is_more(v1, v2, epsilon=1e-6):
    """
    Compare floating values
    :param v1: float
    :param v2: float
    :param epsilon: value of accuracy
    :return: True if v1 is more then v2
    """
    return v1 - v2 > epsilon


class EdgeSweepLine:
    # Special class for storing in status data structure
    global_event_point = None

    def __init__(self, outer_hedge):
        self.hedge = outer_hedge
        self.helper = None

        self.last_event = None
        self.last_intersection = None

        self.cross = cross_product((self.hedge.origin.co[x], self.hedge.origin.co[y], 1),
                                   (self.hedge.twin.origin.co[x], self.hedge.twin.origin.co[y], 1))
        self.is_horizontal = almost_equal(self.hedge.origin.co[y], self.hedge.twin.origin.co[y])

    def __str__(self):
        return 'E_{},{}'.format(self.hedge.origin, self.hedge.twin.origin)

    def __lt__(self, other):
        # when edge are inserting to the three
        if isinstance(other, EdgeSweepLine):
            # there are should not be edges which intersect in one event point
            return self.intersection < other.intersection

        # this part is for searching edges by value of x coordinate of event point
        else:
            return self.intersection < other

    def __gt__(self, other):
        # when edge are inserting to the three
        if isinstance(other, EdgeSweepLine):
            # there are should not be edges which intersect in one event point
            return self.intersection > other.intersection

        # this part is for searching edges by value of x coordinate of event point
        else:
            return self.intersection > other

    @property
    def intersection(self):
        # find intersection current edge with sweeping line
        if self.is_horizontal:
            return self.event_point.co[x]
        if self.event_point != self.last_event:
            self.update_params()
        return self.last_intersection

    def update_params(self):
        # when new event point some parameters should be recalculated
        self.last_intersection = (self.event_point.co[y] * self.cross[y] + self.cross[z]) / -self.cross[x]
        self.last_event = self.event_point
        #print_e(self, 'intersection -{}'.format(self.last_intersection))

    @property
    def event_point(self):
        # get actual event point
        if EdgeSweepLine.global_event_point is not None:
            return EdgeSweepLine.global_event_point
        else:
            raise Exception('Sweep line should be initialized before')


class Point:
    # Special class for storing in queue data structure
    number = 0

    def __init__(self, co):
        self.co = co
        Point.number += 1

        self.hedge = None  # always outer
        self._type = None

    def __str__(self):
        return "P_x({:.1f}), y({:.1f})".format(self.co[x], self.co[y])

    def __lt__(self, other):
        # Sorting of points from upper left point to lowest right point
        if is_less(-self.co[y], -other.co[y]):
            return True
        elif is_more(-self.co[y], -other.co[y]):
            return False
        elif is_less(self.co[x], other.co[x]):
            return True
        else:
            return False

    def __gt__(self, other):
        # Sorting of points from upper left point to lowest right point
        if is_more(-self.co[y], -other.co[y]):
            return True
        elif is_less(-self.co[y], -other.co[y]):
            return False
        elif is_more(self.co[x], other.co[x]):
            return True
        else:
            return False

    @property
    def type(self):
        # returns type of point according the algorithm
        #print_p(self, 'center')
        if not self._type:
            next_point = self.hedge.next.origin
            last_point = self.hedge.twin.next.twin.origin
            is_up_next = next_point < self  # the less point the upper it is
            is_up_last = last_point < self
            if not is_up_next and not is_up_last:
                self._type = 'start' if self.hedge < self.hedge.twin.next else 'split'
            elif is_up_last and is_up_next:
                self._type = 'merge' if self.hedge > self.hedge.twin.next else 'end'
            else:
                self._type = 'regular'
        return self._type

    def get_ccw_hedges(self):
        # returns half edges around the point in counterclockwise direction
        hedges = [self.hedge]
        last_hedge = self.hedge.last.twin
        count = 0
        while last_hedge != self.hedge:
            hedges.append(last_hedge)
            last_hedge = last_hedge.last.twin
            count += 1
            if count > Point.number:
                raise RecursionError('Point {}, consists hedge '
                                     'which has wrong links to other neighbours'.format(self.co))
        return hedges

    def get_next_hedge(self):
        # returns next half edges according the algorithm
        if self.hedge.face and self.hedge.face.outer:
            return self.hedge
        next_hedge = self.hedge.twin.next
        count = 0
        while next_hedge != self.hedge:
            if next_hedge.face and next_hedge.face.outer:
                return next_hedge
            next_hedge = next_hedge.twin.next
            count += 1
            if count > Point.number:
                raise RecursionError('Point {}, consists hedge which has wrong links to other neighbours'.format(self.co))
        raise LookupError('There is no hedge with face')

    def get_last_hedge(self):
        # returns last half edges according the algorithm
        if self.hedge.last.face and self.hedge.last.face.outer:
            return self.hedge.last
        last_hedge = self.hedge.last.twin.last
        count = 0
        while last_hedge != self.hedge.last:
            if last_hedge.face and last_hedge.face.outer:
                return last_hedge
            last_hedge = last_hedge.twin.next
            count += 1
            if count > Point.number:
                raise RecursionError('Point {}, consists hedge which has wrong links to other neighbours'.format(self.co))
        raise LookupError('There is no hedge with face')


class HalfEdge:
    # http://www.holmes3d.net/graphics/dcel/
    def __init__(self, point, face=None):
        self.origin = point
        self.face = face

        self.twin = None
        self.next = None
        self.last = None
        self.edge = None
        self.cash_product = None

    def __str__(self):
        return 'H_{}'.format(self.origin)

    def __lt__(self, other):
        # if self < other other it means that direction of closer to (-1, 0) direction
        if isinstance(other, HalfEdge):
            if almost_equal(self.product, other.product):
                return False
            else:
                return self.product < other.product
        else:
            raise TypeError('unorderable types: {} < {}'.format(type(self), type(other)))

    def __gt__(self, other):
        if isinstance(other, HalfEdge):
            if almost_equal(self.product, other.product):
                return False
            else:
                return self.product > other.product
        else:
            raise TypeError('unorderable types: {} > {}'.format(type(self), type(other)))

    @property
    def product(self):
        if not self.cash_product:
            if self.twin.cash_product:
                self.cash_product = (self.twin.cash_product + 2) % 4
            else:
                vector = (self.twin.origin.co[x] - self.origin.co[x], self.twin.origin.co[y] - self.origin.co[y])
                v_len = (vector[x] ** 2 + vector[y] ** 2) ** 0.5
                norm_v = (vector[x] / v_len, vector[y] / v_len)
                product = dot_product(norm_v, (1, 0))
                product = product + 1 if self.origin < self.twin.origin else 3 - product
                #print_he(self, 'product-({})'.format(product))
                self.cash_product = product
        return self.cash_product


class Face:
    def __init__(self):
        self.outer = None
        self.inners = []

    def __str__(self):
        return 'F{}'.format(self.outer)

    @property
    def outer_hedges(self):
        if not self.outer:
            return []
        hedges = [self.outer]
        next_hedge = self.outer
        count = 0
        while True:
            next_hedge = next_hedge.next
            if next_hedge == self.outer:
                return hedges
            hedges.append(next_hedge)
            count += 1
            if count > Point.number:
                raise Exception('Face {}, consists hedge which has wrong links to other neighbours'.format(self.outer))


def create_half_edges(verts):
    # Creates half edge data structure from list ov vertices
    # todo: self intersection polygons? double repeated polygons?
    half_edges = []
    twin_hedges = []
    points = [Point(v) for v in verts] if is_ccw_polygon(verts) else [Point(v) for v in verts][::-1]
    super_face = Face()
    face = Face()
    for i in range(len(points)):
        next_i = (i + 1) % len(points)
        half_edge = HalfEdge(points[i], face)
        twin = HalfEdge(points[next_i], super_face)
        half_edge.twin = twin
        twin.twin = half_edge
        half_edges.append(half_edge)
        twin_hedges.append(twin)
        points[i].hedge = half_edge
    super_face.inners.append(half_edges[0].twin)
    face.outer = half_edges[0]
    for i in range(len(points)):
        last_hedge = half_edges[(i - 1) % len(points)]
        next_hedge = half_edges[(i + 1) % len(points)]
        half_edges[i].last = last_hedge
        half_edges[i].next = next_hedge
        half_edges[i].twin.last = next_hedge.twin
        half_edges[i].twin.next = last_hedge.twin
    return points, half_edges, [super_face, face]


def create_hedges_from_faces(verts, sv_faces):
    # Creates half edge data structure from vertices and faces of Sverchok data structure
    half_edges = dict()
    points = [Point(v) for v in verts]
    faces = []
    for sv_face in sv_faces:
        sv_face = sv_face if is_ccw_polygon([verts[i] for i in sv_face]) else sv_face[::-1]
        face = Face()
        faces.append(face)
        loop = []
        for i in range(len(sv_face)):
            pi = sv_face[i]
            next_pi = sv_face[(i + 1) % len(sv_face)]
            hedge = HalfEdge(points[pi], face)
            loop.append(hedge)
            half_edges[(pi, next_pi)] = hedge
        for i in range(len(loop)):
            next_i = (i + 1) % len(loop)
            loop[i].next = loop[next_i]
            loop[next_i].last = loop[i]
        face.outer = loop[0]
    outer_hedges = dict()
    for key in half_edges:
        hedge = half_edges[key]
        if key[::-1] in half_edges:
            hedge.twin = half_edges[key[::-1]]
        else:
            outer_edge = HalfEdge(points[key[1]])
            hedge.twin = outer_edge
            outer_edge.twin = hedge
            if key[::-1] in outer_hedges:
                raise Exception("It looks like input mesh has adjacent faces with only one common point"
                                "Handle such meshes does not implemented yet.")
            outer_hedges[key[::-1]] = outer_edge
    for key in outer_hedges:
        outer_edge = outer_hedges[key]
        next_edge = outer_edge.twin
        count = 0
        while next_edge:
            next_edge = next_edge.last.twin
            if not next_edge.face:
                break
            count += 1
            if count > len(verts):
                raise RecursionError('Edge-{} cannot find next edge'.format(key))
        outer_edge.next = next_edge
        next_edge.last = outer_edge
        #print_he(outer_edge, 'outer')
        #print_he(next_edge, 'next')
    super_face = Face()
    faces.append(super_face)
    used = set()
    for outer_hedge in outer_hedges.values():
        if outer_hedge in used:
            continue
        used.add(outer_hedge)
        super_face.inners.append(outer_hedge)
        next_hedge = outer_hedge.next
        count = 0
        while next_hedge != outer_hedge:
            used.add(next_hedge)
            next_hedge = next_hedge.next
            count += 1
            if count > len(outer_hedges):
                raise RecursionError('Edge - ({},{}) cannot make a loop'.format(outer_hedge.origin.co,
                                                                                outer_hedge.twin.origin.co))
    return points, list(half_edges.values()) + list(outer_hedges.values()), faces


def to_sv_mesh_from_faces(points, faces):
    # Crete Sverchok data structure from half edge data structure based on list of vertices and faces
    indexes = {point: i for i, point in enumerate(points)}
    sv_faces = []
    sv_verts = [point.co for point in points]
    for face in faces:
        if face.outer:
            fi = []
            for hedge in face.outer_hedges:
                fi.append(indexes[hedge.origin])
            sv_faces.append(fi)

    return sv_verts, sv_faces


def build_face_list(hedges):
    # Generate face list from list of half edges
    used = set()
    faces = []

    for hedge in hedges:
        #print_p(hedge.origin, 'next hedge {}'.format(hedge.face and not hedge.face.outer or hedge in used))
        if hedge.face and not hedge.face.outer or hedge in used:
            continue
        used.add(hedge)
        face = Face()
        hedge.face = face
        face.outer = hedge
        next_edge = hedge.next
        count = 0
        while next_edge != hedge:
            next_edge.face = face
            used.add(next_edge)
            next_edge = next_edge.next
            count += 1
            if count > len(hedges):
                raise RecursionError('Some hedge does not make a loop')
        faces.append(face)
    return faces


def add_holes(polygon_mesh, hole_faces):
    # Combine base polygon with holes
    p, he, f = 0, 1, 2
    points = polygon_mesh[p]
    half_edges = polygon_mesh[he]
    faces = polygon_mesh[f]
    outer_face = polygon_mesh[f][0] if polygon_mesh[f][0].outer else polygon_mesh[f][1]
    hole_super_face = [face for face in hole_faces if face.inners][0]
    outer_face.inners.extend(hole_super_face.inners)
    for hedge in outer_face.inners:
        #print_he(hedge)
        half_edges.append(hedge)
        points.append(hedge.origin)
        hedge.origin.hedge = hedge
        hedge.twin.last = hedge.next.twin
        hedge.next.twin.next = hedge.twin
        next_hedge = hedge.next
        while next_hedge != hedge:
            #print_he(hedge, 'next')
            next_hedge.twin.last = next_hedge.next.twin
            next_hedge.next.twin.next = next_hedge.twin
            half_edges.append(next_hedge)
            points.append(next_hedge.origin)
            next_hedge.origin.hedge = next_hedge
            next_hedge = next_hedge.next
    return points, half_edges, faces


def insert_edge(up_p, low_p):
    # insert new edge in half edge data structure during working of the partitioning algorithm
    up_hedge = HalfEdge(up_p)
    low_hedge = HalfEdge(low_p)
    up_hedge.twin = low_hedge
    low_hedge.twin = up_hedge
    up_ccw_hedges = up_p.get_ccw_hedges()
    if len(up_ccw_hedges) == 2:
        up_next = up_ccw_hedges[0]
    elif 2 < len(up_ccw_hedges) < 5:
        if up_ccw_hedges[0] > up_hedge:
            if ((up_ccw_hedges[2] < up_hedge and up_ccw_hedges[2] < up_ccw_hedges[0]) or
                    (up_ccw_hedges[2] > up_hedge and up_ccw_hedges[2] > up_ccw_hedges[0])):
                up_next = up_ccw_hedges[2]
            elif ((up_ccw_hedges[1] < up_hedge and up_ccw_hedges[1] < up_ccw_hedges[0]) or
                    (up_ccw_hedges[1] > up_hedge and up_ccw_hedges[1] > up_ccw_hedges[0])):
                up_next = up_ccw_hedges[1]
            else:
                up_next = up_ccw_hedges[0]
        else:
            #print('up_ccw[1] greater then up_hedge -', up_ccw_hedges[1] > up_hedge)
            #print_he(up_ccw_hedges, 'ccw_hedges')
            up_next = up_ccw_hedges[1] if up_ccw_hedges[0] < up_ccw_hedges[1] < up_hedge else up_ccw_hedges[0]
    else:
        raise Exception('Unexpected number of half edges in point {}'.format(up_p))
    low_ccw_hedges = low_p.get_ccw_hedges()
    if len(low_ccw_hedges) == 2:
        low_next = low_ccw_hedges[0]
    elif len(low_ccw_hedges) == 3:
        if low_ccw_hedges[0] > low_hedge:
            if ((low_ccw_hedges[0] > low_ccw_hedges[1] < low_hedge) or
                    (low_ccw_hedges[0] < low_ccw_hedges[1] > low_hedge)):
                low_next = low_ccw_hedges[1]
            else:
                low_next = low_ccw_hedges[0]
        else:
            low_next = low_ccw_hedges[1] if low_ccw_hedges[0] < low_ccw_hedges[1] < low_hedge else low_ccw_hedges[0]
    else:
        raise Exception('Unexpected number of half edges in point {}'.format(low_p))
    up_hedge.last = up_next.last
    up_hedge.next = low_next
    low_hedge.next = up_next
    low_hedge.last = low_next.last
    up_next.last.next = up_hedge
    up_next.last = low_hedge
    low_next.last.next = low_hedge
    low_next.last = up_hedge
    #print_he(up_hedge.next, 'up_next')
    #print_he(up_hedge.last, 'up_last')

    return [up_hedge, low_hedge]


def make_monotone(verts, hole_v=None, hole_f=None):
    """
    Splits polygon on monotone pieces optionally with holes
    :param verts: [[x1, y2, z1], [x2, y2, z2], ...]
    :param hole_v: [[x1, y2, z1], [x2, y2, z2], ...]
    :param hole_f: [[index1, index2, ....], [...], ...]
    :return (vertices of main polygon and vertices of holes, faces of new polygons) - in SV format
    """
    #debug_data_clear()
    points, half_edges, faces = create_half_edges(verts)
    if hole_f:
        hole_v, hole_he, hole_f = create_hedges_from_faces(hole_v, hole_f)
        points, half_edges, faces = add_holes((points, half_edges, faces), hole_f)
    status = AVLTree()
    q = sorted(points)[::-1]
    while q:
        event_point = q.pop()
        EdgeSweepLine.global_event_point = event_point
        #print([(i, p.type) for i, p in enumerate(points)])
        #print_p(event_point, 'event point {} - '.format(event_point.type))
        new_hedges = handle_functions[event_point.type](event_point, status)
        if new_hedges:
            half_edges.extend(new_hedges)
        #print_e(status.as_list(0))
    return to_sv_mesh_from_faces(points, build_face_list(half_edges))


def handle_start_point(point, status):
    # Read Computational Geometry by Mark de Berg
    edge = EdgeSweepLine(point.hedge)
    point.hedge.edge = edge
    point.hedge.twin.edge = edge
    edge.helper = point
    status.insert(edge)


def handle_end_point(point, status):
    # Read Computational Geometry by Mark de Berg
    status.remove(point.hedge.last.edge)
    helper = point.hedge.last.edge.helper
    if helper.type == 'merge':
        return insert_edge(helper, point)


def handle_split_point(point, status):
    # Read Computational Geometry by Mark de Berg
    left_node = status.find_nearest_left(point.co[x])
    new_hedges = insert_edge(left_node.key.helper, point)
    left_node.key.helper = point
    edge = EdgeSweepLine(point.hedge)
    point.hedge.edge = edge
    point.hedge.twin.edge = edge
    edge.helper = point
    status.insert(edge)
    return new_hedges


def handle_merge_point(point, status):
    # Read Computational Geometry by Mark de Berg
    #print_p(point, 'merge point')
    right_helper = point.hedge.last.edge.helper
    new_hedges = []
    if right_helper.type == 'merge':
        new_hedges.extend(insert_edge(right_helper, point))
    status.remove(point.hedge.twin.next.edge)
    left_node = status.find_nearest_left(point.co[x])
    left_helper = left_node.key.helper
    if left_helper.type == 'merge':
        new_hedges.extend(insert_edge(left_helper, point))
    left_node.key.helper = point
    return new_hedges


def handle_regular_point(point, status):
    # Read Computational Geometry by Mark de Berg
    if point < point.hedge.twin.origin:
        right_helper = point.hedge.last.edge.helper
        status.remove(point.hedge.last.edge)
        edge = EdgeSweepLine(point.hedge)
        point.hedge.edge = edge
        point.hedge.twin.edge = edge
        edge.helper = point
        status.insert(edge)
        if right_helper.type == 'merge':
            return insert_edge(right_helper, point)
    else:
        left_node = status.find_nearest_left(point.co[x])
        left_helper = left_node.key.helper
        left_node.key.helper = point
        if left_helper.type == 'merge':
            return insert_edge(left_helper, point)


handle_functions = {'start': handle_start_point, 'end': handle_end_point, 'split': handle_split_point,
                    'merge': handle_merge_point, 'regular': handle_regular_point}


debug_data = []
debug_count = 0


def print_p(point, msg=None):
    global debug_count
    print('{} {}'.format(msg or 'Point', debug_count))
    debug_count += 1
    debug_data.append([point.co])


def print_e(edge, msg=None):
    global debug_count
    if not isinstance(edge, list):
        edge = [edge]
    for e in edge:
        print('{} {}'.format(msg or 'Edge', debug_count))
        debug_count += 1
        debug_data.append([e.hedge.origin.co, e.hedge.twin.origin.co])


def print_he(hedges, msg=None):
    global debug_count
    if not isinstance(hedges, list):
        hedges = [hedges]
    for hedge in hedges:
        print('{} {}'.format(msg or 'Hedge', debug_count))
        debug_count += 1
        debug_data.append([hedge.origin.co, hedge.twin.origin.co])


def print_f(points):
    global debug_count
    print('Face {}'.format(debug_count))
    debug_count += 1
    debug_data.append([p.co for p in points])


def debug_data_clear():
    global debug_count
    debug_data.clear()
    debug_count = 0


class SvMakeMonotone(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Split face into monotone pieces
    Can spilt face with holes

    One object - one polygon
    """
    bl_idname = 'SvMakeMonotone'
    bl_label = 'Make monotone'

    def sv_init(self, context):
        self.inputs.new('VerticesSocket', 'Polygon')
        self.inputs.new('VerticesSocket', 'Hole vectors')
        self.inputs.new('StringsSocket', 'Hole polygons')
        self.outputs.new('VerticesSocket', 'Vertices')
        self.outputs.new('StringsSocket', 'Polygons')

    def process(self):
        verts = self.inputs['Polygon'].sv_get()
        mesh = []
        if self.inputs['Hole vectors'].is_linked and self.inputs['Hole polygons'].is_linked:
            hole_v = self.inputs['Hole vectors'].sv_get()
            hole_f = self.inputs['Hole polygons'].sv_get()
            for vs, hvs, hfs in zip_longest(verts, hole_v, hole_f, fillvalue=None):
                mesh.append(make_monotone(vs, hvs, hfs))
        else:
            for vs in verts:
                mesh.append(make_monotone(vs))
        if mesh:
            v, f = zip(*mesh)
            self.outputs['Vertices'].sv_set(v)
            self.outputs['Polygons'].sv_set(f)


def register():
    bpy.utils.register_class(SvMakeMonotone)


def unregister():
    bpy.utils.unregister_class(SvMakeMonotone)
