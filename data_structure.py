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

from functools import reduce
from math import radians, log
import itertools
import collections
import time
import ast
import bpy
from mathutils import Vector, Matrix

global bmesh_mapping, per_cache

DEBUG_MODE = False
HEAT_MAP = False

# this is set correctly later.
__package__ = "sverchok"

#handle for object in node
temp_handle = {}
# cache node group update trees it not used, as i see
# cache_nodes = {}
# cache node group update trees
list_nodes4update = {}
# cache for partial update lists
partial_update_cache = {}
# wifi node data
sv_Vars = {}
# socket cache
socket_data_cache = {}
# for viewer baker node cache
cache_viewer_baker = {}

# note used?

#bmesh_mapping = {}
#per_cache = {}


#####################################################
################### update magic ####################
#####################################################
# is this used?
# i think no


# main update
def read_cnodes(cnode):
    global cache_nodes
    if cnode not in cache_nodes:
        return None
    return cache_nodes[cnode]


def write_cnodes(cnode, number):
    global cache_nodes
    if cnode in cache_nodes:
        del cache_nodes[cnode]
    cache_nodes[cnode] = number


def clear_cnodes(cnode='ALL'):
    global cache_nodes
    if cnode == 'ALL':
        for i in cache_nodes.items:
            del cache_nodes[i]
    else:
        if read_cnodes(cnode) is not None:
            del cache_nodes[cnode]


def initialize_cnodes():
    node_name = 'GLOBAL CNODE'
    write_cnodes(node_name, 1)
    write_cnodes('LOCK UPDATE CNODES', 1)


def check_update_node(node_name, write=False):
    numb = read_cnodes(node_name)
    etalon = read_cnodes('GLOBAL CNODE')
    #print('etalon',etalon)
    if numb == etalon:
        return False
    else:
        if write:
            write_cnodes(node_name, etalon)
        return True


def ini_update_cnode(node_name):
    if read_cnodes('LOCK UPDATE CNODES') == 1:
        return False

    etalon = read_cnodes('GLOBAL CNODE')
    if etalon is None:
        initialize_cnodes()
        etalon = 1
    else:
        etalon += 1

    write_cnodes('GLOBAL CNODE', etalon)
    write_cnodes(node_name, etalon)
    return True


def is_updated_cnode():
    write_cnodes('LOCK UPDATE CNODES', 0)


def lock_updated_cnode():
    write_cnodes('LOCK UPDATE CNODES', 1)


#####################################################
################### bmesh magic #####################
#####################################################


def read_bmm(bm_ref):
    global bmesh_mapping
    if bm_ref not in bmesh_mapping:
        return None
    return bmesh_mapping[bm_ref]


def write_bmm(bm_ref, bm):
    global bmesh_mapping
    if bm_ref in bmesh_mapping:
        del bmesh_mapping[bm_ref]
    bmesh_mapping[bm_ref] = bm


def clear_bmm(bm_ref='ALL'):
    global bmesh_mapping
    if bm_ref == 'ALL':
        for i in bmesh_mapping.items:
            del bmesh_mapping[i]
    else:
        if read_bmm(bm_ref) is not None:
            del bmesh_mapping[bm_ref]


#####################################################
################### cache magic #####################
#####################################################


def handle_delete(handle):
    if handle in temp_handle:
        del temp_handle[handle]


def handle_read(handle):
    if not (handle in temp_handle):
        return (False, [])

    prop = temp_handle[handle]['prop']
    return (True, prop)


def handle_write(handle, prop):
    if handle in temp_handle:
        if prop != temp_handle[handle]['prop']:
            handle_delete(handle)
    elif not (handle in temp_handle) and handle:
        temp_handle[handle] = {"prop": prop}


def handle_check(handle, prop):
    if handle in handle_check:
        if prop != handle_check[handle]['prop']:
            return False
    else:
        return False
    return True


#####################################################
################ list matching magic ################
#####################################################


# creates an infinite iterator
# use with terminating input
def repeat_last(lst):
    i = -1
    while lst:
        i += 1
        if len(lst) > i:
            yield lst[i]
        else:
            yield lst[-1]


