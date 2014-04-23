import bpy, bmesh, mathutils
from mathutils import Vector, Matrix
from node_s import *
global bmesh_mapping, per_cache
from functools import reduce
from math import radians
import itertools
import collections
import time
import copy

DEBUG_MODE = False
DEBUG_SETTINGS = {}
bmesh_mapping = {}
per_cache = {}
temp_handle = {}
cache_nodes = {}
list_nodes4update = {}
sv_Vars = {}
socket_data_cache = {}


#####################################################
################### update magic ####################
#####################################################

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
    if cnode=='ALL':
        for i in cache_nodes.items:
            del cache_nodes[i]
    else:
        if read_cnodes(cnode)!=None:
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
    if read_cnodes('LOCK UPDATE CNODES')==1:
        return False

    etalon = read_cnodes('GLOBAL CNODE')
    if etalon == None:
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
    if bm_ref=='ALL':
        for i in bmesh_mapping.items:
            del bmesh_mapping[i]
    else:
        if read_bm(bm_ref)!=None:
            del bmesh_mapping[bm_ref]


#####################################################
################### cache magic #####################
#####################################################
'''
def cache_delete(cache):
    if cache in per_cache:
       del per_cache[cache]


def cache_read(cache):
    # current tool not cached yet
    if not (cache in per_cache):
        return(False, False, False, False, False, False, False)

    recipient = per_cache[cache]["recipient"]
    donor = per_cache[cache]["donor"]
    centres = per_cache[cache]["centres"]
    formula = per_cache[cache]["formula"]
    diap_min = per_cache[cache]["diap_min"]
    diap_max = per_cache[cache]["diap_max"]

    return(True, recipient, donor, centres, formula, diap_min, diap_max)


# store information in the cache
def cache_write(cache, recipient, donor, centres, formula, diap_min, diap_max):
    # clear cache of current tool
    if cache in per_cache:
        #del per_cache[cache]
        if recipient != per_cache[cache]['recipient']: cache_delete(cache)
        elif donor != per_cache[cache]['donor']: cache_delete(cache)
        elif centres != per_cache[cache]['centres']: cache_delete(cache)
        elif formula != per_cache[cache]['formula']: cache_delete(cache)
        elif diap_min != per_cache[cache]['diap_min']: cache_delete(cache)
        elif diap_max != per_cache[cache]['diap_max']: cache_delete(cache)

    # update cache
    if not (cache in per_cache) and cache!='':
        per_cache[cache] = {"recipient": recipient, "donor": donor,
            "centres": centres, "formula": formula,
            "diap_min":diap_min, "diap_max":diap_max}


def cache_check(cache, recipient, donor, centres, formula, diap_min, diap_max):
    result = True
    if cache in per_cache:
        if recipient != per_cache[cache]['recipient'] \
            or donor != per_cache[cache]['donor'] \
            or centres != per_cache[cache]['centres'] \
            or formula != per_cache[cache]['formula'] \
            or diap_min != per_cache[cache]['diap_min'] \
            or diap_max != per_cache[cache]['diap_max']:
                cache_delete(cache)
                result = False
    else:
        result = False
    return result
'''

def handle_delete(handle):
    if handle in temp_handle:
       del temp_handle[handle]


def handle_read(handle):
    if not (handle in temp_handle):
        return (False, False)

    prop = temp_handle[handle]['prop']
    return (True, prop)


def handle_write(handle, prop):
    if handle in temp_handle:
        if prop != temp_handle[handle]['prop']: handle_delete(handle)

    if not (handle in temp_handle) and handle !='':
        temp_handle[handle] = {"prop": prop}


def handle_check(handle, prop):
    result = True
    if handle in handle_check:
        if prop != handle_check[handle]['prop']:
                result = False
    else:
        result = False
    return result

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
        max_l = max(max_l,len(l))
    for l in lsts:
        if len(l)==max_l:
            tmp.append(l)
        else:
            tmp.append(repeat_last(l))

    return list(map( list, zip(*zip(*tmp))))

