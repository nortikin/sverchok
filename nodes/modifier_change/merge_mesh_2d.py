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


class Node:
    def __init__(self, key):
        self.key = key
        self.parent = None
        self.leftChild = None
        self.rightChild = None
        self.height = 0

    def __str__(self):
        return str(self.key) + "(" + str(self.height) + ")"

    @property
    def next(self):
        #print('Next -', self, self.leftChild, self.rightChild, self.parent)
        if self.rightChild:
            node = self.rightChild
            while node.leftChild:
                node = node.leftChild
            return node
        elif self.parent:
            parent = self.parent
            child = self
            while True:
                if parent.leftChild and not any([parent.leftChild.key < child.key, parent.leftChild.key > child.key]):  # <-fix??
                    return parent
                elif parent.parent:
                    child = parent
                    parent = parent.parent
                else:
                    return None

    @property
    def last(self):
        if self.leftChild:
            node = self.leftChild
            while node.rightChild:
                node = node.rightChild
            return node
        elif self.parent:
            parent = self.parent
            child = self
            while True:
                if parent.rightChild and not any([parent.rightChild.key < child.key, parent.rightChild.key > child.key]):  # <-fix??
                    return parent
                elif parent.parent:
                    child = parent
                    parent = parent.parent
                else:
                    return None

    def is_leaf(self):
        return (self.height == 0)

    def max_children_height(self):
        if self.leftChild and self.rightChild:
            return max(self.leftChild.height, self.rightChild.height)
        elif self.leftChild and not self.rightChild:
            return self.leftChild.height
        elif not self.leftChild and self.rightChild:
            return self.rightChild.height
        else:
            return -1

    def balance(self):
        return (self.leftChild.height if self.leftChild else -1) - (self.rightChild.height if self.rightChild else -1)


