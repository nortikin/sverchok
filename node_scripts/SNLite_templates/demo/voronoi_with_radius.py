'''
in verts_in v d=[] n=0
in radius s d=1.0 n=1
in resolution s d=0.1 n=1
out verts_out v
out polys_out s
'''
from math import pi, acos, sin, cos
import numpy as np

from mathutils import Vector, Matrix
from mathutils.geometry import intersect_line_line_2d

from sverchok.utils.voronoi import Site, computeDelaunayTriangulation
from sverchok.utils.sv_mesh_utils import polygons_to_edges
from sverchok.data_structure import match_long_repeat

TWO_PI = 2 * pi

def get_delaunay_triangulation(verts_in):
    pt_list = [Site(pt[0], pt[1]) for pt in verts_in]
    res = computeDelaunayTriangulation(pt_list)
    polys_in = [tri for tri in res if -1 not in tri]
    #all faces hase normals -Z, should be reversed
    polys_in = [pol[::-1] for pol in polys_in]
    edges_in = polygons_to_edges([polys_in], unique_edges=True)[0]
    return edges_in, polys_in

def calc_angle(p1,p2,mode='clockwise'):
    #Gives angle in pi2 format from first point to second
    angle = p1.angle_signed(p2)
    angle = angle + TWO_PI if angle < 0 else angle
    if mode != 'clockwise':
        angle = TWO_PI - angle
    return angle

def get_intersection_point(v_a1, v_a2, v_b1, v_b2):
    #return vector or None
    return intersect_line_line_2d(v_a1, v_a2, v_b1, v_b2)

def gen_neighbours_from_edges(verts, edges):
    # output for triangle: [[i_neib_A, i_neib_C],
    #                       [i_neib_B, i_neib_C],
    #                       [i_neib_A, i_neib_C]]
    neighbours = [[] for _ in verts]
    for edg in edges:
        neighbours[edg[0]].append(edg[1])
        neighbours[edg[1]].append(edg[0])
    return neighbours

def sort_neib(current_v, neibs, all_v):
    #Sorting neighbours by hour hand, 
    #all_v is all verts in graph,
    # neighbours is position of neghbours vectors
    angles = [0]
    if len(neibs) > 1:
        first_item = neibs[0]
        vector1 = all_v[first_item]  - current_v
        for second_item in neibs[1:]:            
            vector2 = all_v[second_item] - current_v
            angles.append(calc_angle(vector1, vector2))
            
        sorted_by_angle = list(zip(angles, neibs))
        sorted_by_angle.sort()
        return [neib for ang, neib in sorted_by_angle],[ang for ang, neib in sorted_by_angle]
    return neibs, angles

def get_point_by_angle(vector1, vector2, angle, len_new_v, mode='left and right'):
    #return cords of points in triangle with nown two sides and one angle
    #vector1 is base point, vector2 means only direction
    #angle is measured in vector1 node
    #len_new_v is distanse between vector1 and retrun point
    mat_left  = Matrix.Rotation(angle,2,'X') #hope it left turn
    mat_right = Matrix.Rotation(angle * -1,2,'X')
    v = vector1 - vector2
    new_v_left  = (v @ mat_left ).normalized() * len_new_v + vector2
    new_v_right = (v @ mat_right).normalized() * len_new_v + vector2
    mode_words = mode.split(' ')
    if 'left' in mode_words and 'right' in mode_words:
        if mode_words.index('left') < mode_words.index('right'):
            return new_v_left, new_v_right
        else:
            return new_v_right, new_v_left
    elif 'left' in mode_words:
        return new_v_left
    else:
        return new_v_right
    
def get_distance(vector1, vector2):
    #retrun distance between two points
    return (vector1 - vector2).length

