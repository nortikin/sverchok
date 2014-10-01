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

import bpy
from mathutils import Vector

import data_structure

# cache node group update trees
update_cache = {}
# cache for partial update lists
partial_update_cache = {}


def make_dep_dict(node_tree):
    """
    Create a dependency dictionary for node group.
    """
    ng = node_tree
    deps = {name: set() for name in ng.nodes.keys()}
    for link in ng.links:
        if not link.is_valid:
            return []  # this happens more often than one might think
        deps[link.to_node.name].add(link.from_node.name)

    # create wifi out dependencies, process if needed
    wifi_out_nodes = [(name, node.var_name)
                      for name, node in ng.nodes.items()
                      if node.bl_idname == 'WifiOutNode' and node.outputs]
    if wifi_out_nodes:
        wifi_dict = {node.var_name: name
                     for name, node in ng.nodes.items()
                     if node.bl_idname == 'WifiInNode'}
        for name, var_name in wifi_out_nodes:
            if var_name not in wifi_dict:
                print("Unsatisifed Wifi dependency: node, {0} var,{1}".format(name, var_name))
                return []
            deps[name].add(wifi_dict[var_name])

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
    if node_set:
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
            print("Invalid node tree!")
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
    node_links = {name: set() for name in ng.nodes.keys()}
    nodes = set(ng.nodes.keys())
    if not nodes:
        return []
    for link in ng.links:
        if not link.is_valid:
            return []
        f_name = link.from_node.name
        t_name = link.to_node.name
        node_links[f_name].add(t_name)
        node_links[t_name].add(f_name)

    wifi_out_nodes = [(name, node.var_name)
                      for name, node in ng.nodes.items()
                      if node.bl_idname == 'WifiOutNode' and node.outputs]
    if wifi_out_nodes:
        wifi_dict = {node.var_name: name
                     for name, node in ng.nodes.items()
                     if node.bl_idname == 'WifiInNode'}
        for name, var_name in wifi_out_nodes:
            in_name = wifi_dict.get(var_name)
            if not in_name:
                print("Unsatisifed Wifi dependency: node, {0} var,{1}".format(name, var_name))
                return []
            node_links[name].add(in_name)
            node_links[in_name].add(name)

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

    return [node for node in node_set_list if len(node) > 1]


def make_tree_from_nodes(node_names, tree):
    """
    Create a partial update list from a sub-tree, node_names is a list of node that
    drives change for the tree
    Only nodes downtree from node_name are updated
    """
    ng = tree
    nodes = ng.nodes
    if not node_names:
        print("No nodes!")
        return make_update_list(ng)

    out_set = set(node_names)

    out_stack = collections.deque(node_names)
    current_node = out_stack.pop()

    # build downwards links, this should be cached perhaps
    node_links = {name: set() for name in nodes.keys()}
    for link in ng.links:
        if not link.is_valid:
            return []
        node_links[link.from_node.name].add(link.to_node.name)

    wifi_out_nodes = [(name, node.var_name)
                      for name, node in nodes.items()
                      if node.bl_idname == 'WifiOutNode' and node.outputs]
    if wifi_out_nodes:
        wifi_dict = {node.var_name: name
                     for name, node in nodes.items()
                     if node.bl_idname == 'WifiInNode'}
        for name, var_name in wifi_out_nodes:
            in_name = wifi_dict.get(var_name)
            if not in_name:
                print("Unsatisifed Wifi dependency: node, {0} var,{1}".format(name, var_name))
                return []
            node_links[in_name].add(name)

    while current_node:
        for node in node_links[current_node]:
            if node not in out_set:
                out_set.add(node)
                out_stack.append(node)
        if out_stack:
            current_node = out_stack.pop()
        else:
            current_node = ''

    return make_update_list(ng, out_set)


# to make update tree based on node types and node names bases
# no used yet
# should add a check do find animated or driven nodes.

def make_animation_tree(node_types, node_list, tree_name):
    global update_cache
    ng = bpy.data.node_groups[tree_name]
    node_set = set(node_list)
    for n_t in node_types:
        node_set = node_set | {name for name, node in ng.nodes.items() if node.bl_idname == n_t}
    a_tree = make_tree_from_nodes(list(node_set), tree_name)
    return a_tree


