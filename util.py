import bpy, bmesh, mathutils
from mathutils import Vector, Matrix
from node_s import *
global bmesh_mapping, per_cache
from functools import reduce
from math import radians

bmesh_mapping = {}
per_cache = {}
temp_handle = {}
cache_nodes={}

#####################################################
################### update magic ####################
#####################################################

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
################# list levels magic #################
########### working with nesting levels #############
################ define data floor ##################
#####################################################

# data from nasting to standart: TO container( objects( lists( floats, ), ), )
def dataCorrect(data):
    dept = levelsOflist(data)
    output = []
    if dept < 2:
        #print ('DC, dep<3', dept)
        #print ('correct', data)
        return [dept, data]
    else:
        #print ('DC, dep>2', dept)
        output = dataStandart(data, dept)
        #print ('correct', output)
        return output
    
# from standart data to initial levels: to nasting lists  container( objects( lists( nasty_lists( floats, ), ), ), ) это невозможно!
def dataSpoil(data, dept):
    pass
    
# data from nasting to standart: TO container( objects( lists( floats, ), ), )
def dataStandart(data, dept):
    deptl = dept - 1
    #and type(data) in [list, tuple]:
    output = []
    for object in data:
        if deptl > 1:
            #print ('DS, dep>1', deptl)
            output.extend(dataStandart(object, deptl))
            #elif deptl > 2 and type(object) in [int, float]:
            #output_ += object
        else:
            output.append(data)
            #print ('DS, dep<2', deptl)
            #print (output)
            return output
    return output



# calc list nesting only in countainment level integer

def levelsOflist(list):
    level = 1
    for n in list:
        if type(n) in [type([]), type(tuple())]: # why it not understands [list, tuple]??? strange behaviour
            level += levelsOflist(n)
            #print (level)
        return level


#####################################################
################### matrix magic ####################
##### tools that makes easier to convert data #######
####### from string to matrixes, vertices, ##########
######### lists, other and vise versa ###############
#####################################################



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



def Matrix_location(prop):
    Vectors = []
    for p in prop:
        Vectors.append(p.translation)
    return [Vectors]



def Vector_generate(prop):
    vec_out = []
    for i, object in enumerate(prop):  # lists by objects
        veclist = []
        for v in object: # verts
            veclist.append(Vector(v[:]))
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
    if not ini_update_cnode(self.name):
        return
    
    updateAllOuts(self)
    is_updated_cnode()
    
    