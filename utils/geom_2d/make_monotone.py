# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from typing import Tuple, List, Union

from sverchok.utils.avl_tree import AVLTree
from .dcel import Point as Point_template, HalfEdge as HalfEdge_template, DCELMesh as DCELMesh_template, Face
from .sort_mesh import SortPointsUpDown, SortHalfEdgesCCW, SortEdgeSweepingAlgorithm

from .dcel_debugger import Debugger


def monotone_sv_face_with_holes(vert_face, vert_holes = None, face_holes=None, accuracy=1e-5):
    """
    Get one face in Sverhok format and splitting it into monotone pieces
    Vertices of face should be given in ordered along face indexes order
    Also it is possible to create holes in input face
    Mesh of holes should be inside face without any intersection
    :param vert_face: 
    :param face_face: 
    :param vert_holes: 
    :param face_holes: 
    :param accuracy: two floats figures are equal if their difference is lower then accuracy value, float
    :return: vertices in Sverchok format, faces in Sverchok format
    """
    Debugger.clear()
    mesh = DCELMesh(accuracy)
    mesh.from_sv_faces(vert_face, [list(range(len(vert_face)))], face_data={'main polygon': [True]})
    main_face = [face for face in mesh.faces if face.sv_data.get('main polygon', False)][0]
    if vert_holes and face_holes:
        mesh.from_sv_faces(vert_holes, face_holes, face_data={'hole': [True for _ in range(len(face_holes))]})
        for face in mesh.faces:
            if face.is_unbounded and face.inners[0].face.sv_data.get('hole', False):
                unbounded_face = face
                break
            if face.sv_data.get('hole', False):
                unbounded_face = face.outer.twin.face
                break
        print(unbounded_face)
        Debugger.print(unbounded_face, 'Unbounded face')
        main_face.inners = list(unbounded_face.inners)
        for face_hole_hedge in main_face.inners:
            face_hole_hedge.face.outer = main_face
    make_monotone(main_face)
    rebuild_face_list(mesh)
    return mesh.to_sv_mesh()


def monotone_faces_with_holes(dcel_mesh, accuracy=1e-5):
    """
    Split polygons with holes into monotone pieces of DCEL mesh data structure
    Faces already should have actual information about inner component
    :param dcel_mesh: DCELMesh
    :param accuracy: two floats figures are equal if their difference is lower then accuracy value, float
    :return: DCELMesh with split faces
    """
    is_inners = False
    for face in dcel_mesh.faces:
        if face.outer and face.inners:
            is_inners = True
            make_monotone(face, accuracy)
    if is_inners:
        rebuild_face_list(dcel_mesh)
    return dcel_mesh.to_sv_mesh()


# #############################################################################
# ########### - partitioning to monotone pieces algorithm - ###################
# #############################################################################


x, y, z = 0, 1, 2


class Point(Point_template, SortPointsUpDown):
    monotone_current_face = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._type = None
        self._monotone_face = None

    @property
    def type(self):
        # the type should be updated each time when polygon is changed in partitioning algorithm
        # during handle of polygon point does not change type
        face = self.monotone_face
        if not self._type:
            for coin_hedge in self.hedge.ccw_hedges:
                if coin_hedge.face == face:
                    hedge = coin_hedge
                    break
            next_point = hedge.next.origin
            last_point = hedge.last.origin
            is_up_next = next_point < self  # the less point the upper it is
            is_up_last = last_point < self
            if not is_up_next and not is_up_last:
                self._type = 'start' if self.hedge < self.hedge.last.twin else 'split'
            elif is_up_last and is_up_next:
                self._type = 'merge' if self.hedge > self.hedge.last.twin else 'end'
            else:
                self._type = 'regular'
        return self._type

    @property
    def monotone_face(self):
        # returns face coincidence to a point which is handling by the algorithm
        if not self.monotone_current_face:
            raise Exception('Which polygon is handling should be set before')
        elif self._monotone_face != self.monotone_current_face:
            self._monotone_face = self.monotone_current_face
            self._type = None
        return self._monotone_face


class HalfEdge(HalfEdge_template, SortHalfEdgesCCW):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.edge = None


class DCELMesh(DCELMesh_template):
    Point = Point
    HalfEdge = HalfEdge


class Edge(SortEdgeSweepingAlgorithm):

    def __init__(self, up_p, low_p):
        super().__init__(up_p, low_p)

        self.helper = None


def make_monotone(face):
    """
    Splits polygon into monotone pieces optionally with holes
    :param face: face of half edge data structure
    :return new half edges
    """
    Debugger.print(face.inners, 'inners')
    face.mesh.Point.monotone_current_face = face
    status = AVLTree()
    q = sorted(build_points_list(face))[::-1]
    print([p.type for p in q])
    while q:
        event_point = q.pop()
        Edge.global_event_point = event_point
        handle_functions[event_point.type](event_point, status, find_hedge(event_point))