# longest list matching [[1,2,3,4,5], [10,11]] -> [[1,2,3,4,5], [10,11,11,11,11]]
def match_long_repeat(lsts):
    max_l = 0
    tmp = []
    for l in lsts:
        max_l = max(max_l, len(l))
    for l in lsts:
        if len(l) == max_l:
            tmp.append(l)
        else:
            tmp.append(repeat_last(l))
    return list(map(list, zip(*zip(*tmp))))


# longest list matching, cycle [[1,2,3,4,5] ,[10,11]] -> [[1,2,3,4,5] ,[10,11,10,11,10]]
def match_long_cycle(lsts):
    max_l = 0
    tmp = []
    for l in lsts:
        max_l = max(max_l, len(l))
    for l in lsts:
        if len(l) == max_l:
            tmp.append(l)
        else:
            tmp.append(itertools.cycle(l))
    return list(map(list, zip(*zip(*tmp))))


# cross matching
# [[1,2], [5,6,7]] -> [[1,1,1,2,2,2], [5,6,7,5,6,7]]
def match_cross(lsts):
    return list(map(list, zip(*itertools.product(*lsts))))


# use this one
# cross matching 2, more useful order
# [[1,2], [5,6,7]] ->[[1, 2, 1, 2, 1, 2], [5, 5, 6, 6, 7, 7]]
# but longer and less elegant expression
# performance difference is minimal since number of lists is usually small
def match_cross2(lsts):
    return list(reversed(list(map(list, zip(*itertools.product(*reversed(lsts)))))))


# Shortest list decides output length [[1,2,3,4,5], [10,11]] -> [[1,2], [10, 11]]
def match_short(lsts):
    return list(map(list, zip(*zip(*lsts))))


# extends list so len(l) == count
def fullList(l, count):
    d = count - len(l)
    if d > 0:
        l.extend([l[-1] for a in range(d)])
    return


def sv_zip(*iterables):
    # zip('ABCD', 'xy') --> Ax By
    # like standard zip but list instead of tuple
    sentinel = object()
    iterators = [iter(it) for it in iterables]
    while iterators:
        result = []
        for it in iterators:
            elem = next(it, sentinel)
            if elem is sentinel:
                return
            result.append(elem)
        yield result


#####################################################
################# list levels magic #################
#####################################################

# working with nesting levels
# define data floor

# data from nasting to standart: TO container( objects( lists( floats, ), ), )
def dataCorrect(data, nominal_dept=2):
    dept = levelsOflist(data)
    output = []

    if dept < 2:
        return [dept, data]
    else:
        output = dataStandart(data, dept, nominal_dept)
        return output


# from standart data to initial levels: to nasting lists  container( objects( lists( nasty_lists( floats, ), ), ), ) это невозможно!
def dataSpoil(data, dept):
    if dept:
        out = []
        for d in data:
            out.append([dataSpoil(d, dept-1)])
    else:
        out = data
    return out


# data from nasting to standart: TO container( objects( lists( floats, ), ), )
def dataStandart(data, dept, nominal_dept):
    deptl = dept - 1
    output = []
    for object in data:
        if deptl >= nominal_dept:
            output.extend(dataStandart(object, deptl, nominal_dept))
        else:
            output.append(data)
            return output
    return output


# calc list nesting only in countainment level integer
def levelsOflist(lst):
    level = 1
    for n in lst:
        if n and isinstance(n, (list, tuple)):
            level += levelsOflist(n)
        return level
    return


#####################################################
################### matrix magic ####################
#####################################################

# tools that makes easier to convert data
# from string to matrixes, vertices,
# lists, other and vise versa


def Matrix_listing(prop):
    # matrix degenerate
    mat_out = []
    for i, matrix in enumerate(prop):
        unit = []
        for k, m in enumerate(matrix):
            # [Matrix0, Matrix1, ... ]
            unit.append(m[:])
        mat_out.append((unit))
    return mat_out


def Matrix_generate(prop):
    mat_out = []
    for i, matrix in enumerate(prop):
        unit = Matrix()
        for k, m in enumerate(matrix):
            # [Matrix0, Matrix1, ... ]
            unit[k] = Vector(m)
        mat_out.append(unit)
    return mat_out


def Matrix_location(prop, list=False):
    Vectors = []
    for p in prop:
        if list:
            Vectors.append(p.translation[:])
        else:
            Vectors.append(p.translation)
    return [Vectors]