def get_chord(height,radius,center_v,direction_chord_v):
    #return cords of chord with nown radius and height of chord
    #center is vector of center of circle, direction is direction of normal to chord
    # chord dosen't exist for given parameters so return 0
    if height >= radius:
        return 0
    else:
        #Angle of visibility of half chord
        angle = acos(height / radius)
        points = get_point_by_angle(center_v, direction_chord_v,angle,radius)
        return points, angle
    
def is_chord_intersect(angle_ch1, angle_ch2, angle_both):
    #retrun True or False
    #angle_ch1 and ch2 is half angle of visibility chord
    #angle_both is angle between normals of chords
    return True if angle_ch1 + angle_ch2 > angle_both else False

def get_len_arc(radius,angle):
    #angle between extreme points in radians
    return radius * angle

def get_arc(start_v, end_v, center_v, resolution, mode='clockwise'):
    #return points of arc by two points and center of circle
    #resolution determines distanse between points of arc
    start_v, end_v = start_v - center_v, end_v - center_v
    start_angle = calc_angle(Vector((0,1)), start_v)
    #angle between start and end vectors
    angle = calc_angle(start_v, end_v)
    radius = get_distance(start_v, Vector((0,0)))
    len_arc = get_len_arc(radius, angle)
    count = len_arc / resolution #this place can be calculate once for current radius!!!
    count = count if count > 3 else 3
    end_angle = start_angle + angle if mode == 'clockwise' else start_angle + angle - TWO_PI
    steps_angle = list(np.linspace(start_angle,end_angle,count))
    vectors = [Vector((sin(ang),cos(ang))) * radius + center_v for ang in steps_angle]
    return vectors

def get_circle(center_v, radius, resolution):
    #return points of circle
    count = TWO_PI * radius / resolution
    count = count if count >= 5 else 5
    steps_angle = list(np.linspace(0, TWO_PI, count))[:-1]
    vectors = [Vector((sin(ang),cos(ang))) * radius + center_v for ang in steps_angle]
    return vectors
    
def get_structure_vert():
    dictionary = {'neibs':[],
                  'ang_neibs':[], #sorted
                  'sorted_neibs':[],
                  'height_chords':[], #nested, sorted, PDC
                  'chords':[], #nested, sorted, PDC
                  'vis_angles':[], #sorted, PDC
                  'intersect_chords':[],
                  'is_intersect':[]} #if point was born intersection two chords - True
    return dictionary
                  
def get_structure_edg(edg):
    dictionary = {tuple(edg):{'height_chord':[], #PDC
                              'chord':[], #PDC
                              'vis_angle':[], #PDC
                              'intersect_chord':None, #PDC
                              'is_intersect':None, #[T,T] or [T,F] or [F,T] or [F,F]
                              'hiden_chord':None,
                              'used_edg':[None,None]}}
    return dictionary

def get_structure_pol(pol):
    dictionary = {tuple(sorted(pol)):{'polygon':pol,
                                      'intersect_point':None,
                                      'used_point':None}}
    return dictionary

def check_key(key, dict):
    return key if tuple(key) in dict else key[::-1]

def cycle_item(i,len_i):
    #return correct item of list
    return i % len_i