def build_points_list(face):
    # build list of points for partitioning algorithm, all point of outer and inners components
    verts = []
    for hedge in face.outer.loop_hedges:
        verts.append(hedge.origin)
    for inner_hedge in face.inners:
        for hedge in inner_hedge.loop_hedges:
            verts.append(hedge.origin)
    return verts


def find_hedge(point):
    # find hedge with origin in current point and with partitioning face
    for hedge in point.hedge.ccw_hedges:
        if hedge.face == point.monotone_face:
            break
    return hedge


def rebuild_face_list(dcel_mesh):
    # rebuild face list after partition algorithm
    for hedge in dcel_mesh.hedges:
        if hedge.face:
            continue
        face = dcel_mesh.Face(dcel_mesh)
        face.outer = hedge
        for h in hedge.loop_hedges:
            h.face = face
    used = set()
    faces = []
    for hedge in dcel_mesh.hedges:
        if hedge not in used:
            faces.append(hedge.face)
            [used.add(h) for h in hedge.loop_hedges]
    dcel_mesh.faces = faces


def insert_edge(up_p, low_p):
    # insert new edge into half edge data structure
    up_hedge = up_p.mesh.HalfEdge(up_p.mesh, up_p)
    up_p.mesh.hedges.append(up_hedge)
    low_hedge = up_p.mesh.HalfEdge(up_p.mesh, low_p)
    up_p.mesh.hedges.append(low_hedge)
    up_hedge.twin = low_hedge
    low_hedge.twin = up_hedge
    up_p_hedge = find_hedge(up_p)
    low_p_hedge = find_hedge(low_p)

    up_ccw_hedges = []
    status = 1
    for h in up_p_hedge.ccw_hedges:
        up_ccw_hedges.append(h)
        if h.twin.face and h.twin.face == up_p_hedge.face:
            status -= 1
            break
    if status != 0:
        raise Exception('Hedge ({}) does not have neighbour with the same face'.format(up_p_hedge))

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
            up_next = up_ccw_hedges[1] if up_ccw_hedges[0] < up_ccw_hedges[1] < up_hedge else up_ccw_hedges[0]
    else:
        raise Exception('Unexpected number of half edges in point {}'.format(up_p))

    low_ccw_hedges = []
    status = 1
    for h in low_p_hedge.ccw_hedges:
        low_ccw_hedges.append(h)
        if h.twin.face and h.twin.face == low_p_hedge.face:
            status -= 1
            break
    if status != 0:
        raise Exception('Hedge ({}) does not have neighbour with the same face'.format(low_p.hedge.i))

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
    if hasattr(up_hedge, 'in_faces'):
        # actually this part related with merge mesh algorithm only
        up_hedge.in_faces = set(up_hedge.next.in_faces)
        low_hedge.in_faces = set(low_hedge.next.in_faces)


def handle_start_point(point, status, hedge):
    # Read Computational Geometry by Mark de Berg
    edge = Edge(point, hedge.twin.origin)
    hedge.edge = edge
    hedge.twin.edge = edge
    edge.helper = point
    status.insert(edge)


def handle_end_point(point, status, hedge):
    # Read Computational Geometry by Mark de Berg
    status.remove(hedge.last.edge)
    helper = hedge.last.edge.helper
    if helper.type == 'merge':
        insert_edge(helper, point)


def handle_split_point(point, status, hedge):
    # Read Computational Geometry by Mark de Berg
    left_node = status.find_nearest_left(point.co[x])
    insert_edge(left_node.key.helper, point)
    left_node.key.helper = point
    edge = Edge(point, hedge.twin.origin)
    hedge.edge = edge
    hedge.twin.edge = edge
    edge.helper = point
    status.insert(edge)


def handle_merge_point(point, status, hedge):
    # Read Computational Geometry by Mark de Berg
    right_helper = hedge.last.edge.helper
    last_hedge = hedge.last
    if right_helper.type == 'merge':
        insert_edge(right_helper, point)
    status.remove(last_hedge.edge)
    left_node = status.find_nearest_left(point.co[x])
    left_helper = left_node.key.helper
    if left_helper.type == 'merge':
        insert_edge(left_helper, point)
    left_node.key.helper = point


def handle_regular_point(point, status, hedge):
    # Read Computational Geometry by Mark de Berg
    if point < hedge.twin.origin:
        right_helper = hedge.last.edge.helper
        status.remove(point.hedge.last.edge)
        edge = Edge(point, hedge.twin.origin)
        hedge.edge = edge
        hedge.twin.edge = edge
        edge.helper = point
        status.insert(edge)
        if right_helper.type == 'merge':
            insert_edge(right_helper, point)
    else:
        left_node = status.find_nearest_left(point.co[x])
        left_helper = left_node.key.helper
        left_node.key.helper = point
        if left_helper.type == 'merge':
            insert_edge(left_helper, point)


handle_functions = {'start': handle_start_point, 'end': handle_end_point, 'split': handle_split_point,
                    'merge': handle_merge_point, 'regular': handle_regular_point}
