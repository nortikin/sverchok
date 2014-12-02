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
from math import radians
import itertools
import time
import ast
import bpy
from mathutils import Vector, Matrix

global bmesh_mapping, per_cache

DEBUG_MODE = False
HEAT_MAP = False
RELOAD_EVENT = False

# this is set correctly later.
SVERCHOK_NAME = "sverchok"

#handle for object in node
temp_handle = {}
# cache node group update trees it not used, as i see
# cache_nodes = {}
# socket cache
socket_data_cache = {}
# for viewer baker node cache
cache_viewer_baker = {}
sv_Vars = {}
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
    return (True, temp_handle[handle]['prop'])

def handle_write(handle, prop):
    handle_delete(handle)
    
    temp_handle[handle] = {"prop" : prop}

def handle_check(handle, prop):
    if handle in handle_check and \
            prop == handle_check[handle]['prop']:
        return True
    return False


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
    if not dept: # for empty lists 
        return []
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
    return 0


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
    return [[v[0:3] for v in obj] for obj in prop]


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
    global SVERCHOK_NAME
    import sverchok
    SVERCHOK_NAME = sverchok.__name__
    addon = bpy.context.user_preferences.addons.get(SVERCHOK_NAME)
    if addon:
        DEBUG_MODE = addon.preferences.show_debug
        HEAT_MAP = addon.preferences.heat_map
    else:
        print("Setup of preferences failed")
    
    
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
    Old, use process_node instead
    When a node has changed state and need to call a partial update.
    For example a user exposed bpy.prop
    """
    self.process_node(context)
    
##############################################################
##############################################################
############## changable type of socket magic ################
########### if you have separate socket solution #############
#################### wellcome to provide #####################
##############################################################
##############################################################

def changable_sockets(node, inputsocketname, outputsocketname):
    '''
    arguments: node, name of socket to follow, list of socket to change
    '''
    in_socket = node.inputs[inputsocketname]
    ng = node.id_data
    if in_socket.links:
        in_other = get_other_socket(in_socket)
        if not in_other:
            return
        outputs = node.outputs
        s_type = in_other.bl_idname
        if outputs[outputsocketname[0]].bl_idname != s_type:
            node.id_data.freeze(hard=True)
            to_links = {}
            for n in outputsocketname:
                out_socket = outputs[n]
                to_links[n] = [l.to_socket for l in out_socket.links]
                outputs.remove(outputs[n])
            for n in outputsocketname:
                new_out_socket = outputs.new(s_type, n)
                for to_socket in to_links[n]:
                    ng.links.new(to_socket, new_out_socket)
            node.id_data.unfreeze(hard=True)

def get_socket_type_full(node, inputsocketname):
    socket = node.inputs[inputsocketname]
    other = get_other_socket(socket)
    return other.links[0].from_socket.bl_idname

def replace_socket(socket, new_type, new_name=None, new_pos=None):
    '''
    Replace a socket and keep links
    '''
    if new_name is None:
        new_name = socket.name
    socket.name = new_name    
    # quit early
    #if socket.bl_idname == new_type:
    #    return socket
    ng = socket.id_data
    ng.freeze()
    if socket.is_output:
        to_sockets = [l.to_socket for l in socket.links]
        outputs = socket.node.outputs
        if new_pos is None:
            for i,s in enumerate(outputs):
                if s == socket:
                    node_pos = i
                    break
        else:
            node_pos = new_pos
            
        outputs.remove(socket)
        new_socket = outputs.new(new_type, new_name)
        outputs.move(len(outputs)-1, node_pos)
        for to_socket in to_sockets:
            ng.links.new(new_socket, to_socket)
    else:
        if socket.is_linked:
            from_socket = socket.links[0].from_socket
        else:
            from_socket = None
        inputs = socket.node.inputs
        if new_pos is None:
            for i,s in enumerate(inputs):
                if s == socket:
                    node_pos = i
                    break
        else:
            node_pos = new_pos
        inputs.remove(socket)
        new_socket = inputs.new(new_type, new_name)
        inputs.move(len(inputs)-1, node_pos)
        if from_socket:
            ng.links.new(from_socket, new_socket)
    ng.unfreeze()
    return new_socket
    
def get_other_socket(socket):
    """ 
    Get next real upstream socket.
    This should be expanded to support wifi nodes also.
    Will return None if there isn't a another socket connect
    so no need to check socket.links
    """
    if socket.is_linked and not socket.is_output:
        other = socket.links[0].from_socket
        if other.node.bl_idname == 'NodeReroute':
            return get_other_socket(other.node.inputs[0])
        else:  #other.node.bl_idname == 'WifiInputNode':
            return other
    return None

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

# the named argument min will be replaced soonish.

def multi_socket(node, min=1, start=0, breck=False, out_count=None):
    '''
     min - integer, minimal number of sockets, at list 1 needed
     start - integer, starting socket.
     breck - boolean, adding bracket to name of socket x[0] x[1] x[2] etc
     output - integer, deal with output, if>0 counts number of outputs multy sockets
     base name added in separated node in self.base_name = 'some_name', i.e. 'x', 'data'
     node.multi_socket_type - type of socket, as .bl_idname 

    '''
    #probably incorrect state due or init or change of inputs
    # do nothing
    ng = node.id_data
            
    if min < 1:
        min = 1
    if out_count is None:
        if not node.inputs:
            return
        if node.inputs[-1].links:
            length = start + len(node.inputs)
            if breck:
                name = node.base_name + '[' + str(length) + ']'
            else:
                name = node.base_name + str(length)
            node.inputs.new(node.multi_socket_type, name)
        else:
            while len(node.inputs) > min and not node.inputs[-2].links:
                node.inputs.remove(node.inputs[-1])
    elif isinstance(out_count, int):
        lenod = len(node.outputs)
        ng.freeze(True)
        print(out_count)
        if out_count > 30:
            out_count = 30
        if lenod < out_count:
            while len(node.outputs) < out_count:
                length = start + len(node.outputs)
                if breck:
                    name = node.base_name + '[' + str(length)+ ']'
                else:
                    name = node.base_name + str(length)
                node.outputs.new(node.multi_socket_type, name)
        else:
            while len(node.outputs) > out_count:
                node.outputs.remove(node.outputs[-1])
        ng.unfreeze(True)

#####################################
# node and socket id functions      #
#####################################


# socket.name is not unique... identifier is
def socket_id(socket):
    #return hash(socket)
    return str(hash(socket.id_data.name + socket.node.name + socket.identifier))+socket.node.name+socket.name

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


def SvGetSocketAnyType(self, socket, default=None, deepcopy=True):
    out = SvGetSocket(socket, deepcopy)
    if socket.is_linked:
        return SvGetSocket(socket, deepcopy)
    elif default:
        return default
    else:
        raise LookupError


def SvSetSocketAnyType(self, socket_name, out):
    SvSetSocket(self.outputs[socket_name], out)

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

    global socket_data_cache
    ng = socket.id_data.name
    
    if socket.is_output:
        s_id = socket_id(socket)
    elif socket.links:
        s_id = socket_id(get_other_socket(socket))
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
        print("Warning, {} setting input socket: {}".format(socket.node.name, socket.name))
    if not socket.is_linked:
        print("Warning: {} setting unconncted socket: {}".format(socket.node.name, socket.name))
    s_id = socket_id(socket)
    s_ng = socket.id_data.name
    if s_ng not in socket_data_cache:
        socket_data_cache[s_ng] = {}
    socket_data_cache[s_ng][s_id] = out


def SvGetSocket(socket, deepcopy=True):
    global socket_data_cache
    global DEBUG_MODE
    if socket.is_linked:
        other = get_other_socket(socket)
        s_id = socket_id(other)
        s_ng = other.id_data.name
        if s_ng not in socket_data_cache:
            raise LookupError
        if s_id in socket_data_cache[s_ng]:
            out = socket_data_cache[s_ng][s_id]
            if deepcopy:
                return sv_deep_copy(out)
            else:
                return out
        else:
            if DEBUG_MODE:
                print("cache miss:", socket.node.name, "->", socket.name, "from:", other.node.name, "->", other.name)
            raise SvNoDataError
    # not linked
    raise SvNoDataError

class SvNoDataError(LookupError):
    pass

def reset_socket_cache(ng):
    """
    Reset socket cache either for node group.
    """
    global socket_data_cache
    socket_data_cache[ng.name] = {}
        

####################################
# быстрый сортировщик / quick sorter
####################################

def svQsort(L):
    if L: return svQsort([x for x in L[1:] if x<L[0]]) + L[0:1] + svQsort([x for x in L[1:] if x>=L[0]])
    return []

