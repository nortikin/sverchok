import bpy, bmesh, mathutils
from mathutils import Vector, Matrix
from node_s import *
global bmesh_mapping, per_cache

bmesh_mapping = {}
per_cache = {}
temp_handle = {}

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

# force a full recalculation next time
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



def vec_pols(pol2,ver2,mw2):
    vector_mediana = []
    for p in pol2:
        vs_idx = p.vertices

        v0 = ver2[vs_idx[0]].co
        v1 = ver2[vs_idx[1]].co
        v2 = ver2[vs_idx[2]].co
        v3 = ver2[vs_idx[3]].co
        
        point1 = (v0+v1)/2
        point2 = (v2+v3)/2
        vm = point2 - point1
        
        vector_mediana.append(vm)
    return vector_mediana

def cont_obj(ob):
    (l,r,f,b,t,d) = (0,0,0,0,0,0)
    for v in ob.data.vertices:
        if v.co[0]<l: l = v.co[0]
        if v.co[0]>r: r = v.co[0]
        if v.co[1]<b: b = v.co[1]
        if v.co[1]>f: f = v.co[1]
        if v.co[2]>t: t = v.co[2]
        if v.co[2]<d: d = v.co[2]
   
    length = abs(r-l)   
    weidth = abs(f-b)
    height = abs(t-d)
    
    return (length, weidth, height)

def cont_pol(pol,ver2):
        vs_idx = pol.vertices

        v0 = ver2[vs_idx[0]].co
        v1 = ver2[vs_idx[1]].co
        v2 = ver2[vs_idx[2]].co
        v3 = ver2[vs_idx[3]].co
        
        point1 = (v0+v1)/2
        point2 = (v2+v3)/2
        point3 = (v0+v3)/2
        point4 = (v1+v2)/2
        vmy = (point2 - point1).length
        vmx = (point3 - point4).length
   
        return (vmx,vmy)

def scale_pols(pols, ver, ob):
    scale = []
    gab_ob = cont_obj(ob)
    for p in pols:
        gab_pol = cont_pol(p, ver)
        sc_length = gab_pol[0]/gab_ob[0]
        sc_weidth = gab_pol[1]/gab_ob[1]
        
        scale.append((sc_length,sc_weidth))
    return scale

def distance(x,y):
    vec = mathutils.Vector((x[0]-y[0], x[1]-y[1], x[2]-y[2]))
    return vec.length

def centres(pol2,ver2,mw2):
    centrs = []
    for p in pol2:
        (i,x,y,z) = (0,0,0,0)
        for v in p.vertices:
            x += ver2[v].co[0]
            y += ver2[v].co[1]
            z += ver2[v].co[2]
            i += 1
        (x,y,z) = (x/i, y/i, z/i)
        centrs.append(mw2 * mathutils.Vector((x, y, z)))
    return centrs

def normals(pol2,mw2):
    nor2 = []
    for p in pol2:
        nor2.append(p.normal)
    return nor2

def distancia(obj1,centrs):
    dist = []
    i = 0
    pt = obj1.matrix_world.translation
    for c in centrs:
        lent = distance(pt,c)
        dist.append((lent))
    return dist

#////////////////////////////////////////////////////////////////////
#/////////////////   main   ////////////////////////////////////////
#//////////////////////////////////////////////////////////////////

def main(cache):
    global per_cache
    tree_update()
    tree_update()
    rd_cache = cache_read(cache)
    if not rd_cache[0]:
        #print('rd_cache[0] is False')
        return False
    
    if not ('spreads' in per_cache[cache]):
        drawit(cache, redraw=False)
    else:
        if bpy.data.objects.find(per_cache[cache]['spreads'][0][0])==-1:
            del per_cache[cache]['spreads']
            drawit(cache, redraw=False)
        else:
            drawit(cache, redraw=True)


def drawit(cache, redraw=False):
    # cache
    global per_cache
    rd_cache = cache_read(cache)
    # True, recipient, donor, centres, formula, diap_min, diap_max
    
    # get objects (достаём объекты)
    recipient_name = rd_cache[1] # имя реципиента
    recipient = bpy.data.objects[recipient_name] #bpy.data.objects[Реципиент]
    donor_name = rd_cache[2] # имя донора
    donor = bpy.data.objects[donor_name] #bpy.data.objects[Донор]
    centres_empty = rd_cache[3].split() # центры полигонов
    formula = rd_cache[5]
    maximum = rd_cache[6]
    minimum = rd_cache[7]
    recipient_mw = recipient.matrix_world
    recipient_mesh = recipient.data
    recipient_mesh.name = recipient_name
    recipient_mesh.update()
    recipient_pol = recipient_mesh.polygons
    recipient_ver = recipient_mesh.vertices
    
    # call needed definitions
    sc_pols = scale_pols(recipient_pol, recipient_ver, donor)
    centrs = centres(recipient_pol,recipient_ver,recipient_mw)
    recipient_nor = normals(recipient_pol,recipient_mw)    
    medians = vec_pols(recipient_pol,recipient_ver,recipient_mw)
    
    # main formula parser
    code_formula = parser.expr("max(min("+formula+",minimum),maximum)").compile()
    dist = []   # future distance list (main feature to scale)
    
    # fullfill distsnce list
    for i, obj1_name in enumerate(centres_empty):
        obj1 = bpy.data.objects[obj1_name]
        loc = obj1.location
        obj1.matrix_world.translation = loc
        tmpdist = distancia(obj1,centrs)
        if i == 0:
            dist = tmpdist
        else:
            dist = list(map(lambda x,y: min(x,y),tmpdist, dist))
    # if spread done and spread objects present in scene
    spreads = []
    for i,c in enumerate(centrs):
        bpy.ops.object.select_all(action='DESELECT')
        #bpy.data.objects[donor_name].select = True
        #bpy.ops.object.duplicate(linked=True) 
        #tempob = bpy.context.selected_objects[0]
        #tempob.name = 'spread'
        #tempob.matrix_world.translation = c
        matrix_world = c
        aa = mathutils.Vector((0,1e-6,1)) 
        bb = mathutils.Vector((recipient_nor[i].x,recipient_nor[i].y,recipient_nor[i].z))
        
        vec = aa
        q_rot = vec.rotation_difference(bb).to_matrix().to_4x4()
    
        vec2 = bb
        q_rot2 = vec2.rotation_difference(aa).to_matrix().to_4x4()
    
        a = mathutils.Vector((1e-6,1,0))* q_rot2
        b = medians[i] 
        vec1 = a
        q_rot1 = vec1.rotation_difference(b).to_matrix().to_4x4() 
    
        M = q_rot1*q_rot
        tempob.matrix_local *= M
        
        x = dist[i]
        mul = eval(code_formula)
        mul = min(mul,sc_pols[i][0],sc_pols[i][1])
        
        #tempob.dimensions = tempob.dimensions * mul
        locmat = tempob.matrix_local * mul
        mydata = [i for i in locmat[0]] + [i for i in locmat[1]] + [i for i in locmat[2]] + [i for i in locmat[3]]
        spreads.append(mydata)
        
    per_cache[cache]['spreads'] = spreads



# for viewer_text node!!!! don't delete

def readFORviewer_sockets_data(data):
    cache = ''
    eva = eval(data)    # why it not work properly all the time?
    for i, object in enumerate(eva):
        cache += str('==' + str(i) + '==' + '\n')
        for m in object:
            cache += str(m) + '\n'
    return cache


# for viewer_draw node and object_out node!!!! don't delete

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