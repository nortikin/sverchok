# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


# source of code: https://github.com/pgrafov/python-avl-tree
# usage:
# tree = AVLTree(list(range(20))
# node = tree.find(10)
# node.next -> return 11
# tree.insert(30)
# tree.find_biggest() -> return 30
# tree.remove(1)
# tree.out() -> print tree


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
        # returns next greater element or None if such does not exist
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
        # returns next smaller element or None if such does not exist
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
    """
    https://en.wikipedia.org/wiki/AVL_tree
    https://www.cs.usfca.edu/~galles/visualization/AVLtree.html
    can be used in conditions like this: if AVLTree(): - if is empty returns false
    """
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
        # returns approximate number of elements of a tree based on information about tree height
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
        # inserts new element to a tree, does not make warnings if element with equal value already was inserted
        # returns node any way
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
        # returns node with biggest value
        if not start_node:
            node = self.rootNode
        else:
            node = start_node
        while node.rightChild:
            node = node.rightChild
        return node

    def find_smallest(self, start_node=None):
        # returns node with smallest value
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
        # returns node or None if node with such value does not exist
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

    def find_nearest_left(self, key):
        # returns next smaller to input value node
        if not self.rootNode:
            return None
        elif not self.rootNode.rightChild and self.rootNode.key < key:
            return self.rootNode
        else:
            return self.find_nearest_in_subtree(self.rootNode, key)

    def find_nearest_in_subtree(self, node, key):
        if key < node.key:
            if node.leftChild:
                return self.find_nearest_in_subtree(node.leftChild, key)
            else:
                return node.last
        elif key > node.key:
            if node.rightChild:
                return self.find_nearest_in_subtree(node.rightChild, key)
            else:
                return node  # without last because the node already is left neighbour
        else:
            return node  # probably node.last ???

    def remove(self, key):
        # removes node from a tree equal to input value if such node exists
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
        # removes node from a tree
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
        # prints a tree in suitable for reading form
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
