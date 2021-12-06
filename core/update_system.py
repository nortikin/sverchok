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

import collections
import time
from itertools import chain

import bpy

from sverchok import data_structure
from sverchok.core.socket_data import SvNoDataError
from sverchok.utils.logging import warning, error, exception
from sverchok.utils.profile import profile
from sverchok.core.socket_data import clear_all_socket_cache
import sverchok

import ast

graphs = []
# graph_dicts = {}

no_data_color = (1, 0.3, 0)
exception_color = (0.8, 0.0, 0)


def clear_system_cache():
    print("cleaning Sverchok cache")
    clear_all_socket_cache()


def update_error_colors(self, context):
    global no_data_color
    global exception_color
    no_data_color = self.no_data_color[:]
    exception_color = self.exception_color[:]

def reset_timing_graphs():
    global graphs
    graphs = []
    # graph_dicts = {}


# cache node group update trees
update_cache = {}
# cache for partial update lists
partial_update_cache = {}


def make_dep_dict(node_tree, down=False):
    """
    Create a dependency dictionary for node group.
    """
    ng = node_tree

    deps = collections.defaultdict(set)

    # create wifi out dependencies, process if needed

    wifi_out_nodes = [(name, node.var_name)
                  for name, node in ng.nodes.items()
                  if node.bl_idname == 'WifiOutNode' and node.outputs]
    if wifi_out_nodes:
        wifi_dict = {node.var_name: name
                     for name, node in ng.nodes.items()
                     if node.bl_idname == 'WifiInNode'}

    for i,link in enumerate(list(ng.links)):
        #  this protects against a rare occurrence where
        #  a link is considered valid without a to_socket
        #  or a from_socket. protects against a blender crash
        #  see https://github.com/nortikin/sverchok/issues/493

        if not (link.to_socket and link.from_socket):
            ng.links.remove(link)
            raise ValueError("Invalid link found!, please report this file")
        # it seems to work even with invalid links, maybe because sverchok update is independent from blender update
        # if not link.is_valid:
            # return collections.defaultdict(set)  # this happens more often than one might think
        if link.is_hidden:
            continue
        key, value = (link.from_node.name, link.to_node.name) if down else (link.to_node.name, link.from_node.name)
        deps[key].add(value)

    for name, var_name in wifi_out_nodes:
        other = wifi_dict.get(var_name)
        if not other:
            warning("Unsatisifed Wifi dependency: node, %s var,%s", name, var_name)
            return collections.defaultdict(set)
        if down:
            deps[other].add(name)
        else:
            deps[name].add(other)

    return deps


def make_update_list(node_tree, node_set=None, dependencies=None):
    """
    Makes a update list from a node_group
    if a node set is passed only the subtree defined by the node set is used. Otherwise
    the complete node tree is used.
    If dependencies are not passed they are built.
    """

    ng = node_tree
    if not node_set:  # if no node_set, take all
        node_set = set(ng.nodes.keys())
    if len(node_set) == 1:
        return list(node_set)
    if node_set:  # get one name
        name = node_set.pop()
        node_set.add(name)
    else:
        return []
    if not dependencies:
        deps = make_dep_dict(ng)
    else:
        deps = dependencies

    tree_stack = collections.deque([name])
    tree_stack_append = tree_stack.append
    tree_stack_pop = tree_stack.pop
    out = collections.OrderedDict()
    # travel in node graph create one sorted list of nodes based on dependencies
    node_count = len(node_set)
    while node_count > len(out):
        node_dependencies = True
        for dep_name in deps[name]:
            if dep_name in node_set and dep_name not in out:
                tree_stack_append(name)
                name = dep_name
                node_dependencies = False
                break
        if len(tree_stack) > node_count:
            error("Invalid node tree!")
            return []
        # if all dependencies are in out
        if node_dependencies:
            if name not in out:
                out[name] = 1
            if tree_stack:
                name = tree_stack_pop()
            else:
                if node_count == len(out):
                    break
                for node_name in node_set:
                    if node_name not in out:
                        name = node_name
                        break
    return list(out.keys())


def separate_nodes(ng, links=None):
    '''
    Separate a node group (layout) into unconnected parts
    Arguments: Node group
    Returns: A list of sets with separate node groups
    '''
    nodes = set(ng.nodes.keys())
    if not nodes:
        return []
    node_links = make_dep_dict(ng)
    down = make_dep_dict(ng, down=True)
    for name, links in down.items():
        node_links[name].update(links)
    n = nodes.pop()
    node_set_list = [set([n])]
    node_stack = collections.deque()

    # find separate sets
    node_stack_append = node_stack.append
    node_stack_pop = node_stack.pop

    while nodes:
        for node in node_links[n]:
            if node not in node_set_list[-1]:
                node_stack_append(node)
        if not node_stack:  # new part
            n = nodes.pop()
            node_set_list.append(set([n]))
        else:
            while n in node_set_list[-1] and node_stack:
                n = node_stack_pop()
            nodes.discard(n)
            node_set_list[-1].add(n)

    found_node_sets = [ns for ns in node_set_list if len(ns) > 1]
  
    if hasattr(ng, "sv_subtree_evaluation_order"):
        sorting_type = ng.sv_subtree_evaluation_order
        if sorting_type in {'X', 'Y'}:
            sort_index = 0 if sorting_type == "X" else 1
            find_lowest = lambda ns: min(ng.nodes[n].absolute_location[sort_index] for n in ns)
            found_node_sets = sorted(found_node_sets, key=find_lowest)

    return found_node_sets