def Matrix_scale(prop, list=False):
    Vectors = []
    for p in prop:
        if list:
            Vectors.append(p.to_scale()[:])
        else:
            Vectors.append(p.to_scale())
    return [Vectors]


# returns (Vector, rotation) utility function for Matrix Destructor. if list is true
# the Vector is decomposed into tuple format.
def Matrix_rotation(prop, list=False):
    Vectors = []
    for p in prop:
        q = p.to_quaternion()
        if list:
            vec, angle = q.to_axis_angle()
            Vectors.append((vec[:], angle))
        else:
            Vectors.append(q.to_axis_angle())
    return [Vectors]


def Vector_generate(prop):
    return [[Vector(v) for v in obj] for obj in prop]


def Vector_degenerate(prop):
    return [[v[0:3] for v in object] for object in prop]


def Edg_pol_generate(prop):
    edg_pol_out = []
    if len(prop[0][0]) == 2:
        type = 'edg'
    elif len(prop[0]) > 2:
        type = 'pol'
    for ob in prop:
        list = []
        for p in ob:
            list.append(p)
        edg_pol_out.append(list)
    # [ [(n1,n2,n3), (n1,n7,n9), p, p, p, p...], [...],... ] n = vertexindex
    return type, edg_pol_out


def matrixdef(orig, loc, scale, rot, angle, vec_angle=[[]]):
    modif = []
    for i, de in enumerate(orig):
        ma = de.copy()

        if loc[0]:
            k = min(len(loc[0])-1, i)
            mat_tran = de.Translation(loc[0][k])
            ma *= mat_tran

        if vec_angle[0] and rot[0]:
            k = min(len(rot[0])-1, i)
            a = min(len(vec_angle[0])-1, i)

            vec_a = vec_angle[0][a].normalized()
            vec_b = rot[0][k].normalized()

            mat_rot = vec_b.rotation_difference(vec_a).to_matrix().to_4x4()
            ma = ma * mat_rot

        elif rot[0]:
            k = min(len(rot[0])-1, i)
            a = min(len(angle[0])-1, i)
            mat_rot = de.Rotation(radians(angle[0][a]), 4, rot[0][k].normalized())
            ma = ma * mat_rot

        if scale[0]:
            k = min(len(scale[0])-1, i)
            scale2 = scale[0][k]
            id_m = Matrix.Identity(4)
            for j in range(3):
                id_m[j][j] = scale2[j]
            ma *= id_m

        modif.append(ma)
    return modif


#####################################################
#################### lists magic ####################
#####################################################


def create_list(x, y):
    if type(y) in [list, tuple]:
        return reduce(create_list, y, x)
    else:
        return x.append(y) or x


def preobrazovatel(list_a, levels, level2=1):
    list_tmp = []
    level = levels[0]

    if level > level2:
        if type(list_a)in [list, tuple]:
            for l in list_a:
                if type(l) in [list, tuple]:
                    tmp = preobrazovatel(l, levels, level2+1)
                    if type(tmp) in [list, tuple]:
                        list_tmp.extend(tmp)
                    else:
                        list_tmp.append(tmp)
                else:
                    list_tmp.append(l)

    elif level == level2:
        if type(list_a) in [list, tuple]:
            for l in list_a:
                if len(levels) == 1:
                    tmp = preobrazovatel(l, levels, level2+1)
                else:
                    tmp = preobrazovatel(l, levels[1:], level2+1)
                list_tmp.append(tmp if tmp else l)

    else:
        if type(list_a) in [list, tuple]:
            list_tmp = reduce(create_list, list_a, [])

    return list_tmp


def myZip(list_all, level, level2=0):
    if level == level2:
        if type(list_all) in [list, tuple]:
            list_lens = []
            list_res = []
            for l in list_all:
                if type(l) in [list, tuple]:
                    list_lens.append(len(l))
                else:
                    list_lens.append(0)
            if list_lens == []:
                return False
            min_len = min(list_lens)
            for value in range(min_len):
                lt = []
                for l in list_all:
                    lt.append(l[value])
                t = list(lt)
                list_res.append(t)
            return list_res
        else:
            return False
    elif level > level2:
        if type(list_all) in [list, tuple]:
            list_res = []
            list_tr = myZip(list_all, level, level2+1)
            if list_tr is False:
                list_tr = list_all
            t = []
            for tr in list_tr:
                if type(list_tr) in [list, tuple]:
                    list_tl = myZip(tr, level, level2+1)
                    if list_tl is False:
                        list_tl = list_tr
                    t.extend(list_tl)
            list_res.append(list(t))
            return list_res
        else:
            return False