# longest list matching, cycle [[1,2,3,4,5] ,[10,11]] -> [[1,2,3,4,5] ,[10,11,10,11,10]]
def match_long_cycle(lsts):
    max_l = 0
    tmp = []
    for l in lsts:
        max_l = max(max_l,len(l))
    for l in lsts:
        if len(l)==max_l:
            tmp.append(l)
        else:
            tmp.append(itertools.cycle(l))
    return list(map( list, zip(*zip(*tmp))))

# cross matching
# [[1,2], [5,6,7]] -> [[1,1,1,2,2,2], [5,6,7,5,6,7]]
def match_cross(lsts):
    return list(map(list,zip(*itertools.product(*lsts))))

# use this one
# cross matching 2, more useful order
# [[1,2], [5,6,7]] ->[[1, 2, 1, 2, 1, 2], [5, 5, 6, 6, 7, 7]]
# but longer and less elegant expression
# performance difference is minimal since number of lists is usually small

def match_cross2(lsts):
    return list(reversed(list(map(list,zip(*itertools.product(*reversed(lsts)))))))


# Shortest list decides output length [[1,2,3,4,5], [10,11]] -> [[1,2], [10, 11]]
def match_short(lsts):
    return list(map(list,zip(*zip(*lsts))))

# extends list so len(l) == count

def fullList(l, count):
    d = count - len(l)
    if d > 0:
        l.extend([l[-1] for a in range(d)])
    return

def sv_zip(*iterables):
    # zip('ABCD', 'xy') --> Ax By
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
    if not lst:
        return 1
    level = 1
    for n in lst:
        if n and isinstance(n,(list,tuple)): 
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
            vec,angle=q.to_axis_angle()
            Vectors.append(( vec[:], angle))
        else:
            Vectors.append(q.to_axis_angle())
    return [Vectors]

#def Vector_generate(prop):
#    vec_out = []
#    for i, object in enumerate(prop):  # lists by objects
#        veclist = []
#        for v in object: # verts
#            veclist.append(Vector(v[:]))
#        vec_out.append(veclist)
#    return vec_out

#  about 30% quicker

def Vector_generate(prop):
    return [[Vector(v) for v in obj] for obj in prop]

def Vector_degenerate(prop):
    vec_out = []
    for i, object in enumerate(prop):  # lists by objects
        veclist = []
        for v in object: # verts
            veclist.append((v[:]))
        vec_out.append(veclist)
    return vec_out



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
            k = min(len(loc[0])-1,i)
            mat_tran = de.Translation(loc[0][k])
            ma *= mat_tran

        if scale[0]:
            k = min(len(scale[0])-1,i)
            scale2=scale[0][k]
            id_m = Matrix.Identity(4)
            for j in range(3):
                id_m[j][j] = scale2[j]
            ma *= id_m

        if vec_angle[0] and rot[0]:
            k = min(len(rot[0])-1,i)
            a = min(len(vec_angle[0])-1,i)

            vec_a = vec_angle[0][a].normalized()
            vec_b = rot[0][k].normalized()

            mat_rot = vec_b.rotation_difference(vec_a).to_matrix().to_4x4()
            ma = ma * mat_rot

        elif rot[0]:
            k = min(len(rot[0])-1,i)
            a = min(len(angle[0])-1,i)
            mat_rot = de.Rotation(radians(angle[0][a]), 4, rot[0][k].normalized())
            ma = ma * mat_rot

        modif.append(ma)
    return modif

#####################################################
#################### lists magic ####################
#####################################################

def create_list(x, y):
    if type(y) in [list, tuple]:
        return reduce(create_list,y,x)
    else:
        return x.append(y) or x