class AVLTree:
    def __init__(self, *args):
        self.rootNode = None
        self.elements_count = 0
        self.rebalance_count = 0
        if len(args) == 1:
            for i in args[0]:
                self.insert(i)

    def __bool__(self):
        return bool(self.rootNode)

    def height(self):
        if self.rootNode:
            return self.rootNode.height
        else:
            return 0

    def max_len(self):
        return sum([2 ** i for i in range(1, self.height())]) + 1

    def rebalance(self, node_to_rebalance):
        self.rebalance_count += 1
        A = node_to_rebalance
        F = A.parent  # allowed to be NULL
        if node_to_rebalance.balance() == -2:
            if node_to_rebalance.rightChild.balance() <= 0:
                """Rebalance, case RRC """
                B = A.rightChild
                C = B.rightChild
                assert (not A is None and not B is None and not C is None)
                A.rightChild = B.leftChild
                if A.rightChild:
                    A.rightChild.parent = A
                B.leftChild = A
                A.parent = B
                if F is None:
                    self.rootNode = B
                    self.rootNode.parent = None
                else:
                    if F.rightChild == A:
                        F.rightChild = B
                    else:
                        F.leftChild = B
                    B.parent = F
                self.recompute_heights(A)
                self.recompute_heights(B.parent)
            else:
                """Rebalance, case RLC """
                B = A.rightChild
                C = B.leftChild
                assert (not A is None and not B is None and not C is None)
                B.leftChild = C.rightChild
                if B.leftChild:
                    B.leftChild.parent = B
                A.rightChild = C.leftChild
                if A.rightChild:
                    A.rightChild.parent = A
                C.rightChild = B
                B.parent = C
                C.leftChild = A
                A.parent = C
                if F is None:
                    self.rootNode = C
                    self.rootNode.parent = None
                else:
                    if F.rightChild == A:
                        F.rightChild = C
                    else:
                        F.leftChild = C
                    C.parent = F
                self.recompute_heights(A)
                self.recompute_heights(B)
        else:
            assert (node_to_rebalance.balance() == +2)
            if node_to_rebalance.leftChild.balance() >= 0:
                B = A.leftChild
                C = B.leftChild
                """Rebalance, case LLC """
                assert (not A is None and not B is None and not C is None)
                A.leftChild = B.rightChild
                if (A.leftChild):
                    A.leftChild.parent = A
                B.rightChild = A
                A.parent = B
                if F is None:
                    self.rootNode = B
                    self.rootNode.parent = None
                else:
                    if F.rightChild == A:
                        F.rightChild = B
                    else:
                        F.leftChild = B
                    B.parent = F
                self.recompute_heights(A)
                self.recompute_heights(B.parent)
            else:
                B = A.leftChild
                C = B.rightChild
                """Rebalance, case LRC """
                assert (not A is None and not B is None and not C is None)
                A.leftChild = C.rightChild
                if A.leftChild:
                    A.leftChild.parent = A
                B.rightChild = C.leftChild
                if B.rightChild:
                    B.rightChild.parent = B
                C.leftChild = B
                B.parent = C
                C.rightChild = A
                A.parent = C
                if F is None:
                    self.rootNode = C
                    self.rootNode.parent = None
                else:
                    if (F.rightChild == A):
                        F.rightChild = C
                    else:
                        F.leftChild = C
                    C.parent = F
                self.recompute_heights(A)
                self.recompute_heights(B)

    def sanity_check(self, *args):
        if len(args) == 0:
            node = self.rootNode
        else:
            node = args[0]
        if (node is None) or (node.is_leaf() and node.parent is None):
            # trival - no sanity check needed, as either the tree is empty or there is only one node in the tree
            pass
        else:
            if node.height != node.max_children_height() + 1:
                raise Exception("Invalid height for node " + str(node) + ": " + str(node.height) + " instead of " + str(
                    node.max_children_height() + 1) + "!")

            balFactor = node.balance()
            # Test the balance factor
            if not (balFactor >= -1 and balFactor <= 1):
                raise Exception("Balance factor for node " + str(node) + " is " + str(balFactor) + "!")
            # Make sure we have no circular references
            if not (node.leftChild != node):
                raise Exception("Circular reference for node " + str(node) + ": node.leftChild is node!")
            if not (node.rightChild != node):
                raise Exception("Circular reference for node " + str(node) + ": node.rightChild is node!")

            if (node.leftChild):
                if not (node.leftChild.parent == node):
                    raise Exception("Left child of node " + str(node) + " doesn't know who his father is!")
                if not (node.leftChild.key <= node.key):
                    raise Exception("Key of left child of node " + str(node) + " is greater than key of his parent!")
                self.sanity_check(node.leftChild)

            if (node.rightChild):
                if not (node.rightChild.parent == node):
                    raise Exception("Right child of node " + str(node) + " doesn't know who his father is!")
                if not (node.rightChild.key >= node.key):
                    raise Exception("Key of right child of node " + str(node) + " is less than key of his parent!")
                self.sanity_check(node.rightChild)

    def recompute_heights(self, start_from_node):
        changed = True
        node = start_from_node
        while node and changed:
            old_height = node.height
            node.height = (node.max_children_height() + 1 if (node.rightChild or node.leftChild) else 0)
            changed = node.height != old_height
            node = node.parent

    def add_as_child(self, parent_node, child_node):
        node_to_rebalance = None
        if child_node.key < parent_node.key:
            if not parent_node.leftChild:
                parent_node.leftChild = child_node
                child_node.parent = parent_node
                if parent_node.height == 0:
                    node = parent_node
                    while node:
                        node.height = node.max_children_height() + 1
                        if not node.balance() in [-1, 0, 1]:
                            node_to_rebalance = node
                            break  # we need the one that is furthest from the root
                        node = node.parent
            else:
                child_node = self.add_as_child(parent_node.leftChild, child_node)
        else:
            if not parent_node.rightChild:
                parent_node.rightChild = child_node
                child_node.parent = parent_node
                if parent_node.height == 0:
                    node = parent_node
                    while node:
                        node.height = node.max_children_height() + 1
                        if not node.balance() in [-1, 0, 1]:
                            node_to_rebalance = node
                            break  # we need the one that is furthest from the root
                        node = node.parent
            else:
                child_node = self.add_as_child(parent_node.rightChild, child_node)

        if node_to_rebalance:
            self.rebalance(node_to_rebalance)

        return child_node

    def insert(self, key):
        new_node = Node(key)
        if not self.rootNode:
            self.rootNode = new_node
            return new_node
        else:
            exist_node = self.find(key)
            if not exist_node:
                self.elements_count += 1
                new_node = self.add_as_child(self.rootNode, new_node)
                return new_node
            else:
                return exist_node

    def find_biggest(self, start_node=None):
        if not start_node:
            node = self.rootNode
        else:
            node = start_node
        while node.rightChild:
            node = node.rightChild
        return node

    def find_smallest(self, start_node=None):
        if not start_node:
            node = self.rootNode
        else:
            node = start_node
        while node.leftChild:
            node = node.leftChild
        return node

    def inorder_non_recursive(self):
        node = self.rootNode
        retlst = []
        while node.leftChild:
            node = node.leftChild
        while (node):
            retlst += [node.key]
            if (node.rightChild):
                node = node.rightChild
                while node.leftChild:
                    node = node.leftChild
            else:
                while ((node.parent) and (node == node.parent.rightChild)):
                    node = node.parent
                node = node.parent
        return retlst

    def preorder(self, node, retlst=None):
        if retlst is None:
            retlst = []
        retlst += [node.key]
        if node.leftChild:
            retlst = self.preorder(node.leftChild, retlst)
        if node.rightChild:
            retlst = self.preorder(node.rightChild, retlst)
        return retlst

    def inorder(self, node, retlst=None):
        if retlst is None:
            retlst = []
        if node.leftChild:
            retlst = self.inorder(node.leftChild, retlst)
        retlst += [node.key]
        if node.rightChild:
            retlst = self.inorder(node.rightChild, retlst)
        return retlst

    def postorder(self, node, retlst=None):
        if retlst is None:
            retlst = []
        if node.leftChild:
            retlst = self.postorder(node.leftChild, retlst)
        if node.rightChild:
            retlst = self.postorder(node.rightChild, retlst)
        retlst += [node.key]
        return retlst

    def as_list(self, pre_in_post):
        if not self.rootNode:
            return []
        if pre_in_post == 0:
            return self.preorder(self.rootNode)
        elif pre_in_post == 1:
            return self.inorder(self.rootNode)
        elif pre_in_post == 2:
            return self.postorder(self.rootNode)
        elif pre_in_post == 3:
            return self.inorder_non_recursive()

    def find(self, key):
        return self.find_in_subtree(self.rootNode, key)

    def find_in_subtree(self, node, key):
        if node is None:
            return None  # key not found
        if key < node.key:
            return self.find_in_subtree(node.leftChild, key)
        elif key > node.key:
            return self.find_in_subtree(node.rightChild, key)
        else:  # key is equal to node key
            return node

    def remove(self, key):
        # first find
        node = self.find(key)

        if not node is None:
            self.elements_count -= 1

            #     There are three cases:
            #
            #     1) The node is a leaf.  Remove it and return.
            #
            #     2) The node is a branch (has only 1 child). Make the pointer to this node
            #        point to the child of this node.
            #
            #     3) The node has two children. Swap items with the successor
            #        of the node (the smallest item in its right subtree) and
            #        delete the successor from the right subtree of the node.
            if node.is_leaf():
                self.remove_leaf(node)
            elif (bool(node.leftChild)) ^ (bool(node.rightChild)):
                self.remove_branch(node)
            else:
                assert (node.leftChild) and (node.rightChild)
                self.swap_with_successor_and_remove(node)

    def remove_node(self, node):
        if node.is_leaf():
            self.remove_leaf(node)
        elif (bool(node.leftChild)) ^ (bool(node.rightChild)):
            self.remove_branch(node)
        else:
            assert (node.leftChild) and (node.rightChild)
            self.swap_with_successor_and_remove(node)

    def remove_leaf(self, node):
        parent = node.parent
        if (parent):
            if parent.leftChild == node:
                parent.leftChild = None
            else:
                assert (parent.rightChild == node)
                parent.rightChild = None
            self.recompute_heights(parent)
        else:
            self.rootNode = None
        del node
        # rebalance
        node = parent
        while (node):
            if not node.balance() in [-1, 0, 1]:
                self.rebalance(node)
            node = node.parent

    def remove_branch(self, node):
        parent = node.parent
        leftChild = node.leftChild
        rightChild = node.rightChild

        if (parent):
            if parent.leftChild == node:
                parent.leftChild = node.rightChild or node.leftChild
            else:
                assert (parent.rightChild == node)
                parent.rightChild = node.rightChild or node.leftChild
            if node.leftChild:
                node.leftChild.parent = parent
            else:
                assert (node.rightChild)
                node.rightChild.parent = parent
            self.recompute_heights(parent)
        del node
        # rebalance
        node = parent
        if node:
            while node:
                if not node.balance() in [-1, 0, 1]:
                    self.rebalance(node)
                node = node.parent
        else:
            if leftChild:
                self.rootNode = leftChild
            else:
                self.rootNode = rightChild

            self.rootNode.parent = None

    def swap_with_successor_and_remove(self, node):
        successor = self.find_smallest(node.rightChild)
        self.swap_nodes(node, successor)
        assert (node.leftChild is None)
        if node.height == 0:
            self.remove_leaf(node)
        else:
            self.remove_branch(node)

    def swap_nodes(self, node1, node2):
        assert (node1.height > node2.height)
        parent1 = node1.parent
        leftChild1 = node1.leftChild
        rightChild1 = node1.rightChild
        parent2 = node2.parent
        assert (not parent2 is None)
        assert (parent2.leftChild == node2 or parent2 == node1)
        leftChild2 = node2.leftChild
        assert (leftChild2 is None)
        rightChild2 = node2.rightChild

        # swap heights
        tmp = node1.height
        node1.height = node2.height
        node2.height = tmp

        if parent1:
            if parent1.leftChild == node1:
                parent1.leftChild = node2
            else:
                assert (parent1.rightChild == node1)
                parent1.rightChild = node2
            node2.parent = parent1
        else:
            self.rootNode = node2
            node2.parent = None

        node2.leftChild = leftChild1
        leftChild1.parent = node2
        node1.leftChild = leftChild2  # None
        node1.rightChild = rightChild2
        if rightChild2:
            rightChild2.parent = node1
        if not (parent2 == node1):
            node2.rightChild = rightChild1
            rightChild1.parent = node2

            parent2.leftChild = node1
            node1.parent = parent2
        else:
            node2.rightChild = node1
            node1.parent = node2

            # use for debug only and only with small trees

    def out(self, start_node=None):
        if start_node == None:
            start_node = self.rootNode
        space_symbol = "*"
        spaces_count = 80
        out_string = ""
        initial_spaces_string = space_symbol * spaces_count + "\n"
        if not start_node:
            return "AVLTree is empty"
        else:
            level = [start_node]
            while (len([i for i in level if (not i is None)]) > 0):
                level_string = initial_spaces_string
                for i in range(len(level)):
                    j = int((i + 1) * spaces_count / (len(level) + 1))
                    level_string = level_string[:j] + (str(level[i]) if level[i] else space_symbol) + level_string[
                                                                                                      j + 1:]
                level_next = []
                for i in level:
                    level_next += ([i.leftChild, i.rightChild] if i else [None, None])
                level = level_next
                out_string += level_string
        return out_string