#####################################################
################### update List join magic ##########
#####################################################


def myZip_2(list_all, level, level2=1):
    def create_listDown(list_all, level):
        def subDown(list_a, level):
            list_b = []
            for l2 in list_a:
                if type(l2) in [list, tuple]:
                    list_b.extend(l2)
                else:
                    list_b.append(l2)
            if level > 1:
                list_b = subDown(list_b, level-1)
            return list_b

        list_tmp = []
        if type(list_all) in [list, tuple]:
            for l in list_all:
                list_b = subDown(l, level-1)
                list_tmp.append(list_b)
        else:
            list_tmp = list_all
        return list_tmp

    list_tmp = list_all.copy()
    for x in range(level-1):
        list_tmp = create_listDown(list_tmp, level)

    list_r = []
    l_min = []

    for el in list_tmp:
        if type(el) not in [list, tuple]:
            break

        l_min.append(len(el))

    if l_min == []:
        l_min = [0]
    lm = min(l_min)
    for elm in range(lm):
        for el in list_tmp:
            list_r.append(el[elm])

    list_tmp = list_r

    for lev in range(level-1):
        list_tmp = [list_tmp]

    return list_tmp


def joiner(list_all, level, level2=1):
    list_tmp = []

    if level > level2:
        if type(list_all) in [list, tuple]:
            for list_a in list_all:
                if type(list_a) in [list, tuple]:
                    list_tmp.extend(list_a)
                else:
                    list_tmp.append(list_a)
        else:
            list_tmp = list_all

        list_res = joiner(list_tmp, level, level2=level2+1)
        list_tmp = [list_res]

    if level == level2:
        if type(list_all) in [list, tuple]:
            for list_a in list_all:
                if type(list_a) in [list, tuple]:
                    list_tmp.extend(list_a)
                else:
                    list_tmp.append(list_a)
        else:
            list_tmp.append(list_all)

    if level < level2:
        if type(list_all) in [list, tuple]:
            for l in list_all:
                list_tmp.append(l)
        else:
            list_tmp.append(l)

    return list_tmp


def wrapper_2(l_etalon, list_a, level):
    def subWrap(list_a, level, count):
        list_b = []
        if level == 1:
            if len(list_a) == count:
                for l in list_a:
                    list_b.append([l])
            else:
                dc = len(list_a)//count
                for l in range(count):
                    list_c = []
                    for j in range(dc):
                        list_c.append(list_a[l*dc+j])
                    list_b.append(list_c)
        else:
            for l in list_a:
                list_b = subWrap(l, level-1, count)
        return list_b

    def subWrap_2(l_etalon, len_l, level):
        len_r = len_l
        if type(l_etalon) in [list, tuple]:
            len_r = len(l_etalon) * len_l
            if level > 1:
                len_r = subWrap_2(l_etalon[0], len_r, level-1)

        return len_r

    len_l = len(l_etalon)
    lens_l = subWrap_2(l_etalon, 1, level)
    list_tmp = subWrap(list_a, level, lens_l)

    for l in range(level-1):
        list_tmp = [list_tmp]
    return list_tmp


#####################################################
############### debug settings magic ################
#####################################################


def sverchok_debug(mode):
    global DEBUG_MODE
    DEBUG_MODE = mode
    return DEBUG_MODE


def setup_init():
    global DEBUG_MODE
    global HEAT_MAP
    global __package__
    # okay this set __package__ to what it should be
    __package__ = bpy.types.SverchokPreferences.bl_idname
    addon = bpy.context.user_preferences.addons.get(__package__)
    if addon:
        DEBUG_MODE = addon.preferences.show_debug
        HEAT_MAP = addon.preferences.heat_map
        
    
    
#####################################################
###############  heat map system     ################
#####################################################