def preobrazovatel(list_a,levels,level2=1):
    list_tmp = []
    level = levels[0]

    if level>level2:
        if type(list_a)in [list, tuple]:
            for l in list_a:
                if type(l) in [list, tuple]:
                    tmp = preobrazovatel(l,levels,level2+1)
                    if type(tmp) in [list, tuple]:
                        list_tmp.extend(tmp)
                    else:
                        list_tmp.append(tmp)
                else:
                    list_tmp.append(l)

    elif level==level2:
        if type(list_a) in [list, tuple]:
            for l in list_a:
                if len(levels)==1:
                    tmp = preobrazovatel(l,levels,level2+1)
                else:
                    tmp = preobrazovatel(l,levels[1:],level2+1)
                list_tmp.append(tmp if tmp else l)

    else:
        if type(list_a) in [list, tuple]:
            list_tmp = reduce(create_list,list_a,[])

    return list_tmp


def myZip(list_all, level, level2=0):
    if level==level2:
        if type(list_all) in [list, tuple]:
            list_lens = []
            list_res = []
            for l in list_all:
                if type(l) in [list, tuple]:
                    list_lens.append(len(l))
                else:
                    list_lens.append(0)
            if list_lens==[]:return False
            min_len=min(list_lens)
            for value in range(min_len):
                lt=[]
                for l in list_all:
                    lt.append(l[value])
                t = list(lt)
                list_res.append(t)
            return list_res
        else:
            return False
    elif level>level2:
        if type(list_all) in [list, tuple]:
            list_res = []
            list_tr = myZip(list_all, level, level2+1)
            if list_tr==False:
                list_tr = list_all
            t = []
            for tr in list_tr:
                if type(list_tr) in [list, tuple]:
                    list_tl = myZip(tr, level, level2+1)
                    if list_tl==False:
                        list_tl=list_tr
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
            if level>1:
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

    if l_min==[]: l_min=[0]
    lm = min(l_min)
    for elm in range(lm):
        for el in list_tmp:
            list_r.append(el[elm])

    list_tmp = list_r

    for lev in range(level-1):
        list_tmp=[list_tmp]

    return list_tmp


def joiner(list_all, level, level2=1):
    list_tmp = []

    if level>level2:
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

    if level==level2:
        if type(list_all) in [list, tuple]:
            for list_a in list_all:
                if type(list_a) in [list, tuple]:
                    list_tmp.extend(list_a)
                else:
                    list_tmp.append(list_a)
        else:
            list_tmp.append(list_all)

    if level<level2:
        if type(list_all) in [list, tuple]:
            for l in list_all:
                list_tmp.append(l)
        else:
            list_tmp.append(l)

    return list_tmp


def wrapper_2(l_etalon, list_a, level):
    def subWrap(list_a, level, count):
        list_b = []
        if level==1:
            if len(list_a)==count:
                for l in list_a:
                    list_b.append([l])
            else:
                dc=len(list_a)//count
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
            if level>1:
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

def sv_debug_update(self,context):
    if sverchok_debug(mode=self.debug_mode):
        if self.show_updated_nodes:
            sverchok_debug(key='show_updated_nodes', value=self.show_updated_nodes)
        else:
            sverchok_debug(key='show_updated_nodes')
        if self.print_timings:
            sverchok_debug(key='print_timings', value=self.print_timings)
        else:
            sverchok_debug(key='print_timings')



def sverchok_debug(mode = None,key=None,value=None):
    global DEBUG_MODE
    global DEBUG_SETTINGS
    if mode != None:
        DEBUG_MODE = mode
    if key != None and value != None:
        DEBUG_SETTINGS[key]=value
    if key != None and value == None:
        if key in DEBUG_SETTINGS:
            del DEBUG_SETTINGS[key]
    return DEBUG_MODE

#####################################################
############### update sockets magic ################
#####################################################


def updateAllOuts(self, update_self=True):
    if update_self:
        self.update()
    #print('update_node ', self.name)
    for output in self.outputs:
        if output.links:
            for link in output.links:
                nod = link.to_socket.node
                if check_update_node(nod.name, True):
                    updateAllOuts(nod)



def updateSlot(self, context):
    return

def updateNode(self, context):
    global DEBUG_MODE
    global DEBUG_SETTINGS
    a=time.time()
    speedUpdate(self.name,self.id_data.name)
    b=time.time()
    if DEBUG_MODE:
        print("Partial update from node",self.name,"in",round(b-a,4))

    '''
    if not ini_update_cnode(self.name):
        return

    updateAllOuts(self)
    is_updated_cnode()'''