x, y, z = 0, 1, 2
test_hedge = []
test_intersections = []


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


def is_less(v1, v2, epsilon=1e-5):
    return v2 - v1 > epsilon


def is_more(v1, v2, epsilon=1e-5):
    return v1 - v2 > epsilon


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
    global_event_point = None

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
        self.is_horizontal = almost_equal(self.up_v[y], self.low_v[y])
        self.direction = self.get_direction()

        self.low_hedge = None
        self.up_hedge = None
        self.coincidence = []

    def __str__(self):
        return 'Edge({}, {})({})'.format(self.i1, self.i2, self.subdivision)

    def __lt__(self, other):
        #debug("~~~~~~~~Start to compare {} < {}".format(self, other))
        # when edge are inserting to the three
        if isinstance(other, EdgeSweepLine):
            # if two edges intersect in one point less edge will be with bigger angle with X coordinate
            if almost_equal(self.intersection, other.intersection):
                #debug("Edges are equal, self angle: {} < other angle: {}".format(self.product, other.product))
                if almost_equal(self.product, other.product):
                    # two edges are overlapping each other, there is no need of storing them together in tree
                    # longest edge should take place in tree with information of both overlapping edges
                    # input can have equal edges, such cases should be handled externally
                    return False
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
                    # two edges are overlapping each other, there is no need of storing them together in tree
                    # longest edge should take place in tree with information of both overlapping edges
                    # input can have equal edges, such cases should be handled externally
                    return False
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
            return self.event_point.co[x]
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
        self.last_intersection = (self.event_point.co[y] * self.cross[y] + self.cross[z]) / -self.cross[x]
        self.last_product = dot_product(self.direction, (1, 0))
        self.last_event = self.event_point

    def get_low_index(self):
        # find index in edge of index of lowest point
        if is_more(self.v1[y], self.v2[y]):
            out = 1
        elif is_less(self.v1[y], self.v2[y]):
            out = 0
        else:
            if is_less(self.v1[x], self.v2[x]):
                out = 1
            else:
                out = 0  # Исправить в алгоритме пересечений отрезков !!!
        return out

    @property
    def is_c(self):
        # returns True if current event point is intersection point of current edge
        return not (almost_equal(self.low_v[x], self.event_point.co[x]) and
                    almost_equal(self.low_v[y], self.event_point.co[y]))

    @property
    def event_point(self):
        # get actual event point
        if EdgeSweepLine.global_event_point is not None:
            return EdgeSweepLine.global_event_point
        else:
            raise Exception('Sweep line should be initialized before')

    def get_direction(self):
        # get downward direction of edge
        vector = (self.low_v[x] - self.up_v[x], self.low_v[y] - self.up_v[y])
        v_len = (vector[x] ** 2 + vector[y] ** 2) ** 0.5
        return (vector[x] / v_len, vector[y] / v_len)

    @property
    def low_dot_length(self):
        vector = [ax1 - ax2 for ax1, ax2 in zip(self.event_point.co, self.low_v)]
        return dot_product(vector, vector)

    def get_angle(self):
        # this does not take in account cases with c edges
        if self.is_horizontal:
            pass

    @property
    def inner_hedge(self):
        return self.low_hedge if self.low_hedge.i == self.event_point.i else self.up_hedge

    @property
    def outer_hedge(self):
        return self.low_hedge if self.low_hedge.i != self.event_point.i else self.up_hedge

    @property
    def subdivision(self):
        if self.up_hedge is None:
            return None
        else:
            return {v for s in [self.up_hedge, self.low_hedge] for v in s.subdivision}

    def set_low_i(self, i):
        self.i1, self.i2 = (i, self.i2) if self.low_i == self.i1 else (self.i1, i)
        self.low_i = i
        self.low_hedge.i = i

    def set_up_i(self, i):
        self.i1, self.i2 = (i, self.i2) if self.up_i == self.i1 else (self.i1, i)
        self.up_i = i
        self.up_hedge.i = i


