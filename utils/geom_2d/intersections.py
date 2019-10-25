# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


from .dcel import DCELMesh as DCELMesh_template, Point as Point_template, HalfEdge as HalfEdge_template
from .lin_alg import almost_equal, is_edges_intersect, intersect_edges
from .sort_mesh import SortPointsUpDown, SortEdgeSweepingAlgorithm
from sverchok.utils.avl_tree import AVLTree

from .dcel_debugger import Debugger


def intersect_sv_edges(sv_verts, sv_edges, accuracy=1e-5):
    """
    Merge several Sverchok mesh objects into one with finding self intersections
    :param sv_verts: [[[x1, y1, z1], [x2, y2, z2], ...]-obj_1, [[x1, y1, z1], [x2, y2, z2], ...]-obj_2, ..., obj_n]
    :param sv_edges: [[[i1, i2], edge2, .., edge n]-obj_1, [[i1, i2], edge2, .., edge n]-obj_2, .., obj_n]
    :param accuracy: two floats figures are equal if their difference is lower then accuracy value, float
    :return: vertices in SV format, edges in SV format
    """
    mesh = DCELMesh(accuracy)
    mesh.from_sv_edges(sv_verts, sv_edges)
    find(mesh, accuracy)
    return mesh.to_sv_edges()


# #############################################################################
# ###########________find intersections algorithm_________#####################
# #############################################################################


x, y, z = 0, 1, 2


class Point(Point_template, SortPointsUpDown):

    def __init__(self, mesh, co, accuracy=1e-6):
        super().__init__(mesh, co)
        self.accuracy = accuracy
        self.up_edges = []  # edges below event point


class HalfEdge(HalfEdge_template):
    def __init__(self,  mesh, point, face=None):
        super().__init__(mesh, point, face)

        # This need for find intersection algorithm for detection unused half edges
        # Also this need for make monotone algorithm, don't remember how
        self.edge = None


class DCELMesh(DCELMesh_template):
    Point = Point
    HalfEdge = HalfEdge


class Edge(SortEdgeSweepingAlgorithm):
    # Special class for storing in status data structure

    def __init__(self, up_p, low_p):
        super().__init__(up_p, low_p)

        self.low_hedge = None  # half edge which origin is lower then origin of twin
        self.up_hedge = None  # half edge which origin is upper then origin of twin
        self.coincidence = []  # just a list of overlapping edges

    @property
    def is_c(self):
        # returns True if current event point is intersection point of current edge
        return self.low_p != self.event_point

    @property
    def low_dot_length(self):
        # returns length of edge from event point to low point of the edge
        return (self.low_p - self.event_point).length()

    @property
    def inner_hedge(self):
        # returns half edge with origin in event point
        return self.low_hedge if self.low_hedge.origin == self.event_point else self.up_hedge

    @property
    def outer_hedge(self):
        # returns half edge pointing to event point
        return self.low_hedge if self.low_hedge.origin != self.event_point else self.up_hedge


def find(dcel_mesh, accuracy=1e-6):
    """
    Initializing of searching intersection algorithm, read Computational Geometry by Mark de Berg
    :param dcel_mesh: inner DCELMesh data structure
    :param accuracy: two floats figures are equal if their difference is lower then accuracy value, float
    """
    status = AVLTree()
    event_queue = AVLTree()
    accuracy = accuracy if isinstance(accuracy, float) else 1 / 10 ** accuracy
    Edge.set_accuracy(accuracy)
    init_event_queue(event_queue, dcel_mesh)
    while event_queue:
        event_node = event_queue.find_smallest()
        handle_event_point(status, event_queue, event_node.key, dcel_mesh, accuracy)
        event_queue.remove_node(event_node)
    dcel_mesh.hedges = [hedge for hedge in dcel_mesh.hedges if hedge.edge]