'''
def updateTreeNode(self, context):
    for ng in context.blend_data.node_groups:
        for nod in ng.nodes:
            flag=False
            for inputs in nod.inputs:
                if inputs.links:
                    Flag=True
                    break

            if flag:
                continue

            ini_update_cnode(nod.name)
            lock_updated_cnode()
            updateAllOuts(nod)
            is_updated_cnode()

        #ng.interface_update(bpy.context)'''

# old function, kept while evaluating new solution.
# look at makeTreeUpdate2() and make_update_list()
# if you try to use this now you might have to change speedUpdate...
def makeTreeUpdate():
    global list_nodes4update
    def insertnode(nod, nodeset, etalonset, priority):
        if nod.name not in etalonset and nod.name not in priority:
            nodeset.append(nod.name)
            for output in nod.outputs:
                for link in output.links:
                    nod_ = link.to_socket.node
                    insertnode(nod_, nodeset, etalonset, priority)
                    if nodeset:
                        if len(nod_.name)>4 and nod_.name[:5]=='WifiI':
                            priority = nodeset + priority
                            nodeset = []
                        else:
                            idx = min(len(etalonset)-1, 0)
                            etalonset = etalonset[:idx]+nodeset + etalonset[idx:]
                            nodeset = []

        elif nod.name in priority:
            idx = priority.index(nod.name)
            priority = priority[:idx]+nodeset + priority[idx:]
            nodeset = []

        elif nodeset:
            idx = etalonset.index(nod.name)
            etalonset = etalonset[:idx]+nodeset + etalonset[idx:]
            nodeset = []

        return etalonset, priority


    for ng in bpy.context.blend_data.node_groups:
        nodeset_e=[]
        prioritet = []
        for nod in ng.nodes:
            flag=False
            for input in nod.inputs:
                if input.links:
                    Flag=True
                    break
            if flag:
                continue

            nodeset_a = []
            nodeset_e, prioritet = insertnode(nod, nodeset_a, nodeset_e, priority=prioritet)

        list_nodes4update[ng.name] = prioritet + nodeset_e
        #print("MaketreeUpdate()",list_nodes4update[ng.name])
    list_nodes4update['TreeName'] = bpy.context.space_data.node_tree.name
    return



def make_update_list(node_tree,node_set = None):
    """ Makes a list for updates from a node_group
    if a node set is passed only the subtree defined by the node set is used. Otherwise
    the complete node tree is used.
    """

    deps = {}
    # get nodes, select root nodes, wifi nodes and create dependencies for each node
    # 70-80% of the time is in the first loop
    #  stack for traversing node graph
    tree_stack = collections.deque()
    wifi_out = []
    wifi_in = []
    if not node_tree in bpy.data.node_groups:
        return []
    ng = bpy.data.node_groups[node_tree]
    node_list = []
    if not node_set: # if no node_set, take all
        node_set = set(ng.nodes.keys())
    for name,node in [(node_name,ng.nodes[node_name]) for node_name in node_set]:
        node_dep = []
        for socket in node.inputs:
            if socket.links and socket.links[0].from_node.name in node_set:
                if socket.links[0].is_valid:
                    node_dep.append(socket.links[0].from_node.name)
                else: #invalid node tree. Join nodes with F gives one instance of this, then ok
                    #print("Invalid Link in",node_tree,"!",socket.name,"->",socket.links[0].from_socket.name)
                    return []
        is_root = True
        for socket in node.outputs:
            if socket.links:
                is_root = False
                break
        # ignore nodes without input or outputs, like frames
        if node_dep or len(node.inputs) or len(node.outputs):
            deps[name]=node_dep
        if is_root and node_dep and not node.bl_idname == 'WifiInNode':
            tree_stack.append(name)
        if node.bl_idname == 'WifiOutNode':
            wifi_out.append(name)
        if node.bl_idname == 'WifiInNode':
            wifi_in.append(name)

    # create wifi out dependencies
    for wifi_out_node in wifi_out:
        wifi_dep = []
        for wifi_in_node in wifi_in:
            if ng.nodes[wifi_out_node].var_name == ng.nodes[wifi_in_node].var_name:
                wifi_dep.append(wifi_in_node)
        if wifi_dep:
            deps[wifi_out_node]=wifi_dep
        else:
            print("Broken Wifi dependency:",wifi_out_node,"-> var:",ng.nodes[wifi_out_node].var_name)
            return []

    if tree_stack:
        name = tree_stack.pop()
    else:
        if len(deps):
            tmp = list(deps.keys())
            name = tmp[0]
        else: # no nodes
            return []

    out = collections.OrderedDict()

    # travel in node graph create one sorted list of nodes based on dependencies
    node_count = len(deps)
    while node_count > len(out):
        node_dependencies = True
        for dep_name in deps[name]:
            if not dep_name in out:
                tree_stack.append(name)
                name = dep_name
                node_dependencies = False
                break
        if len(tree_stack) > node_count:
            print("Invalid node tree!")
            return []
        # if all dependencies are in out
        if node_dependencies:
            if not name in out:
                out[name]=1
                del deps[name]
            if tree_stack:
                name = tree_stack.pop()
            else:
                if node_count == len(out):
                    break
                for node_name in deps.keys():
                    name=node_name
                    break

    return list(out.keys())