def heat_map_state(state):
    global HEAT_MAP
    HEAT_MAP = state
    sv_ng = [ng for ng in bpy.data.node_groups if ng.bl_idname == 'SverchCustomTreeType']
    if state:
        for ng in sv_ng:
            color_data = {node.name: (node.color[:], node.use_custom_color) for node in ng.nodes}
            if not ng.sv_user_colors:
                ng.sv_user_colors = str(color_data)
    else:
        for ng in sv_ng:
            if not ng.sv_user_colors:
                print("{0} has no colors".format(ng.name))
                continue
            color_data = ast.literal_eval(ng.sv_user_colors)
            for name, node in ng.nodes.items():
                if name in color_data:
                    color, use = color_data[name]
                    setattr(node, 'color', color)
                    setattr(node, 'use_custom_color', use)
            ng.sv_user_colors = ""
            
#####################################################
############### update system magic! ################
#####################################################


def updateNode(self, context):
    """
    When a node has changed state and need to call a partial update.
    For example a user exposed bpy.prop
    """
    global DEBUG_MODE
    a = time.perf_counter()
    speedUpdate(start_node=self)
    b = time.perf_counter()
    if DEBUG_MODE:
        print("Partial update from node", self.name, "in", round(b-a, 4))


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
    global list_nodes4update
    ng = bpy.data.node_groups[tree_name]
    node_set = set(node_list)
    for n_t in node_types:
        node_set = node_set | {name for name, node in ng.nodes.items() if node.bl_idname == n_t}
    a_tree = make_tree_from_nodes(list(node_set), tree_name)
    return a_tree


def makeTreeUpdate2(tree=None):
    """ makes a complete update list for the tree_name, or all node trees"""
    global list_nodes4update
    global partial_update_cache
    global socket_data_cache
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
            list_nodes4update[name] = out
            partial_update_cache[name] = {}
            socket_data_cache[name] = {}


def do_update_heat_map(node_list, nodes):
    global DEBUG_MODE
    times = []
    node_list = list(node_list)
    for name in node_list:
        if name in nodes:
            start = time.perf_counter()
            nodes[name].update()
            delta = time.perf_counter()-start
            if DEBUG_MODE:
                print("Updated  {0} in:{1}".format(name, round(delta, 4)))
            times.append(delta)
    if not times:
        return
    if not nodes.id_data.sv_user_colors:
        ng = nodes.id_data
        color_data = {node.name: (node. color[:], node.use_custom_color) for node in nodes}
        nodes.id_data.sv_user_colors = str(color_data)
        
    t_max = max(times)
    
    addon = bpy.context.user_preferences.addons.get(__package__)
    if addon:
        # to use Vector.lerp
        cold = Vector(addon.preferences.heat_map_cold)
        hot =  addon.preferences.heat_map_hot
    else:
        print("Cannot find preferences")
        cold = Vector((1,1,1))
        hot = (.8,0,0)
    for name, t in zip(node_list, times):
        nodes[name].use_custom_color = True
        # linerar scale.
        nodes[name].color = cold.lerp(hot, t / t_max)


def do_update_debug(node_list, nods):
    global DEBUG_MODE
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


# master update function, has several different modes

def speedUpdate(start_node=None, tree=None, animation_mode=False):
    global list_nodes4update
    global DEBUG_MODE
    global partial_update_cache
    global HEAT_MAP
    
    def do_update(node_list, nods):
        for nod_name in node_list:
            if nod_name in nods:
                nods[nod_name].update()

    if DEBUG_MODE:
        do_update = do_update_debug
    if HEAT_MAP:
        do_update = do_update_heat_map

    # try to update optimized animation trees, not ready
    if animation_mode:
        pass
    # start from the mentioned node the, called from updateNode
    if start_node:
        tree = start_node.id_data
        if tree.name in list_nodes4update and list_nodes4update[tree.name]:
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
            makeTreeUpdate2(tree)
            do_update(itertools.chain.from_iterable(list_nodes4update[tree.name]), tree.nodes)
            return
    # draw the complete named tree, called from SverchokCustomTreeNode
    if tree:
        node_groups = [(tree.name,tree)]
    else:
        node_groups = bpy.data.node_groups.items()

    # update all node trees
    for name, ng in node_groups:
        if ng.bl_idname == 'SverchCustomTreeType':
            update_list = list_nodes4update.get(name)
            if not update_list:
                makeTreeUpdate2(ng)
                update_list = list_nodes4update.get(name)
            for l in update_list:
                do_update(l, ng.nodes)
            