def build_update_list(tree=None):
    """
    Makes a complete update list for the tree,
    If tree is not passed
    """
    global update_cache
    global partial_update_cache
    # clear cache on every full update

    if tree is not None:
        tree_list = [(tree.name, tree)]
    else:
        tree_list = bpy.data.node_groups.items()

    for name, ng in tree_list:
        if ng.bl_idname == 'SverchCustomTreeType':
            node_sets = separate_nodes(ng)
            deps = make_dep_dict(ng)
            out = [make_update_list(ng, s, deps) for s in node_sets]
            update_cache[name] = out
            partial_update_cache[name] = {}
            data_structure.reset_socket_cache(ng)


def do_update_heat_map(node_list, nodes):
    """
    Create a heat map for the node tree, under development.
    """
    global DEBUG_MODE
    times = []
    node_list = list(node_list)
    for name in node_list:
        if name in nodes:
            start = time.perf_counter()
            nodes[name].update()
            delta = time.perf_counter()-start
            if data_structure.DEBUG_MODE:
                print("Updated  {0} in:{1}".format(name, round(delta, 4)))
            times.append(delta)
    if not times:
        return
    if not nodes.id_data.sv_user_colors:
        color_data = {node.name: (node.color[:], node.use_custom_color) for node in nodes}
        nodes.id_data.sv_user_colors = str(color_data)

    t_max = max(times)
    addon_name = data_structure.SVERCHOK_NAME
    addon = bpy.context.user_preferences.addons.get(addon_name)
    if addon:
        # to use Vector.lerp
        cold = Vector(addon.preferences.heat_map_cold)
        hot = addon.preferences.heat_map_hot
    else:
        print("Cannot find preferences")
        cold = Vector((1, 1, 1))
        hot = (.8, 0, 0)
    for name, t in zip(node_list, times):
        nodes[name].use_custom_color = True
        # linear scale.
        nodes[name].color = cold.lerp(hot, t / t_max)


def do_update_debug(node_list, nods):
    """
    Debug update, under development
    """
    timings = []
    for nod_name in node_list:
        if nod_name in nods:
            delta = None
            #try:
            start = time.perf_counter()
            nods[nod_name].update()
            delta = time.perf_counter()-start
            #except Exception as e:
            #    nods[nod_name].color=(.9,0,0)
            #    nods[nod_name].use_custom_color=True
            #    print("Node {0} had exception {1}".format(nod_name,e))
            if delta:
                print("Updated  {0} in:{1}".format(nod_name, round(delta, 4)))
                timings.append((nod_name, delta))


def sverchok_update(start_node=None, tree=None, animation_mode=False):
    """
    Sverchok master update function.
    Update from a given node, or a complete layout.
    """
    global update_cache
    global partial_update_cache

    def do_update(node_list, nods):
        for nod_name in node_list:
            if nod_name in nods:
                nods[nod_name].update()

    if data_structure.DEBUG_MODE:
        do_update = do_update_debug
    if data_structure.HEAT_MAP:
        do_update = do_update_heat_map

    # try to update optimized animation trees, not ready
    if animation_mode:
        pass
    # start from the mentioned node the which has had changed property,
    # called from updateNode
    if start_node:
        tree = start_node.id_data
        if tree.name in update_cache and update_cache[tree.name]:
            update_list = None
            p_u_c = partial_update_cache.get(tree.name)
            if p_u_c:
                update_list = p_u_c.get(start_node.name)
            if not update_list:
                update_list = make_tree_from_nodes([start_node.name], tree)
                partial_update_cache[tree.name][start_node.name] = update_list
            nods = tree.nodes
            do_update(update_list, nods)
            return
        else:
            build_update_list(tree)
            update_list = update_cache[tree.name]
            for l in update_list:
                do_update(l, tree.nodes)
            return
    # draw the complete named tree, called from SverchokCustomTreeNode
    if tree:
        node_groups = [(tree.name, tree)]
    else:
        node_groups = bpy.data.node_groups.items()

    # update all node trees
    for name, ng in node_groups:
        if ng.bl_idname == 'SverchCustomTreeType':
            update_list = update_cache.get(name)
            if not update_list:
                build_update_list(ng)
                update_list = update_cache.get(name)
            for l in update_list:
                do_update(l, ng.nodes)


def get_update_lists(ng):
    """
    Make update list available in blender console.
    See the function with the same name in node_tree.py
    """
    global update_cache
    global partial_update_cache
    return (update_cache[ng.name], partial_update_cache[ng.name])