def makeTreeUpdate2(tree_name=None):
    """ makes a complete update list for the current node tree"""
    global list_nodes4update
    global socket_data_cache
    # clear cache on every full update
    socket_data_cache.clear()
    if tree_name != None:
        list_nodes4update[tree_name] = make_update_list(tree_name)
        list_nodes4update['TreeName'] = tree_name
    else:
        for ng in bpy.data.node_groups[:]:
            if ng.bl_idname == 'SverchCustomTreeType':
                list_nodes4update[ng.name]=make_update_list(ng.name)
#           print(list_nodes4update[ng.name])
        list_nodes4update['TreeName'] = bpy.context.space_data.node_tree.name




def make_tree_from_nodes(node_names,tree_name):
    """
    Create a partial update list from a sub-tree, node_names is a list of node that
    drives change for the tree
    Only nodes downtree from node_name are updated
    """
    if not node_names:
        print("No nodes!")
        return make_update_list(tree_name)
    ng = bpy.data.node_groups[tree_name]
    out_set = set(node_names)
    current_node = node_names.pop()
    out_stack = node_names[:]
    wifi_out = []
    # build the set of nodes that needs to be updated
    while current_node:
        if ng.nodes[current_node].bl_idname == 'WifiInNode':
            if not wifi_out:  # build only if needed
                wifi_out = [name for name in ng.nodes.keys() if ng.nodes[name].bl_idname == 'WifiOutNode']
            for wifi_out_node in wifi_out:
                if ng.nodes[current_node].var_name == ng.nodes[current_node].var_name:
                    if not wifi_out_node in out_set:
                        out_stack.append(wifi_out_node)
                        out_set.add(wifi_out_node)
        for socket in ng.nodes[current_node].outputs:
            if socket.links:
                for link in socket.links:
                    if not link.to_node.name in out_set:
                        out_set.add(link.to_node.name)
                        out_stack.append(link.to_node.name)
        if out_stack:
            current_node = out_stack.pop()
        else:
            current_node = ''
    return make_update_list(tree_name,out_set)

# to make update tree based on node types and node names bases
# no used yet
# should add a check do find animated or driven nodes.