class EventPoint:
    # Special class for storing in queue data structure

    max_index = -1

    def __init__(self, co, index=None):
        self.co = co
        self.i = index
        self.up_edges = []
        self.check_index()

    def __str__(self):
        #return "({:.1f}, {:.1f})".format(self.co[x], self.co[y])
        return "i - {}".format(self.i)

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

    def check_index(self):
        if self.i is None:
            EventPoint.max_index += 1
            self.i = EventPoint.max_index
        elif self.i > EventPoint.max_index:
            EventPoint.max_index = self.i


def get_coincidence_edges(tree, x_position):
    """
    Get from status all edges and their neighbours which go through event point
    :param tree: status data structure - AVLTree
    :param x_position: x position of event point
    :return: tuple(left neighbour, adjacent edges, right neighbour) - (AVL node, [AVL node, ...], AVL node)
    """
    start_node = tree.find(x_position)
    tree_max_length = tree.max_len()
    #print("searching neighbos, start node -", start_node)
    right_part = [start_node] if start_node else []
    left_part = []
    adjacent_right = None
    adjacent_left = None

    counter = 0
    next_node = start_node
    while next_node:
        next_node = next_node.next
        if next_node and almost_equal(next_node.key.intersection, x_position):
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
        if last_node and almost_equal(last_node.key.intersection, x_position):
            left_part.append(last_node)
        elif last_node:
            adjacent_left = last_node.key
            break
        if counter > tree_max_length:
            raise TimeoutError("Can't find exit from status tree, start node -", start_node)
        counter += 1

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