def get_voronoi_with_radius(verts_in,radius,resolution):
    verts_out, polys_out = [],[]
    edges_in, polys_in = get_delaunay_triangulation(verts_in)
    verts_in = [Vector(v).to_2d() for v in verts_in]
    neighbours = gen_neighbours_from_edges(verts_in, edges_in)
    verts_data = [get_structure_vert() for _ in verts_in]
    edges_data = {}
    [edges_data.update(get_structure_edg(edg)) for edg in edges_in]
    #structure verts_data - [{'a':[],...},{'b':[],...}...]
    #structure edges_data - {'edg':{'a':[],'b':[]},..., 'edg':{'a':[],...},...}
    [dict['neibs'].extend(neibs) for dict,neibs in zip(verts_data, neighbours)]

    #sorting up neibs and calculation height of chords
    for i,dict in enumerate(verts_data):
        neibs, angles = sort_neib(verts_in[i],dict['neibs'],verts_in)
        dict['ang_neibs'].extend(angles)
        dict['sorted_neibs'].extend(neibs)
        for neib in dict['sorted_neibs']:
            edg = check_key([i,neib],edges_data)
        
            #Protection of Double Calculation
            if not(edges_data[tuple(edg)]['height_chord']):
                height_chord = get_distance(verts_in[i],verts_in[neib]) / 2
                edges_data[tuple(edg)]['height_chord'].append(height_chord)
            else:
                height_chord = edges_data[tuple(edg)]['height_chord'][0]
            
            dict['height_chords'].append(height_chord)

    #calculation chords
    for i,dict in enumerate(verts_data):
        for h_chord,neib in zip(dict['height_chords'],dict['sorted_neibs']):
        
            edg = check_key([i,neib],edges_data)
            #Protection of Double Calculation
            if not(edges_data[tuple(edg)]['chord']):
                if h_chord > radius:
                    v_chord, vis_angle = None, None
                    edges_data[tuple(edg)]['chord'] = v_chord
                    edges_data[tuple(edg)]['vis_angle'] = vis_angle
                else:
                    v_chord, vis_angle = get_chord(h_chord,radius,verts_in[i],verts_in[neib])
                    edges_data[tuple(edg)]['chord'].extend(v_chord)
                    edges_data[tuple(edg)]['vis_angle'].append(vis_angle)
            else:
                v_chord = edges_data[tuple(edg)]['chord'][::-1]
                vis_angle = edges_data[tuple(edg)]['vis_angle'][0]
                
            dict['chords'].append(v_chord)
            dict['vis_angles'].append(vis_angle)

    #get intersection points
    polys_data = {}
    [polys_data.update(get_structure_pol(pol)) for pol in polys_in]
    for key in polys_data.keys():
        neib1, current, neib2 = polys_data[key]['polygon']
        dict = verts_data[current]
        angles = dict['ang_neibs'] + [TWO_PI]
        i = dict['sorted_neibs'].index(neib1) #not good i think
        len_neibs = len(dict['neibs'])
        i_next = cycle_item(i + 1,len_neibs)
    
        if dict['chords'][i] and dict['chords'][i_next]:
            ang_cur = angles[i+1] - angles[i]
            vis_cur = dict['vis_angles'][i]
            vis_next = dict['vis_angles'][i_next]
            cho_cur = dict['chords'][i]
            cho_next = dict['chords'][i_next]
    
            if ang_cur < vis_cur + vis_next:
                intersect_v = get_intersection_point(cho_cur[0], cho_cur[1], cho_next[0], cho_next[1])
            else:
                intersect_v = False
    
            polys_data[key]['intersect_point'] = intersect_v

    #get new chords
    for edg in edges_in:
        dict = edges_data[tuple(edg)]
        if dict['chord']:
            v_cur = edg[0]
            n_cur = edg[1]
            i = verts_data[v_cur]['sorted_neibs'].index(n_cur)
            angles = verts_data[v_cur]['ang_neibs'] + [TWO_PI]
    
            if len(verts_data[v_cur]['neibs']) == 2:
                angle = angles[i+1] - angles[i]
                #if angle > 180(pi) Left else Right
                i_next = 1 if i == 0 else 0
                polygon = sorted([*edg,verts_data[v_cur]['sorted_neibs'][i_next]])
                intersect = polys_data[tuple(polygon)]['intersect_point']
                chord = verts_data[v_cur]['chords'][i]
                i_place = intersect if intersect else chord[0] if angle > pi else chord[1]
                dict['intersect_chord'] = ([i_place,chord[1]] if angle > pi else [chord[0],i_place])
            
                if intersect and angle > pi:
                    dict['is_intersect'] = [True,False]
                elif intersect and angle < pi:
                    dict['is_intersect'] = [False,True]
                else:
                    dict['is_intersect'] = [False,False]
            
            else:
                len_neibs = len(verts_data[v_cur]['sorted_neibs'])
                i_prev = cycle_item(i-1,len_neibs)
                i_next = cycle_item(i+1,len_neibs)
                p_prev = sorted([*edg,verts_data[v_cur]['sorted_neibs'][i_prev]])
                p_next = sorted([*edg,verts_data[v_cur]['sorted_neibs'][i_next]])
                sec_prev = polys_data.get(tuple(p_prev),{'intersect_point':None})['intersect_point']
                sec_next = polys_data.get(tuple(p_next),{'intersect_point':None})['intersect_point']
                chord = verts_data[v_cur]['chords'][i]
            
                if sec_prev and sec_next:
                    dict['intersect_chord'] = [sec_prev, sec_next]
                elif sec_prev:
                    dict['intersect_chord'] = [sec_prev,chord[1]]
                elif sec_next:
                    dict['intersect_chord'] = [chord[0],sec_next]
                else:
                    dict['intersect_chord'] = chord
                
                dict['is_intersect'] = [bool(sec_prev),bool(sec_next)]

    #add new chords to verts_data
    for i,dict in enumerate(verts_data):
        for neib in dict['sorted_neibs']:
            edg = check_key([i,neib],edges_data)
            sec_chord = edges_data[tuple(edg)]['intersect_chord']
            is_sec_chord = edges_data[tuple(edg)]['is_intersect']
            if sec_chord:
                oder = edg[0] == i
                dict['intersect_chords'].append(sec_chord if oder else sec_chord[::-1])
                dict['is_intersect'].append(is_sec_chord if oder else is_sec_chord[::-1])
            else:
                dict['intersect_chords'].append(None)
                dict['is_intersect'].append([None,None])
 
    #generation new geometry
    count_v = 0
    for i,dict in enumerate(verts_data):
        poly = []
        is_chords = [cho for cho in dict['intersect_chords'] if cho]
        if not(is_chords):
            circle = get_circle(verts_in[i], radius, resolution)
            len_circle = len(circle)
            poly.extend(list(range(count_v,count_v + len_circle))[::-1])
            verts_out.extend(circle)
            count_v += len_circle
            polys_out.append(poly)
            continue
    
        len_neibs = len(dict['neibs'])
        #We chould start from chord wich have the list hight chord
        min_hight = min(dict['height_chords'])
        i_min_chord = dict['height_chords'].index(min_hight)
        iterator = list(range(len_neibs))[i_min_chord:] + list(range(len_neibs))[:i_min_chord]
    
        if is_chords:
            for i_iter,i_cur in enumerate(iterator):
                chord_cur = dict['intersect_chords'][i_cur]
                edg_cur = check_key([i,dict['sorted_neibs'][i_cur]],edges_data)
            
                if not(chord_cur) or edges_data[tuple(edg_cur)]['hiden_chord']:
                    continue
            
                vis_angle_cur = dict['vis_angles'][i_cur]
                angle_cur = dict['ang_neibs'][i_cur]
            
                #Chowsing next chord
                for i_next in (iterator[cycle_item(i_iter + 1, len_neibs):] + 
                               iterator[:cycle_item(i_iter + 1, len_neibs)]):
                    chord_next = dict['intersect_chords'][i_next]
                    i_next2 = cycle_item(i_next+1, len_neibs)
                
                    if not(chord_next):
                        continue
                    
                    if chord_cur == chord_next:
                        break
                
                    edg_next = check_key([i,dict['sorted_neibs'][i_next]],edges_data)
                    if edges_data[tuple(edg_next)]['hiden_chord']:
                        continue
                    
                    #Chercking is next chord in shadow of the previous
                    if (dict['height_chords'][i_next] > dict['height_chords'][i_cur] or
                        dict['height_chords'][i_next] > dict['height_chords'][i_next2]):
                
                        vis_angle_next = dict['vis_angles'][i_next]
                        angle_next = dict['ang_neibs'][i_next]
                        angle = (angle_next - angle_cur if i_cur < i_next 
                                                        else TWO_PI - abs(angle_next - angle_cur))
                                
                        if (angle + vis_angle_cur - vis_angle_next > TWO_PI or
                            2 * vis_angle_cur > vis_angle_cur + angle + vis_angle_next):
                            edges_data[tuple(edg_next)]['hiden_chord'] = True
                            continue
                
                    #Cherching is next chord in shadow of the tvice next chord
                    if dict['height_chords'][i_next] > dict['height_chords'][i_next2]:
                
                        edg_next2 = check_key([i,dict['sorted_neibs'][i_next2]],edges_data)
                        vis_angle_next2 = dict['vis_angles'][i_next2]
                        angle_next2 = dict['ang_neibs'][i_next2]
                        angle2 = (angle_next2 - angle_next if i_next < i_next2
                                                        else TWO_PI - abs(angle_next2 - angle_next))
      
                        if (vis_angle_next2 - angle2 > vis_angle_next or
                            angle2 + vis_angle_next2 - vis_angle_next > TWO_PI):
                            edges_data[tuple(edg_next)]['hiden_chord'] = True
                            continue
                    
                    break
            
                if dict['is_intersect'][i_next][0]:
                    polygon = sorted([*edg_cur,dict['sorted_neibs'][i_next]])
                    if polys_data[tuple(polygon)]['used_point'] != None:
                        poly.append(polys_data[tuple(polygon)]['used_point'])
                    else:
                        poly.append(count_v)
                        verts_out.append(chord_cur[1])
                        polys_data[tuple(polygon)]['used_point'] = count_v
                        count_v += 1
                
                else:
                    oder_cur = True if i == edg_cur[0] else False
                    used_edg_cur = (edges_data[tuple(edg_cur)]['used_edg'] if oder_cur else
                                    edges_data[tuple(edg_cur)]['used_edg'][::-1])
                    if used_edg_cur[1] != None:
                        poly.append(used_edg_cur[1])
                    else:
                        poly.append(count_v)
                        verts_out.append(chord_cur[1])
                        item = 1 if oder_cur else 0
                        edges_data[tuple(edg_cur)]['used_edg'][item] = count_v
                        count_v += 1
                    
                    arc = get_arc(chord_cur[1],chord_next[0],verts_in[i],resolution)[1:-1]
                    len_arc = len(arc)
                    poly.extend(list(range(count_v,count_v + len_arc)))
                    verts_out.extend(arc)
                    count_v += len_arc
                
                    edg_next = check_key([i,dict['sorted_neibs'][i_next]],edges_data)
                    oder_next = True if i == edg_next[0] else False
                    used_edg_next = (edges_data[tuple(edg_next)]['used_edg'] if oder_next else
                                     edges_data[tuple(edg_next)]['used_edg'][::-1])
                    if used_edg_next[0] != None:
                        poly.append(used_edg_next[0])
                    else:
                        poly.append(count_v)
                        verts_out.append(chord_next[0])
                        item = 0 if oder_next else 1
                        edges_data[tuple(edg_next)]['used_edg'][item] = count_v
                        count_v += 1
                    
                if chord_cur == chord_next:
                    break
        
            polys_out.append(poly[::-1])

    verts_out = [v.to_3d()[:] for v in verts_out]
    return verts_out, polys_out

#Process
if type(radius) != list:
    radius = [radius]
    
if type(resolution) != list:
    resolution = [resolution]

data = verts_in, radius, resolution
data = match_long_repeat(data)

for v_obj,rad,res in zip(*data):
    #protection zero deviding
    res = res if res > 0.02 else 0.02

    verts, polys = get_voronoi_with_radius(v_obj,rad,res)
    verts_out.append(verts)
    polys_out.append(polys)