def make_animation_tree(node_types,node_list,tree_name):
    global list_nodes4update
    ng = bpy.data.node_groups[tree_name]
    node_set = set(node_list)
    for n_t in node_types:
        node_set = node_set | {name for name in ng.nodes.keys() if ng.nodes[name].bl_idname == n_t}
    #print("make ani tree",node_set)
    a_tree = make_tree_from_nodes(list(node_set),tree_name)
    #print("make anitree2",a_tree)
    if "SverchokAnimationTree" in list_nodes4update:
        a_tree_list = list_nodes4update["SverchokAnimationTree"]
        if not tree_name in a_tree_list:
            a_tree_list.append(tree_name)
            list_nodes4update["SverchokAnimationTree"]=a_tree_list
    else:
        list_nodes4update["SverchokAnimationTree"]=[tree_name]
    #print(a_tree)
    if a_tree:
        list_nodes4update["SverchokAnimationTree"+tree_name]=a_tree



# master update function, has several different modes

def speedUpdate(start_node = None, tree_name = None, animation_mode = False):
    global list_nodes4update
    global socket_data_cache
    global DEBUG_MODE
    global DEBUG_SETTINGS

    def do_update(node_list,nods):
        for nod_name in node_list:
            if nod_name in nods:
                if DEBUG_MODE:
                    if 'print_timings' in DEBUG_SETTINGS:
                        start = time.time()
                nods[nod_name].update()
                if DEBUG_MODE:
                    if 'print_timings' in DEBUG_SETTINGS:
                        stop = time.time()
                        print("Updated: ",nod_name, " in ", round(stop-start,4))
                    if 'show_updated_nodes' in DEBUG_SETTINGS:
                        nods[nod_name].use_custom_color = True
                        nods[nod_name].color = (0.1,.8,0)

    # try to update optimized animation trees
    if animation_mode:
        if not "SverchokAnimationTree" in list_nodes4update:
            print("No animation data")
            return
        for ng in list_nodes4update["SverchokAnimationTree"]:
            nods = bpy.data.node_groups[ng].nodes
            do_update(list_nodes4update["SverchokAnimationTree"+ng],nods)
        return
    # start from the mentioned node the, called from updateNode
    if start_node != None:
        if tree_name in list_nodes4update:
            update_list = make_tree_from_nodes([start_node],tree_name)
            nods = bpy.data.node_groups[tree_name].nodes
            do_update(update_list,nods)
            return
        else:
            socket_data_cache.clear()
            makeTreeUpdate2()
    # draw the named tree, called from SverchokCustomTreeNode
    if tree_name != None:
        if not tree_name in list_nodes4update:
            makeUpdateTree2(tree_name)
        if not tree_name in bpy.data.node_groups:
            return #start up is not complete
        nods = bpy.data.node_groups[tree_name].nodes
        do_update(list_nodes4update[tree_name],bpy.data.node_groups[tree_name].nodes)
        return

    if 'TreeName' in list_nodes4update:
        NodeTree_name = list_nodes4update['TreeName']
    else:
        NodeTree_name = bpy.context.space_data.node_tree.name
        list_nodes4update['TreeName'] = NodeTree_name

    for ng_name in list_nodes4update:
        if ng_name in bpy.context.blend_data.node_groups and ng_name==NodeTree_name:
            nods = bpy.data.node_groups[ng_name].nodes
            do_update(list_nodes4update[ng_name],nods)

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

def SvGetSocketAnyType(self, socket):

    out = SvGetSocket(socket)
    if out :
        return out
    else:
        return []
    #if type(socket.links[0].from_socket) == bpy.types.StringsSocket:
    #    typeresult = eval(socket.links[0].from_socket.StringsProperty)
    #elif type(socket.links[0].from_socket) == bpy.types.VerticesSocket:
    #    typeresult = eval(socket.links[0].from_socket.VerticesProperty)
    #elif type(socket.links[0].from_socket) == bpy.types.MatrixSocket:
    #    typeresult = eval(socket.links[0].from_socket.MatrixProperty)
    #return typeresult


def SvSetSocketAnyType(self, socket_name, out):
    SvSetSocket(self.outputs[socket_name],out)
    return
    # R/W decision point, to test performance without
    # writing to string props, uncomment. will break if any used node
    # is not using SvGet/SvSet
    #if DEBUG_MODE:
    #    return
    #if type(self.outputs[socket_name]) == bpy.types.StringsSocket:
    #    self.outputs[socket_name].StringsProperty = str(out)
    #elif type(self.outputs[socket_name]) == bpy.types.VerticesSocket:
    #    self.outputs[socket_name].VerticesProperty = str(out)
    #elif type(self.outputs[socket_name]) == bpy.types.MatrixSocket:
    #    self.outputs[socket_name].MatrixProperty = str(out)