def make_tree_from_nodes(node_names, tree, down=True):
    """
    Create a partial update list from a sub-tree, node_names is a list of nodes that
    drives change for the tree
    """
    ng = tree
    nodes = ng.nodes
    if not node_names:
        warning("No nodes!")
        return make_update_list(ng)

    out_set = set(node_names)

    out_stack = collections.deque(node_names)
    current_node = out_stack.pop()

    # build downwards links, this should be cached perhaps
    node_links = make_dep_dict(ng, down)
    while current_node:
        for node in node_links[current_node]:
            if node not in out_set:
                out_set.add(node)
                out_stack.append(node)
        if out_stack:
            current_node = out_stack.pop()
        else:
            current_node = ''

    if len(out_set) == 1:
        return list(out_set)
    else:
        return make_update_list(ng, out_set)


# to make update tree based on node types and node names bases
# no used yet
# should add a check do find animated or driven nodes.
# needs some updates


def update_error_nodes(ng, name, err=Exception):
    if "error nodes" in ng:
        error_nodes = ast.literal_eval(ng["error nodes"])
    else:
        error_nodes = {}

    node = ng.nodes.get(name)
    if not node:
        return
    error_nodes[name] = (node.use_custom_color, node.color[:])
    ng["error nodes"] = str(error_nodes)

    if isinstance(err, SvNoDataError):
        node.color = no_data_color
    else:
        node.color = exception_color
    node.use_custom_color=True


def reset_error_node(ng, name):
    node = ng.nodes.get(name)
    if node:
        if "error nodes" in ng:
            error_nodes = ast.literal_eval(ng["error nodes"])
            if name in error_nodes:
                node.use_custom_color, node.color = error_nodes[name]
                del error_nodes[name]
            ng["error nodes"] = str(error_nodes)

def reset_error_nodes(ng):
    if "error nodes" in ng:
        error_nodes = ast.literal_eval(ng["error nodes"])
        for name, data in error_nodes.items():
            node = ng.nodes.get(name)
            if node:
                node.use_custom_color = data[0]
                node.color = data[1]
        del ng["error nodes"]

def node_info(ng_name, node, start, delta):
    return {"name" : node.name, "bl_idname": node.bl_idname, "start": start, "duration": delta, "tree_name": ng_name}

@profile(section="UPDATE")
def do_update_general(node_list, nodes, procesed_nodes=set()):
    """
    General update function for node set
    """
    ng = nodes.id_data

    global graphs
    # graph_dicts[ng.name] = []
    timings = []
    graph = []
    gather = graph.append
    
    total_time = 0
    done_nodes = set(procesed_nodes)

    for node_name in node_list:
        if node_name in done_nodes:
            continue
        try:
            node = nodes[node_name]
            start = time.perf_counter()
            if hasattr(node, "process"):
                node.process()

            delta = time.perf_counter() - start
            total_time += delta

            timings.append(delta)
            gather(node_info(ng.name, node, start, delta))

            # probably it's not great place for doing this, the node can be a ReRoute
            [s.update_objects_number() for s in chain(node.inputs, node.outputs) if hasattr(s, 'update_objects_number')]

        except Exception as err:
            update_error_nodes(ng, node_name, err)
            #traceback.print_tb(err.__traceback__)
            exception("Node %s had exception: %s", node_name, err)
            return None

    graphs.append(graph)

    # graph_dicts[nodes.id_data.name] = graph
    return timings


def do_update(node_list, nodes):
    do_update_general(node_list, nodes)

def build_update_list(ng=None):
    """
    Makes a complete update list for the tree,
    If tree is not passed, all sverchok custom tree
    are processced
    """
    global update_cache
    global partial_update_cache
    reset_timing_graphs()

    if not ng:
        for ng in sverchok_trees():
            build_update_list(ng)
    else:
        node_sets = separate_nodes(ng)
        deps = make_dep_dict(ng)
        out = [make_update_list(ng, s, deps) for s in node_sets]
        update_cache[ng.name] = out
        partial_update_cache[ng.name] = {}
        # reset_socket_cache(ng)


def sverchok_trees():
    for ng in bpy.data.node_groups:
        if ng.bl_idname == "SverchCustomTreeType":
            yield ng

def process_tree(ng=None):
    global update_cache
    global partial_update_cache
    reset_timing_graphs()

    if data_structure.RELOAD_EVENT:
        reload_sverchok()
        #return
    if not ng:
        for ng in sverchok_trees():
            process_tree(ng)
    elif ng.bl_idname == "SverchCustomTreeType" and ng.sv_process:
        update_list = update_cache.get(ng.name)
        reset_error_nodes(ng)
        if not update_list:
            build_update_list(ng)
            update_list = update_cache.get(ng.name)
        for l in update_list:
            do_update(l, ng.nodes)
    else:
        pass


def reload_sverchok():
    data_structure.RELOAD_EVENT = False
    from sverchok.core import handlers
    handlers.sv_post_load([])
    reset_timing_graphs()


def register():
    addon_name = sverchok.__name__
    addon = bpy.context.preferences.addons.get(addon_name)
    if addon:
        update_error_colors(addon.preferences, [])
