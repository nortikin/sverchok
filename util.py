import bpy, bmesh, mathutils
from mathutils import Vector, Matrix
from node_s import *
global bmesh_mapping, per_cache
from functools import reduce
from math import radians
import itertools
import collections

bmesh_mapping = {}
per_cache = {}
temp_handle = {}
cache_nodes = {}
list_nodes4update = {}
sv_Vars = {}

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

def levelsOflist(list):
    level = 1
    for n in list:
        if type(n) in [type([]), type(tuple())] and len(n) > 0: # why it not understands [list, tuple]??? strange behaviour
            level += levelsOflist(n)
        return level


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

def Vector_generate(prop):
    vec_out = []
    for i, object in enumerate(prop):  # lists by objects
        veclist = []
        for v in object: # verts
            veclist.append(Vector(v[:]))
        vec_out.append(veclist)
    return vec_out

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
            
        if scale[0]:
            k = min(len(scale[0])-1,i)
            scale2=scale[0][k]
            for j in range(4):
                kk=min(j,2)
                ma[j][j] = ma[j][j] * scale2[kk]
            
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



################### update List join magic ##########

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
############### update sockets magic ################
#####################################################


def updateAllOuts(self, update_self=True):
    if update_self:
        self.update()
    #print('update_node ', self.name) 
    for output in self.outputs:
        if output.is_linked:
            for link in output.links:
                nod = link.to_socket.node
                if check_update_node(nod.name, True):
                    updateAllOuts(nod)
                    
    

def updateSlot(self, context):
    return
    
def updateNode(self, context):
    speedUpdate(self.name,self.id_data.name)
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
                if input.is_linked:
                    Flag=True
                    break  
            if flag: 
                continue
            
            nodeset_a = []
            nodeset_e, prioritet = insertnode(nod, nodeset_a, nodeset_e, priority=prioritet)
            
        list_nodes4update[ng.name] = prioritet + nodeset_e
        print("MaketreeUpdate()",list_nodes4update[ng.name])
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
    roots = []
    wifi_out = []
    wifi_in = []
    ng = bpy.data.node_groups[node_tree]
    node_list = []
    if not node_set: # if no node_set, take all
        node_set = set(ng.nodes.keys())
    for name,node in [(node_name,ng.nodes[node_name]) for node_name in node_set]:
        node_dep = []
        for socket in node.inputs:
            if socket.is_linked and socket.links[0].from_socket.node.name in node_set:
                node_dep.append(socket.links[0].from_socket.node.name)
        is_root = True            
        for socket in node.outputs:
            if socket.is_linked:
                is_root = False
                break
        # ignore nodes without input or outputs, like frames        
        if node_dep or len(node.inputs) or len(node.outputs):
            deps[name]=node_dep
        if is_root and node_dep and not name[:6] == 'Wifi i':
            roots.append(name)
        if name[:6] == 'Wifi o':
            wifi_out.append(name)
        if name[:6] == 'Wifi i':
            wifi_in.append(name)  
            
    # create wifi out dependencies            
    for wifi_out_node in wifi_out:
        wifi_dep = []
        for wifi_in_node in wifi_in:
            if ng.nodes[wifi_out_node].var_name == ng.nodes[wifi_in_node].var_name:
                wifi_dep.append(wifi_in_node)
        if wifi_dep:
            deps[wifi_out_node]=wifi_dep        
    
    if roots:
        name = roots.pop()
    else: #should never happen for a proper node tree
        if len(deps):
            tmp = list(deps.keys())
            name = tmp[0]
        else: # no nodes
            return
    # index stack for traversing node graph   
    tree_stack = []          
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
        # if all dependencies are in out        
        if node_dependencies:
            if not name in out:
                out[name]=1
                del deps[name]
            if tree_stack:
                name = tree_stack.pop()
            elif roots:
                name = roots.pop()
            else: 
                if len(deps)==len(out):
                    break
                for node_name in deps.keys():
                    name=node_name
                    break
    return list(out.keys())
    
def makeTreeUpdate2():
    """ makes a complete update list for the current node tree"""
    global list_nodes4update
        
    for ng in bpy.data.node_groups[:]:                
        list_nodes4update[ng.name]=make_update_list(ng.name)
    list_nodes4update['TreeName'] = bpy.context.space_data.node_tree.name   



                