# caching data solution

# socket.name is not unique... identifier is
def socket_id(socket):
    return socket.id_data.name+socket.node.name+socket.identifier

# faster than builtin deep copy for us.
# useful for our limited case
# we should be able to specify vectors here to get them create
# or stop destroying them when in vector socket.

def sv_deep_copy(lst):
    if isinstance(lst,(list,tuple)):
        if lst and not isinstance(lst[0],(list,tuple)):
            return lst[:]
        return [sv_deep_copy(l) for l in lst]
    return lst

# Build string for showing in socket label

def SvGetSocketInfo(socket):    
    def build_info(data):
        if not data:
            return str(data)
        if isinstance(data,list):
            return '['+build_info(data[0])
        elif isinstance(data,tuple):
            return '('+build_info(data[0])
        else:
            return str(data)
            
    global socket_data_cache
    s_id = socket_id(socket)
    if s_id in socket_data_cache:
        data = socket_data_cache[s_id]
        if data:
            return build_info(data)[:7]    
    
    return ''
        
def SvSetSocket(socket, out):
    global socket_data_cache
    s_id = socket_id(socket)
    if s_id in socket_data_cache:
        del socket_data_cache[s_id]
    socket_data_cache[s_id]=copy.copy(out)

def SvGetSocket(socket, copy = False):
    global socket_data_cache
    global DEBUG_MODE
    if socket.links:
        other =  socket.links[0].from_socket
        s_id = socket_id(other)
        if s_id in socket_data_cache:
            out = socket_data_cache[s_id]
            if copy:
                return out.copy()
            else:
                return sv_deep_copy(out)
        else: # failure, should raise error in future
            if DEBUG_MODE:
                print("cache miss:",socket.node.name,"->",socket.name,"from:",other.node.name,"->",other.name)
    return None

def get_socket_type(node, inputsocketname):
    if type(node.inputs[inputsocketname].links[0].from_socket) == bpy.types.VerticesSocket:
        return 'v'
    if type(node.inputs[inputsocketname].links[0].from_socket) == bpy.types.StringsSocket:
        return 's'
    if type(node.inputs[inputsocketname].links[0].from_socket) == bpy.types.MatrixSocket:
        return 'm'

#####################################
# Multysocket / множественный сокет #
#####################################

#     utility function for handling n-inputs, for usage see Test1.py
#     for examples see ListJoin2, LineConnect, ListZip
#     min parameter sets minimum number of sockets
#     setup two variables in Node class
#     create Fixed inputs socket, the multi socket will not change anything
#     below min
#     base_name = 'Data '
#     multi_socket_type = 'StringsSocket'

def multi_socket(node , min=1, start=0, breck=False):
    # probably incorrect state due o init or change of inputs
    # do nothing
    if not len(node.inputs):
        return
    if min < 1:
        min = 1
    if node.inputs[-1].links:
        length = start + len(node.inputs)
        if breck:
            name = node.base_name + '[' + str(length) + ']'
        else:
            name = node.base_name + str(length)
        node.inputs.new(node.multi_socket_type, name, name)
    else:
        while len(node.inputs)>min and not node.inputs[-2].links:
            node.inputs.remove(node.inputs[-1])

####################################
# быстрый сортировщик / quick sorter
####################################

def svQsort(L):
    if L: return svQsort([x for x in L[1:] if x<L[0]]) + L[0:1] + svQsort([x for x in L[1:] if x>=L[0]])
    return []

####################################
# update node on framechange
####################################

def update_nodes(scene):
    try: #bpy.ops.node.sverchok_update_all()
        speedupdate()
    except: pass
# addtionally
pre = bpy.app.handlers.frame_change_pre
for x in pre: pre.remove(x)
pre.append(update_nodes)
