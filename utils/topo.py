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

"""
Topological sorting.

Performs stable "topological" sort of directed graphs (including graphs with cycles).
Possible optimization: instead of counting sort just put vertices on rindex[v]
positions if there were no SCCs detected.

Ported from original implementation in Java by Marat Radchenko.

original: https://github.com/slonopotamus/stable-topo-sort/blob/master/test/StableTopoSort.java#L16
algorithm description (russian): https://habr.com/ru/post/451208/
"""

from collections import defaultdict

class DoubleStack(object):
    def __init__(self, capacity):
        self.fp = 0 # front pointer
        self.bp = capacity # back pointer
        self.items = [0 for i in range(capacity)]

    def is_empty_front(self):
        return self.fp == 0

    def top_front(self):
        return self.items[self.fp - 1]

    def pop_front(self):
        self.fp -= 1
        return self.items[self.fp]

    def push_front(self, item):
        self.items[self.fp] = item
        self.fp += 1

    def is_empty_back(self):
        return self.bp == len(self.items)

    def top_back(self):
        return self.items[self.bp]

    def pop_back(self):
        value = self.items[self.bp]
        self.bp += 1
        return value
    
    def push_back(self, item):
        self.bp -= 1
        self.items[self.bp] = item

class Node(object):
    def __init__(self, value):
        self.value = value
        self.edges = []
        self.unique_edges = set()
        self.index = 0

    def add_edge_to(self, node):
        self.unique_edges.add(node)
        self.edges.append(node)

    def __str__(self):
        return str(self.value)

class PeaSCC(object):
    def __init__(self, g):
        self.graph = g
        self.rindex = [0 for i in range(len(g))]
        self.index = 1
        self.c = len(g) - 1

        self.vS = DoubleStack(len(g))
        self.iS = DoubleStack(len(g))
        self.root = [False for i in range(len(g))]

    def visit(self, v=None):
        if v is None:
            # Attn! We're walking nodes in reverse
            for i in range(len(self.graph)-1, -1, -1):
                if self.rindex[i] == 0:
                    self.visit(i)
        else:
            self.begin_visiting(v)
            while not self.vS.is_empty_front():
                self.visit_loop()

    def visit_loop(self):
        v = self.vS.top_front()
        i = self.iS.top_front()

        num_edges = len(self.graph[v].edges)

        # Continue traversing out-edges until none left.
        while i <= num_edges:
            # Continuation
            if i > 0:
                # Update status for previously traversed out-edge
                self.finish_edge(v, i - 1)
            if i < num_edges and self.begin_edge(v, i):
                return
            i += 1

        # Finished traversing out edges, update component info
        self.finish_visiting(v)

    def begin_visiting(self, v):
        self.vS.push_front(v)
        self.iS.push_front(0)
        self.root[v] = True
        self.rindex[v] = self.index
        self.index += 1

    def finish_visiting(self, v):
        # Take this vertex off the call stack
        self.vS.pop_front()
        self.iS.pop_front()
        # Update component information
        if self.root[v]:
            self.index -= 1
            while not self.vS.is_empty_back() and self.rindex[v] <= self.rindex[self.vS.top_back()]:
                w = self.vS.pop_back()
                self.rindex[w] = self.c
                self.index -= 1;

            self.rindex[v] = self.c
            self.c -= 1
        else:
            self.vS.push_back(v)

    def begin_edge(self, v, k):
        w = self.graph[v].edges[k].index

        if self.rindex[w] == 0:
            self.iS.pop_front()
            self.iS.push_front(k+1)
            self.begin_visiting(w)
            return True
        else:
            return False

    def finish_edge(self, v, k):
        w = self.graph[v].edges[k].index

        if self.rindex[w] < self.rindex[v]:
            self.rindex[v] = self.rindex[w]
            self.root[v] = False

class StableTopoSort(object):
    @staticmethod
    def reverse_counting_sort(nodes, rindex):
        count = [0 for i in range(len(nodes))]

        for i in range(len(rindex)):
            cindex = len(nodes) - 1 - rindex[i]
            count[cindex] += 1

        for i in range(1, len(count)):
            count[i] += count[i - 1]

        output = [None for i in range(len(nodes))]
        for i in range(len(output)):
            cindex = len(nodes) - 1 - rindex[i]

            # Attn! We're sorting in reverse
            output_index = len(output) - count[cindex]

            output[output_index] = nodes[i]
            count[cindex] -= 1

        return output

    @staticmethod
    def stable_topo_sort(nodes):
        # 0. Remember where each node was
        for i in range(len(nodes)):
            nodes[i].index = i

        # 1. Sort edges according to node indices
        for i in range(len(nodes)):
            nodes[i].edges.sort(key = lambda o: o.index)

        # 2. Perform Tarjan SCC
        scc = PeaSCC(nodes)
        scc.visit()

        # 3. Perform *reverse* counting sort
        return StableTopoSort.reverse_counting_sort(nodes, scc.rindex)

def sort_by_incidence(vertices, edges):
    incidence = defaultdict(lambda: 0)
    for i, j in edges:
        incidence[i] += 1
        incidence[j] += 1
    
    indicies = list(range(len(vertices)))
    indicies.sort(key = lambda i: incidence[i])

    reverse_index = dict()
    vertices_out = []
    for new_index, old_index in enumerate(indicies):
        reverse_index[old_index] = new_index
        vertices_out.append(vertices[old_index])

    edges_out = []
    for i, j in edges:
        edges_out.append((reverse_index[i], reverse_index[j]))

    return vertices_out, edges_out

def stable_topo_sort(vertices, edges):
    graph = []
    nodes = dict()

    #vertices, edges = sort_by_incidence(vertices, edges)

    for i, vertex in enumerate(vertices):
        node = Node(vertex)
        graph.append(node)
        nodes[i] = node

    for i, j in edges:
        from_node = nodes[i]
        to_node = nodes[j]
        from_node.add_edge_to(to_node)

    graph = StableTopoSort.stable_topo_sort(graph)
    return [node.value for node in graph]