def init_event_queue(event_queue, dcel_mesh):
    # preparation to finding intersection algorithm
    Edge.global_event_point = None
    used = set()
    for hedge in dcel_mesh.hedges:
        if hedge.twin in used:
            continue
        up_h, low_h = (hedge, hedge.twin) if hedge.origin < hedge.twin.origin else (hedge.twin, hedge)
        edge = Edge(up_h.origin, low_h.origin)
        edge.up_hedge, edge.low_hedge = up_h, low_h
        hedge.edge, hedge.twin.edge = edge, edge
        # The trick here is that AVL tree does not create new node if node with such value already exist
        # It just returns existing node without any warnings
        up_node = event_queue.insert(up_h.origin)
        up_node.key.up_edges += [edge]
        event_queue.insert(low_h.origin)
        used.add(hedge)


def handle_event_point(status, event_queue, event_point, dcel_mesh, accuracy=1e-6):
    # Read Computational Geometry by Mark de Berg
    Edge.global_event_point = event_point
    left_l_candidate, coincidence, right_l_candidate = get_coincidence_edges(status, event_point.co[x], accuracy)
    c = [node for node in coincidence if node.key.is_c]
    l = [node for node in coincidence if not node.key.is_c]
    [status.remove_node(node) for node in c]
    [status.remove_node(node) for node in l]

    lc, uc_edges, is_lapp_1 = split_crossed_edge(coincidence, event_point, dcel_mesh)
    up_overlapping, is_lapp_2 = extract_overlapping_edges(coincidence, event_point)
    u, is_lapp_3 = insert_edges_in_status(status, event_point, uc_edges, up_overlapping)
    is_overlapping = any([is_lapp_1, is_lapp_2, is_lapp_3])

    # After new up edges (created be dividing intersected event point edges) was insert in status
    # The order of edges should be taken from status again
    # Don't remember why left and right neighbour should be recheck :/
    left_u_candidate, uc, right_u_candidate = get_coincidence_edges(status, event_point.co[x], accuracy)
    left_neighbor = left_l_candidate if left_l_candidate else left_u_candidate
    right_neighbor = right_l_candidate if right_l_candidate else right_u_candidate

    relink_half_edges(uc, lc, c, left_neighbor, is_overlapping)

    if not uc:
        if left_neighbor and right_neighbor:
            find_new_event(left_neighbor, right_neighbor, event_queue, event_point, dcel_mesh, accuracy)
    else:
        leftmost_node = uc[0]
        rightmost_node = uc[-1]
        if left_neighbor:
            find_new_event(leftmost_node.key, left_neighbor, event_queue, event_point, dcel_mesh, accuracy)
        if right_neighbor:
            find_new_event(rightmost_node.key, right_neighbor, event_queue, event_point, dcel_mesh, accuracy)


def get_coincidence_edges(tree, x_position, accuracy=1e-6):
    """
    Get from status all edges and their neighbours which go through event point
    :param tree: status data structure - AVLTree
    :param x_position: x position of event point
    :param accuracy: two floats figures are equal if their difference is lower then accuracy value, float
    :return: tuple(left neighbour, adjacent edges, right neighbour) - (AVL node, [AVL node, ...], AVL node)
    """
    start_node = tree.find(x_position)
    tree_max_length = tree.max_len()
    right_part = [start_node] if start_node else []
    left_part = []
    adjacent_right = None
    adjacent_left = None

    counter = 0
    next_node = start_node
    while next_node:
        next_node = next_node.next
        if next_node and almost_equal(next_node.key.intersection, x_position, accuracy):
            right_part.append(next_node)
        elif next_node:
            adjacent_right = next_node.key
            break
        if counter > tree_max_length:
            raise TimeoutError("Can't find exit from status tree, start node -", start_node)
        counter += 1

    counter = 0
    last_node = start_node
    while last_node:
        last_node = last_node.last
        if last_node and almost_equal(last_node.key.intersection, x_position, accuracy):
            left_part.append(last_node)
        elif last_node:
            adjacent_left = last_node.key
            break
        if counter > tree_max_length:
            raise TimeoutError("Can't find exit from status tree, start node -", start_node)
        counter += 1

    return adjacent_left, left_part[::-1] + right_part, adjacent_right