def get_update_lists(ng):
    global list_nodes4update
    global partial_update_cache

    return (list_nodes4update[ng.name], partial_update_cache[ng.name])


##############################################################
##############################################################
############## changable type of socket magic ################
########### if you have separate socket solution #############
#################### wellcome to provide #####################
##############################################################
##############################################################

# node has to have self veriables:
# self.typ = bpy.props.StringProperty(name='typ', default='')
# self.newsock = bpy.props.BoolProperty(name='newsock', default=False)
# and in update:
# inputsocketname = 'data' # 'data' - name of your input socket, that defines type
# outputsocketname = ['dataTrue','dataFalse'] # 'data...' - are names of your sockets to be changed
# changable_sockets(self, inputsocketname, outputsocketname)


def check_sockets(self, inputsocketname):
    if type(self.inputs[inputsocketname].links[0].from_socket) == bpy.types.VerticesSocket:
        if self.typ == 'v':
            self.newsock = False
        else:
            self.typ = 'v'
            self.newsock = True
    if type(self.inputs[inputsocketname].links[0].from_socket) == bpy.types.StringsSocket:
        if self.typ == 's':
            self.newsock = False
        else:
            self.typ = 's'
            self.newsock = True
    if type(self.inputs[inputsocketname].links[0].from_socket) == bpy.types.MatrixSocket:
        if self.typ == 'm':
            self.newsock = False
        else:
            self.typ = 'm'
            self.newsock = True
    return


# cleaning of old not fited
def clean_sockets(self, outputsocketname):
    for n in outputsocketname:
        if n in self.outputs:
            self.outputs.remove(self.outputs[n])
    return


# main def for changable sockets type
def changable_sockets(self, inputsocketname, outputsocketname):
    if len(self.inputs[inputsocketname].links) > 0:
        check_sockets(self, inputsocketname)
        if self.newsock:
            clean_sockets(self, outputsocketname)
            self.newsock = False
            if self.typ == 'v':
                for n in outputsocketname:
                    self.outputs.new('VerticesSocket', n, n)
            if self.typ == 's':
                for n in outputsocketname:
                    self.outputs.new('StringsSocket', n, n)
            if self.typ == 'm':
                for n in outputsocketname:
                    self.outputs.new('MatrixSocket', n, n)
        else:
            self.newsock = False
    return


def get_socket_type(node, inputsocketname):
    if type(node.inputs[inputsocketname].links[0].from_socket) == bpy.types.VerticesSocket:
        return 'v'
    if type(node.inputs[inputsocketname].links[0].from_socket) == bpy.types.StringsSocket:
        return 's'
    if type(node.inputs[inputsocketname].links[0].from_socket) == bpy.types.MatrixSocket:
        return 'm'


def get_socket_type_full(node, inputsocketname):
   # this is solution, universal and future proof.
    return node.inputs[inputsocketname].links[0].from_socket.bl_idname
     # it is real solution, universal
    #if type(node.inputs[inputsocketname].links[0].from_socket) == bpy.types.VerticesSocket:
    #    return 'VerticesSocket'
    #if type(node.inputs[inputsocketname].links[0].from_socket) == bpy.types.StringsSocket:
    #    return 'StringsSocket'
    #if type(node.inputs[inputsocketname].links[0].from_socket) == bpy.types.MatrixSocket:
    #    return 'MatrixSocket'


###########################################
# Multysocket magic / множественный сокет #
###########################################

#     utility function for handling n-inputs, for usage see Test1.py
#     for examples see ListJoin2, LineConnect, ListZip
#     min parameter sets minimum number of sockets
#     setup two variables in Node class
#     create Fixed inputs socket, the multi socket will not change anything
#     below min
#     base_name = StringProperty(default='Data ')
#     multi_socket_type = StringProperty(default='StringsSocket')