class HalfEdge:

    def __init__(self, origin, subdivision, i=None):
        self.origin = origin
        self.subdivision = set()
        if subdivision is not None:
            self.subdivision.update(subdivision)
        self.i = i

        self.face = None
        self.twin = None
        self.next = None
        self.last = None

    def __str__(self):
        return 'he-{}{}'.format((self.i, self.twin.i), self.subdivision)

    def __repr__(self):
        return repr('hedge - {}, subset - {}'.format((self.i, self.twin.i), self.subdivision))


class Face:

    def __init__(self, subdivision=None):
        self.outer = None
        self.inners = []
        self.subdivision = set()
        if subdivision:
            self.subdivision = subdivision


def create_half_edges(verts, faces):
    # to do: self intersection polygons? double repeated polygons?
    half_edges_list = dict()
    for i_face, face in enumerate(faces):
        face = face if is_ccw_polygon([verts[i] for i in face]) else face[::-1]
        loop = []
        for i in range(len(face)):
            origin_i = face[i]
            next_i = face[(i + 1) % len(face)]
            half_edge = HalfEdge(verts[origin_i], {0}, origin_i)
            half_edge.face = Face({0})
            loop.append(half_edge)
            half_edges_list[(origin_i, next_i)] = half_edge
        for i in range(len(face)):
            loop[i].last = loop[(i - 1) % len(face)]
            loop[i].next = loop[(i + 1) % len(face)]
    outer_half_edges = dict()
    for key in half_edges_list:
        half_edge = half_edges_list[key]
        if key[::-1] in half_edges_list:
            half_edge.twin = half_edges_list[key[::-1]]
        else:
            outer_edge = HalfEdge(verts[key[1]], None, key[1])
            half_edge.twin = outer_edge
            outer_edge.twin = half_edge
            if key[::-1] in outer_half_edges:
                raise Exception("It looks like input mesh has adjacent faces with only one common point"
                                "Handle such meshes does not implemented yet.")
            outer_half_edges[key[::-1]] = outer_edge
    for key in outer_half_edges:
        outer_edge = outer_half_edges[key]
        next_edge = outer_edge.twin
        while next_edge:
            next_edge = next_edge.last.twin
            if not next_edge.subdivision:
                break
        outer_edge.next = next_edge
        next_edge.last = outer_edge
    return list(half_edges_list.values()) + list(outer_half_edges.values())