def split_crossed_edge(coincidence_nodes, event_point, dcel_mesh):
    """
    In this bloke of code  edges which go through event point are splitting in to edges upper and lower of event point
    Also in this bloke of code coincidence of ends of edges are detected
    Also there is need in checking has "l" edges overlapping or not
    if so the overlapping edges should be carefully repack
    :param coincidence_nodes: list of nodes which intersects with event point, [Node1, ..., Node_n]
    :param event_point: event point of intersection algorithm, Point
    :param dcel_mesh: for new half edges recording, DCELMesh
    :param accuracy: two floats figures are equal if their difference is lower then accuracy value, float
    :return: list of nodes with edges above event point, list of edges below event point, flag of overlapping detection
    """
    lc = []  # is ordered in cw direction low edges
    uc_edges = []
    is_overlapping = False
    for node in coincidence_nodes:
        edge = node.key
        if edge.is_c:
            # split edge on low und up sides
            low_edge = Edge(edge.up_hedge.origin, event_point)  # above event point
            up_edge = Edge(event_point, edge.low_hedge.origin)  # below event point
            # Add information about overlapping edges
            up_edge.coincidence = list(edge.coincidence)
            # assign to new edges existing half edges of initial edge
            low_edge.up_hedge = edge.up_hedge
            up_edge.low_hedge = edge.low_hedge
            low_edge.up_hedge.edge = low_edge  # new "user" of half edge should be replace
            up_edge.low_hedge.edge = up_edge  # the same
            # copy pare of half edges from existing half edges and create appropriate links
            low_edge.low_hedge = HalfEdge(dcel_mesh, event_point, edge.low_hedge.face)
            dcel_mesh.hedges.append(low_edge.low_hedge)
            low_edge.low_hedge.next = edge.low_hedge.next
            edge.low_hedge.next.last = low_edge.low_hedge
            up_edge.up_hedge = HalfEdge(dcel_mesh, event_point, edge.up_hedge.face)
            dcel_mesh.hedges.append(up_edge.up_hedge)
            up_edge.up_hedge.next = edge.up_hedge.next
            edge.up_hedge.next.last = up_edge.up_hedge
            if not "This is for marking faces algorithm for future implementation":
                # add information about belonging to other faces only for new half edge of low edge
                # https://github.com/nortikin/sverchok/issues/2497#issuecomment-536862680
                # and delete outdate information about belonging for low half edge of up edge
                low_edge.low_hedge.in_faces = set(edge.low_hedge.in_faces)  # <-- should be init in data structure
                up_edge.low_hedge.in_faces = set(up_edge.low_hedge.lap_faces)  # <-- should be init in data structure
                up_edge.up_hedge.in_faces = set(low_edge.up_hedge.lap_faces)  # <-- should be init in data structure
                up_edge.up_hedge.lap_faces = set(low_edge.up_hedge.lap_faces)  # <-- should be init in data structure
            up_edge.low_hedge.left = None  # for hole detection
            low_edge.low_hedge.edge = low_edge  # "user" of half edge should be set
            up_edge.up_hedge.edge = up_edge  # the same
            # link half edges to each other
            low_edge.up_hedge.twin = low_edge.low_hedge
            low_edge.low_hedge.twin = low_edge.up_hedge
            up_edge.up_hedge.twin = up_edge.low_hedge
            up_edge.low_hedge.twin = up_edge.up_hedge
            node.key = low_edge
            uc_edges.append(up_edge)
        else:
            # check overlapping points
            if id(edge.low_p) != id(event_point):
                edge.low_p = event_point
                edge.low_hedge.origin = event_point
                is_overlapping = True
        lc.append(node)
    return lc, uc_edges, is_overlapping