def multi_socket(node, min=1, start=0, breck=False, output=False):
    '''
     min - integer, minimal number of sockets, at list 1 needed
     start - integer, starting socket.
     breck - boolean, adding brecket to nmae of socket x[0] x[1] x[2] etc
     output - integer, deal with output, if>0 counts number of outputs multy sockets
     base name added in separated node in self.base_name = 'some_name', i.e. 'x', 'data'
     node.multi_socket_type - type of socket, added in self.multi_socket_type
     as one of three sverchok types 'StringsProperty', 'MatricesProperty', 'VerticesProperty'

    '''
    #probably incorrect state due or init or change of inputs
    # do nothing
    if not len(node.inputs):
        return
    if min < 1:
        min = 1
    if not output:
        if node.inputs[-1].links:
            length = start + len(node.inputs)
            if breck:
                name = node.base_name + '[' + str(length) + ']'
            else:
                name = node.base_name + str(length)
            node.inputs.new(node.multi_socket_type, name, name)
        else:
            while len(node.inputs) > min and not node.inputs[-2].links:
                node.inputs.remove(node.inputs[-1])
    else:
        lenod = len(node.outputs)
        if lenod < output:
            length = output-lenod
            for n in range(length):
                if breck:
                    name = node.base_name + '[' + str(n+lenod-1) + ']'
                else:
                    name = node.base_name + str(n+lenod-1)
                node.outputs.new(node.multi_socket_type, name, name)
        else:
            while len(node.outputs) > output:
                node.outputs.remove(node.outputs[-1])


#####################################
# node and socket id functions      #
#####################################


# socket.name is not unique... identifier is
def socket_id(socket):
    #return hash(socket)
    return hash(socket.id_data.name+socket.node.name+socket.identifier)

# For when need a key for use with dict in node
#  create a string property like this.
#  n_id =  StringProperty(default='')
# And a copy function
#  def copy(self,node)
#      self.n_id=''
# the always use like this
# n_id = node_id(self)
# node_dict[n_id]['key']


def node_id(node):
    if not node.n_id:
        node.n_id = str(hash(node) ^ hash(time.monotonic()))
    return node.n_id


#####################################
# socket data cache                 #
#####################################


def SvGetSocketAnyType(self, socket, deepcopy=True):
    out = SvGetSocket(socket, deepcopy)
    if out:
        return out
    else:
        return []


def SvSetSocketAnyType(self, socket_name, out):
    SvSetSocket(self.outputs[socket_name], out)
    return

# faster than builtin deep copy for us.
# useful for our limited case
# we should be able to specify vectors here to get them create
# or stop destroying them when in vector socket.


def sv_deep_copy(lst):
    if isinstance(lst, (list, tuple)):
        if lst and not isinstance(lst[0], (list, tuple)):
            return lst[:]
        return [sv_deep_copy(l) for l in lst]
    return lst


# Build string for showing in socket label
def SvGetSocketInfo(socket):
    def build_info(data):
        if not data:
            return str(data)
        #if isinstance(data,list):
            #return '['+build_info(data[0])
        #elif isinstance(data,tuple):
            #return '('+build_info(data[0])
        else:
            return str(data)
    global socket_data_cache
    ng = socket.id_data.name
    if socket.is_output:
        s_id = socket_id(socket)
    elif socket.links:
        s_id = socket_id(socket.links[0].from_socket)
    else:
        return ''
    if ng in socket_data_cache:
        if s_id in socket_data_cache[ng]:
            data = socket_data_cache[ng][s_id]
            if data:
                return str(len(data))
    return ''


def SvSetSocket(socket, out):
    global socket_data_cache
    if not socket.is_output:
        print("Warning, setting input socket")
    s_id = socket_id(socket)
    s_ng = socket.id_data.name
    if s_ng not in socket_data_cache:
        socket_data_cache[s_ng] = {}
    socket_data_cache[s_ng][s_id] = out


def SvGetSocket(socket, deepcopy = True):
    global socket_data_cache
    global DEBUG_MODE
    if socket.links:
        other = socket.links[0].from_socket
        s_id = socket_id(other)
        s_ng = other.id_data.name
        if s_ng not in socket_data_cache:
            return None
        if s_id in socket_data_cache[s_ng]:
            out = socket_data_cache[s_ng][s_id]
            if deepcopy:
                return sv_deep_copy(out)
            else:
                return out
        else:  # failure, should raise error in future
            if DEBUG_MODE:
#                traceback.print_stack()
                print("cache miss:", socket.node.name, "->", socket.name, "from:", other.node.name, "->", other.name)
    return None


####################################
# быстрый сортировщик / quick sorter
####################################

def svQsort(L):
    if L: return svQsort([x for x in L[1:] if x<L[0]]) + L[0:1] + svQsort([x for x in L[1:] if x>=L[0]])
    return []