def make_tree_from_node(node_name,tree_name):
    """ 
    Create a partial update list from a sub-tree, node_name is node that has changed
    Only nodes downtree from node_name
    """
    ng = bpy.data.node_groups[tree_name]
    out_set = {node_name}
    out_stack = []
    wifi_out = []
    current_node = node_name
    while current_node:
        if current_node[:6] == 'Wifi i':
            if not wifi_out:  # build only if needed
                for name,node in ng.nodes.items():
                    if name[:6] == 'Wifi o':
                        wifi_out.append(name)
            for wifi_out_node in wifi_out:
                if ng.nodes[current_node].var_name == ng.nodes[current_node].var_name:
                    if not wifi_out_node in out_set:
                        out_stack.append(wifi_out_node)
                        out_set.add(wifi_out_node)
        for socket in ng.nodes[current_node].outputs:
            if socket.is_linked:
                for link in socket.links:
                    if not link.to_socket.node.name in out_set:
                        out_set.add(link.to_socket.node.name)
                        out_stack.append(link.to_socket.node.name)
        if out_stack:
            current_node = out_stack.pop()
        else:
            current_node = ''

    return make_update_list(tree_name,out_set)
       
        
# for timing different nodes
#import time
#import operator

# only update from start_node with selected tree or update everything if nothing is set.
def speedUpdate(start_node = None, node_tree_name = None):
    global list_nodes4update

    if not 'TreeName' in list_nodes4update: 
        makeTreeUpdate2() 
        start_node = None
    if 'TreeName' in list_nodes4update:
        NodeTree_name = list_nodes4update['TreeName']
    else:
        NodeTree_name = bpy.context.space_data.node_tree.name
        list_nodes4update['TreeName'] = NodeTree_name
   
    if start_node != None:
        out = make_tree_from_node(start_node,node_tree_name)
        nods = bpy.data.node_groups[node_tree_name].nodes
#        start = time.time()        

        for nod_name in out:
            if nod_name in nods:
                nods[nod_name].update()
#                print("updated-sub:",nod_name)
#        stop = time.time()

#        print("limited update",round(stop-start,4))
    
        return
                    
    for ng_name in list_nodes4update:
        if ng_name in bpy.context.blend_data.node_groups and ng_name==NodeTree_name:
            nods = bpy.data.node_groups[ng_name].nodes
#            start = time.time()  
            for nod_name in list_nodes4update[ng_name]:
                if nod_name in nods:
                    nods[nod_name].update()
#                    print("updated:",nod_name)
#            stop = time.time()
#            print("full update",round(stop-start,4))    

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
    if not socket.node.socket_value_update:
        socket.node.update()
    if type(socket.links[0].from_socket) == bpy.types.StringsSocket:
        typeresult = eval(socket.links[0].from_socket.StringsProperty)
    elif type(socket.links[0].from_socket) == bpy.types.VerticesSocket:
        typeresult = eval(socket.links[0].from_socket.VerticesProperty)
    elif type(socket.links[0].from_socket) == bpy.types.MatrixSocket:
        typeresult = eval(socket.links[0].from_socket.MatrixProperty)
    return typeresult


def SvSetSocketAnyType(self, socket, out):
    if not self.outputs[socket].node.socket_value_update:
        self.outputs[socket].node.update()
    if type(self.outputs[socket]) == bpy.types.StringsSocket:
        self.outputs[socket].StringsProperty = str(out) 
    elif type(self.outputs[socket]) == bpy.types.VerticesSocket:
        self.outputs[socket].VerticesProperty = str(out) 
    elif type(self.outputs[socket]) == bpy.types.MatrixSocket:
        self.outputs[socket].MatrixProperty = str(out) 


def get_socket_type(node, inputsocketname):
    if type(node.inputs[inputsocketname].links[0].from_socket) == bpy.types.VerticesSocket:
        return 'v'
    if type(node.inputs[inputsocketname].links[0].from_socket) == bpy.types.StringsSocket:
        return 's'
    if type(node.inputs[inputsocketname].links[0].from_socket) == bpy.types.MatrixSocket:
        return 'm'

#     utility function for handling n-inputs, for usage see Test1.py
#     for examples see ListJoin2, LineConnect, ListZip  
#     min parameter sets minimum number of sockets  
#     setup two variables in Node class 
#     create Fixed inputs socket, the multi socket will not change anything
#     below min  
#     base_name = 'Data '
#     multi_socket_type = 'StringsSocket'

def multi_socket(node , min=1):
    # probably incorrect state due o init or change of inputs
    # do nothing
    if not len(node.inputs):
        return
    if min < 1:
        min = 1
    if node.inputs[-1].is_linked:
        name = node.base_name+str(len(node.inputs))
        node.inputs.new(node.multi_socket_type, name, name)
    else:
        while len(node.inputs)>min and not node.inputs[-2].is_linked:
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
        speedUpdate()
    except: pass
# addtionally 
pre = bpy.app.handlers.frame_change_pre
for x in pre: pre.remove(x)
pre.append(update_nodes)