def extract_overlapping_edges(coincidence_nodes, event_point):
    """
    As sooner low edges keeps overlapping edges inside itself
    the overlapping edges should be extract before handling up edges
    :param coincidence_nodes: list of nodes which intersects with event point, [Node1, ..., Node_n]
    :param event_point: event point of intersection algorithm, Point
    :return: list of extracted edges below event point, flag of overlapping detection
    """
    up_overlapping = []
    is_overlapping = False
    for node in coincidence_nodes:
        if not node.key.is_c and node.key.coincidence:
            is_overlapping = True  # just enabled relinking half edges of edges around event point
            while node.key.coincidence:
                # only shortest edge (between event point and low end of an edge) should be extracted
                # it will be better to use some another data structure for keeping overlapping edges instead of list
                i_min_edge = min([(edge.low_dot_length, i) for i, edge in enumerate(node.key.coincidence)])[1]
                min_edge = node.key.coincidence.pop(i_min_edge)
                if min_edge.low_p == event_point:
                    # it means the end point of the overlapping edge coincident with end point of main edge
                    # in this case the status of overlapping faces should updated
                    # and next overlapping edge should be founded if such edge exists
                    # also there is need in deleting half edges of such overlapping edges
                    min_edge.up_hedge.edge = None  # this means that the hedge does not use any more...
                    min_edge.low_hedge.edge = None  # and should be deleted
                    if not "this part for marking faces algorithm":
                        node.key.low_hedge.lap_faces -= {min_edge.low_hedge.face}
                        node.key.up_hedge.lap_faces -= {min_edge.up_hedge.face}
                else:
                    # All part of nested edge upper event point should be removed
                    # according this part was already calculated
                    # It looks like instead of editing existing edge it is better to create new one
                    up_edge = Edge(event_point, min_edge.low_p)
                    # Newer the less new half edges for new edge can't be created
                    # because all half edges are stored in the list and deleting old half edges will take linear time
                    # instead of that more appropriate to modify old half edges
                    # actually there is way to delete them after the algorithm is finish
                    # but it works any way at this view
                    up_edge.low_hedge = min_edge.low_hedge
                    up_edge.up_hedge = min_edge.up_hedge
                    up_edge.up_hedge.origin = event_point
                    up_edge.up_hedge.edge = up_edge
                    up_edge.low_hedge.edge = up_edge
                    if not "this part for marking faces algorithm":
                        # Add in_faces status, also faces of half edges of low edge should be remove from in_faces
                        up_edge.low_hedge.lap_faces = node.key.low_hedge.lap_faces - {node.key.low_hedge.face}
                        up_edge.up_hedge.lap_faces = node.key.up_hedge.lap_faces - {node.key.up_hedge.face}
                        up_edge.low_hedge.in_faces = set(up_edge.low_hedge.lap_faces)
                        up_edge.up_hedge.in_faces = set(up_edge.up_hedge.lap_faces)
                    # there is no need in relinking last hedge for up_hedge and next hedge for low_hedge
                    # because this will be done father
                    up_edge.coincidence = list(node.key.coincidence)
                    up_overlapping.append(up_edge)
                    break
    return up_overlapping, is_overlapping