def merge_two_half_edges_list(a, b, len_verts_a=None):
    out = list(a)
    for half_edge in b:
        if len_verts_a:
            half_edge.i += len_verts_a
        if half_edge.subdivision:
            half_edge.subdivision = {v + 1 for v in half_edge.subdivision}
        if half_edge.face:
            half_edge.face.subdivision = {v + 1 for v in half_edge.face.subdivision}
        out.append(half_edge)
    return out


def create_edges(half_edges):
    created_edges = set()
    out_edges = []
    out_subdivision_mask = []
    for half_edge in half_edges.values():
        if half_edge.twin_id not in created_edges:
            created_edges.add(half_edge.self_id)
            out_edges.append(half_edge.self_id)
            if half_edge.subdivision:
                out_subdivision_mask.append(list(half_edge.subdivision)[0])
            elif half_edge.twin.subdivision:
                out_subdivision_mask.append(list(half_edge.twin.subdivision)[0])
            else:
                out_subdivision_mask.append(None)
    return out_edges, out_subdivision_mask


def mesh_from_half_edge(half_edges):

    used = set()
    verts = []
    for hedge in half_edges:
        counter = 0
        if hedge in used:
            continue
        used.add(hedge)
        hedge.i = len(verts)
        verts.append(hedge.origin)
        next_edge = hedge.twin.next
        while next_edge != hedge:
            next_edge.i = hedge.i
            used.add(next_edge)
            next_edge = next_edge.twin.next
            counter += 1
            if counter > len(half_edges):
                raise TimeoutError('Hedge - {} does not have a loop'.format(hedge))

    used.clear()
    faces = []
    mask_a = []
    mask_b = []
    for hedge in half_edges:
        if not hedge.subdivision or hedge in used:
            continue
        #print('Build face from -', hedge)
        used.add(hedge)
        face = [hedge.i]
        mask_a.append(1 if 0 in hedge.subdivision else 0)
        mask_b.append(1 if 1 in hedge.subdivision else 0)
        next_edge = hedge.next
        while next_edge != hedge:
            face.append(next_edge.i)
            used.add(next_edge)
            next_edge = next_edge.next
        faces.append(face)

    return verts, faces, mask_a, mask_b


def map_overlay(verts_a, faces_a, verts_b, faces_b):
    global test_hedge
    half_edges = merge_two_half_edges_list(create_half_edges(verts_a, faces_a), create_half_edges(verts_b, faces_b),
                                           len(verts_a))
    intersections = find_intersections(half_edges)
    test_hedge = half_edges
    return mesh_from_half_edge(half_edges)
    #verts = verts_a + verts_b
    #faces = faces_a + faces_b
    #half_edges = merge_two_half_edges_list(create_half_edges(verts_a, faces_a), create_half_edges(verts_b, faces_b),
    #                                       len(verts_a), len(faces_a))
    #edges, subdivision_mask = create_edges(half_edges)
    #intersections = find_intersections(verts, edges, subdivision_mask, half_edges)
    #if intersections:
    #    co, edg = zip(*intersections)
    #    return list(co)


def init_event_queue(event_queue, half_edges):
    EventPoint.max_index = -1
    EdgeSweepLine.global_event_point = None
    used = set()
    for hedge in half_edges:
        if hedge.twin in used:
            continue
        edge = EdgeSweepLine(hedge.origin, hedge.twin.origin, hedge.i, hedge.twin.i)
        edge.up_hedge, edge.low_hedge = (hedge, hedge.twin) if hedge.i == edge.up_i else (hedge.twin, hedge)
        up_node = event_queue.insert(EventPoint(edge.up_v, edge.up_i))
        up_node.key.up_edges += [edge]
        event_queue.insert(EventPoint(edge.low_v, edge.low_i))
        used.add(hedge)


def find_intersections(half_edges):
    """
    Initializing of searching intersection algorithm, read Computational Geometry by Mark de Berg
    :param verts: [(x, y) or (x, y, z), ...]
    :param edges: [(1, 5), ...]
    :return: [(3d dimensional intersection point, [edge1 involved in intersection, edge2, ...]), ...]
    """
    status = AVLTree()
    event_queue = AVLTree()
    init_event_queue(event_queue, half_edges)
    out = []
    while event_queue:
        event_node = event_queue.find_smallest()
        intersection = handle_event_point(status, event_queue, event_node.key, half_edges)
        if intersection:
            out.append(intersection)
        event_queue.remove_node(event_node)
    test_intersections.clear()
    test_intersections.extend(out)
    return out


def handle_event_point(status, event_queue, event_point, half_edges):
    # Read Computational Geometry by Mark de Berg
    EdgeSweepLine.global_event_point = event_point
    out = []
    is_overlapping_points = False
    #print(event_point.i)
    global_event_point = event_point.co
    left_l_candidate, coincidence, right_l_candidate = get_coincidence_edges(status, event_point.co[x])
    c = [node for node in coincidence if node.key.is_c]
    l = [node for node in coincidence if not node.key.is_c]
    [status.remove_node(node) for node in c]
    [status.remove_node(node) for node in l]

    lc = []
    uc_edges = []
    for node in coincidence:
        edge = node.key
        #print('edge {}, up hedge {}, low hedge {}'.format(edge, edge.up_hedge, edge.low_hedge))
        if edge.is_c:
            # split edge on low und up sides
            low_edge = EdgeSweepLine(edge.up_v, event_point.co, edge.up_i, event_point.i)
            up_edge = EdgeSweepLine(event_point.co, edge.low_v, event_point.i, edge.low_i)
            # assign to new edges existing half edges of initial edge
            low_edge.up_hedge = edge.up_hedge
            up_edge.low_hedge = edge.low_hedge
            # copy pare of half edges from existing half edges and create appropriate links
            up_hedge_twin = HalfEdge(event_point.co, edge.low_hedge.subdivision, event_point.i)
            up_hedge_twin.face = edge.low_hedge.face
            up_hedge_twin.next = edge.low_hedge.next
            edge.low_hedge.next.last = up_hedge_twin
            low_hedge_twin = HalfEdge(event_point.co, edge.up_hedge.subdivision, event_point.i)
            low_hedge_twin.face = edge.up_hedge.face
            low_hedge_twin.next = edge.up_hedge.next
            edge.up_hedge.next.last = low_hedge_twin
            low_edge.low_hedge = up_hedge_twin
            up_edge.up_hedge = low_hedge_twin
            low_edge.up_hedge.twin = low_edge.low_hedge
            low_edge.low_hedge.twin = low_edge.up_hedge
            up_edge.up_hedge.twin = up_edge.low_hedge
            up_edge.low_hedge.twin = up_edge.up_hedge
            # turn back subdivision of half edges of up edge
            up_edge.up_hedge.subdivision = set(up_edge.up_hedge.face.subdivision) if up_edge.up_hedge.face else set()
            up_edge.low_hedge.subdivision = set(up_edge.low_hedge.face.subdivision) if up_edge.low_hedge.face else set()
            half_edges.extend([up_hedge_twin, low_hedge_twin])
            node.key = low_edge
            uc_edges.append(up_edge)
            #print('low edge {}, up_hedge {}, low hedge {}'.format(low_edge, low_edge.up_hedge, low_edge.low_hedge))
            #print('up edge {}, up hedge {}, low hedge {}'. format(up_edge, up_edge.up_hedge, up_edge.low_hedge))
        else:
            if edge.low_i != event_point.i:
                # check overlapping points
                edge.set_low_i(event_point.i)
                is_overlapping_points = True
        lc.append(node)
    #print('lc -', *lc)

    u = []
    for edge in event_point.up_edges + uc_edges:
        if edge.up_i != event_point.i:
            # check overlapping points
            edge.set_up_i(event_point.i)
            is_overlapping_points = True
        node = status.insert(edge)
        if edge != node.key:
            if edge.low_dot_length > node.key.low_dot_length:
                edge.coincidence.append(node.key)
                node.key = edge
            else:
                node.key.coincidence.append(edge)
        u.append(node)
    left_u_candidate, uc, right_u_candidate = get_coincidence_edges(status, event_point.co[x])
    left_neighbor = left_l_candidate if left_l_candidate else left_u_candidate
    right_neighbor = right_l_candidate if right_l_candidate else right_u_candidate
    #print('uc -', *uc)
    #print('left and right neighbors -', left_neighbor, right_neighbor)

    rotation_nodes = uc + lc[::-1]
    if c or is_overlapping_points:
        #print('uc lc -', *rotation_nodes)
        for i in range(len(rotation_nodes)):
            edge = rotation_nodes[i].key
            #print('edge -', edge)
            next_i = (i + 1) % len(rotation_nodes)
            last_i = (i - 1) % len(rotation_nodes)
            edge.outer_hedge.next = rotation_nodes[last_i].key.inner_hedge
            edge.inner_hedge.last = rotation_nodes[next_i].key.outer_hedge
            #print('outer hedge {}, next {}, last {}'.format(edge.outer_hedge, edge.outer_hedge.next, edge.outer_hedge.last))
            #print('inner hedge {}, next {}, last {}'.format(edge.inner_hedge, edge.inner_hedge.next, edge.inner_hedge.last))

        sub_status = set(rotation_nodes[-1].key.inner_hedge.subdivision)
        for i in range(len(rotation_nodes) * 2):
            edge = rotation_nodes[i % len(rotation_nodes)].key
            off = edge.outer_hedge.subdivision - edge.inner_hedge.subdivision
            on = edge.inner_hedge.subdivision - edge.outer_hedge.subdivision
            sub_status -= off
            edge.outer_hedge.subdivision |= sub_status
            sub_status |= on
            edge.inner_hedge.subdivision |= sub_status
            #print('Edge {}, outer_subd {}, inner_subd {}'.format(edge, edge.outer_hedge, edge.inner_hedge))
    elif left_neighbor and left_neighbor.up_hedge.subdivision:
        for node in uc:
            edge = node.key
            if edge.subdivision != left_neighbor.up_hedge.subdivision:
                #print('Mark edge {} by {}'.format(edge, left_neighbor.up_hedge))
                off = edge.low_hedge.subdivision - edge.up_hedge.subdivision
                sub_status = left_neighbor.up_hedge.subdivision - off
                edge.low_hedge.subdivision |= sub_status
                edge.up_hedge.subdivision |= sub_status
                #print('Result -', edge.low_hedge, edge.up_hedge)

    if c or len(set([node.key.up_i for node in u] + [node.key.low_i for node in l])) > 1:
        point = tuple(list(event_point.co) + [0]) if len(event_point.co) == 2 else tuple(event_point.co)
        out.append(point)

    if not uc:
        if left_neighbor and right_neighbor:
            find_new_event(left_neighbor, right_neighbor, event_queue, event_point)
    else:
        leftmost_node = uc[0]
        rightmost_node = uc[-1]
        #left_neighbor = leftmost_node.last
        #right_neighbor = rightmost_node.next
        #print('leftmost_node', leftmost_node)
        #print('rightmost_node', rightmost_node)
        if left_neighbor:
            find_new_event(leftmost_node.key, left_neighbor, event_queue, event_point)
        if right_neighbor:
            find_new_event(rightmost_node.key, right_neighbor, event_queue, event_point)
    #print(status.out())
    if out:
        return out