def insert_edges_in_status(status, event_point, uc_edges, up_overlapping):
    """
    Here the edges below of the event point are inserted in status tree
    Also it detects overlapping of points in case if two edges has two different start points
    Also it store overlapping edges to each other
    :param status: list of edges intersection sweep line, AVLTree
    :param event_point: event point of intersection algorithm, Point
    :param uc_edges: list of edges below event point which was created by splitting by sweeping line edges
    :param up_overlapping: list of extracted edges from overlapping list of edges above event point
    :return: list of nodes with edges below an event point, flag of overlapping detection
    """
    u = []
    is_overlapping = False
    for edge in event_point.up_edges + uc_edges + up_overlapping:
        if id(edge.up_p) != id(event_point):
            # check overlapping points
            edge.up_p = event_point
            edge.up_hedge.origin = event_point
            is_overlapping = True
        node = status.insert(edge)
        # actually it does not insert new edge if status already has edge with the same slap
        # and returns node with edge which was already insert before
        if edge != node.key:
            # Store overlapping edges
            if edge.low_dot_length < node.key.low_dot_length:
                # if tow overlapping edges are detected then edge with shortest distance between event point and its end
                # include other overlapping edges inside itself
                edge.coincidence.extend(node.key.coincidence)
                node.key.coincidence.clear()
                edge.coincidence.append(node.key)
                node.key, edge = edge, node.key
            else:
                # This also mean that edges can be equal but there is no difference
                node.key.coincidence.extend(edge.coincidence)
                node.key.coincidence.append(edge)
            if not "This part for marking face mode":
                # Combine information about relations half edges with faces
                # Only current edge can keep actual information about in_faces status
                node.key.low_hedge.in_faces |= edge.low_hedge.in_faces
                node.key.up_hedge.in_faces |= edge.up_hedge.in_faces
                node.key.low_hedge.lap_faces |= edge.low_hedge.lap_faces
                node.key.up_hedge.lap_faces |= edge.up_hedge.lap_faces
        else:
            # store only unique nodes with upper edges
            u.append(node)
    return u, is_overlapping


def relink_half_edges(uc, lc, c, left_neighbor, is_overlapping):
    """
    Here new connections between intersected edges are creating
    Also half edges are marked in which faces they located if need
    :param uc: list of node with edges below event point ordered from left ro right along X coordinate
    :param lc: list of nodes with edges above event point which was born by splitting edges intersecting sweep line
    :param c: list of nodes with edges intersection sweep line, just for knowing if such exist for current event point
    :param left_neighbor: nearest left edge to event point which intersects sweep line
    :param is_overlapping: flag of overlapping detection
    :return: None
    """
    rotation_nodes = uc + lc[::-1]
    if left_neighbor:
        rotation_nodes[0].key.outer_hedge.left = left_neighbor.up_hedge  # for hole detection
    if c or is_overlapping:
        for i in range(len(rotation_nodes)):
            edge = rotation_nodes[i].key
            next_i = (i + 1) % len(rotation_nodes)
            last_i = (i - 1) % len(rotation_nodes)
            edge.outer_hedge.next = rotation_nodes[last_i].key.inner_hedge
            edge.inner_hedge.last = rotation_nodes[next_i].key.outer_hedge

        if not "this part for marking faces mode":
            sub_status = set(rotation_nodes[-1].key.inner_hedge.in_faces)
            for i in range(len(rotation_nodes)):
                edge = rotation_nodes[i].key
                sub_status -= edge.outer_hedge.in_faces
                edge.outer_hedge.in_faces |= sub_status
                sub_status |= edge.inner_hedge.in_faces
                edge.inner_hedge.in_faces |= sub_status

    else:
        if not "and this part for marking faces mode":
            sub_status = set(left_neighbor.up_hedge.in_faces) if left_neighbor else set()
            for node in uc:
                edge = node.key
                sub_status -= edge.outer_hedge.in_faces
                edge.outer_hedge.in_faces |= sub_status
                sub_status |= edge.inner_hedge.in_faces
                edge.inner_hedge.in_faces |= sub_status


def find_new_event(edge1, edge2, event_queue, event_point, dcel_mesh, accuracy=1e-6):
    """
    Tet if there is an intersections and if there is add new event point to event queue
    :param edge1: Edge data structure
    :param edge2: Edge data structure
    :param event_queue: AVLTree
    :param event_point: event point of intersection algorithm, Point
    :param dcel_mesh: for new points recording, DCELMesh
    :param accuracy: two floats figures are equal if their difference is lower then accuracy value, float
    :return: None
    """
    if is_edges_intersect(edge1.up_p.co, edge1.low_p.co, edge2.up_p.co, edge2.low_p.co):
        intersection = intersect_edges(edge1.up_p.co, edge1.low_p.co, edge2.up_p.co, edge2.low_p.co)
        if intersection:  # strange checking
            new_event_point = Point(dcel_mesh, intersection + [0], accuracy)
            if new_event_point > event_point:
                event_queue.insert(new_event_point)