def find_new_event(edge1, edge2, event_queue, event_point):
    # Read Computational Geometry by Mark de Berg
    #print('intersection test -', edge1, edge2)
    if is_edges_intersect_2d(edge1.v1, edge1.v2, edge2.v1, edge2.v2):
        intersection = intersect_lines_2d(edge1.v1, edge1.v2, edge2.v1, edge2.v2)
        if intersection:
            new_event_point = EventPoint(intersection + [0], None)
            if new_event_point > event_point:
                event_queue.insert(new_event_point)
                #print('past new event point : \n', event_queue.out())


class MergeMesh2D(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: like boolean
    Tip

    Tip
    """
    bl_idname = 'MergeMesh2D'
    bl_label = 'Merge mesh 2D'
    bl_icon = 'AUTOMERGE_ON'

    def sv_init(self, context):
        self.inputs.new('VerticesSocket', 'VertsA')
        self.inputs.new('StringsSocket', 'FacesA')
        self.inputs.new('VerticesSocket', 'VertsB')
        self.inputs.new('StringsSocket', 'FacesB')
        self.outputs.new('VerticesSocket', 'Verts')
        self.outputs.new('StringsSocket', 'Faces')
        self.outputs.new('StringsSocket', 'MaskA')
        self.outputs.new('StringsSocket', 'MaskB')

    def process(self):
        global test
        verts_a = self.inputs['VertsA'].sv_get()[0]
        faces_a = self.inputs['FacesA'].sv_get()[0]
        verts_b = self.inputs['VertsB'].sv_get()[0]
        faces_b = self.inputs['FacesB'].sv_get()[0]
        mesh = map_overlay(verts_a, faces_a, verts_b, faces_b)
        if mesh:
            v, f, ma, mb = zip(mesh)
            self.outputs['Verts'].sv_set(v)
            self.outputs['Faces'].sv_set(f)
            self.outputs['MaskA'].sv_set(ma)
            self.outputs['MaskB'].sv_set(mb)


def register():
    bpy.utils.register_class(MergeMesh2D)


def unregister():
    bpy.utils.unregister_class(MergeMesh2D)
