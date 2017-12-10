"""
in verts_in v d=[] n=1
in edges_in s d=[] n=1
in shift s d=1.0 n=2
out verts_out v
out edges_out s
"""
from mathutils import Vector, Matrix
from math import radians, pi, sin
from mathutils.geometry import normal

verts_in = [Vector(v).to_2d() for v in verts_in]

#Searching neighbours for each point
neighbours = [[] for _ in range(len(verts_in))]
for edg in edges_in:
    neighbours[edg[0]].append(edg)
    neighbours[edg[1]].append(edg)

#Convert to from 0 to 2pi angle
def calc_angle(p1,p2):
    angle = p1.angle_signed(p2)
    if angle < 0:
        angle += 2*pi
    return angle

#Sorting neighbours by hour hand
for i, p_neighbs in enumerate(neighbours):
    if len(p_neighbs) != 1:
        angles = [0]
        first_item = list(set(p_neighbs[0]) - set([i]))[0]
        for another_neighb in p_neighbs[1:]:            
            second_item = list(set(another_neighb) - set([i]))[0]
            vector1 = verts_in[first_item] - verts_in[i]
            vector2 = verts_in[second_item] - verts_in[i]
            angles.append(calc_angle(vector1, vector2))
        sorted = list(zip(angles, p_neighbs))
        sorted.sort()
        neighbours[i] = [e[1] for e in sorted]

def get_end_points(item_point):
    second_item = list(set(neighbours[item_point][0]) - set([item_point]))[0]
    vert_edg = verts_in[item_point] - verts_in[second_item]
    mat_r1 = Matrix.Rotation(radians(-45),2,'X')
    mat_r2 = Matrix.Rotation(radians(45),2,'X')
    vert_new1 = (vert_edg * mat_r1).normalized() * shift/sin(radians(45)) + verts_in[item_point]
    vert_new2 = (vert_edg * mat_r2).normalized() * shift/sin(radians(45)) + verts_in[item_point]
    return [vert_new1,vert_new2]

def get_middle_points(item_point):
    points = []
    for i in range(len(neighbours[item_point])):
        current_edges = (neighbours[item_point][i:] + neighbours[item_point][:i])[:2]
        second_item1 = list(set(current_edges[0]) - set([item_point]))[0]
        second_item2 = list(set(current_edges[1]) - set([item_point]))[0]
        vert_edg1 = verts_in[second_item1] - verts_in[item_point]
        vert_edg2 = verts_in[second_item2] - verts_in[item_point]
        angle = calc_angle(vert_edg1, vert_edg2) / 2
        mat_r = Matrix.Rotation(angle, 2, 'X')        
        points.append((vert_edg1 * mat_r).normalized() * shift/sin(angle) + verts_in[item_point])
    return points

#Seting points
findex_new_points = [0]
for i in range(len(verts_in)):
    if len(neighbours[i]) == 1:
        verts_out.extend(get_end_points(i))
        findex_new_points.append(findex_new_points[-1] + 2)
    else:
        p = get_middle_points(i)
        verts_out.extend(p)
        findex_new_points.append(findex_new_points[-1] + len(p))
        
findex_new_points = findex_new_points[:-1]
        
#Creating faces
current_index = len(verts_out) - 1
position_old_points = [0 for _ in range(len(verts_out))]
for edg in edges_in:
    need_points = []
    for i in edg:
        if len(neighbours[i]) <= 2:
            need_points.extend([findex_new_points[i], findex_new_points[i] + 1])
        else:
            position = neighbours[i].index(edg)
            nomber_points = len(neighbours[i])
            variants_positions = list(range(findex_new_points[i], findex_new_points[i] + nomber_points))
            need_points.extend((variants_positions[position - 1:] + variants_positions[:position - 1])[:2])
    
    vec_edg = verts_in[edg[0]] - verts_in[edg[1]]
    vec_1 = verts_out[need_points[0]] - verts_in[edg[0]]
    vec_2 = verts_out[need_points[1]] - verts_in[edg[0]]
    vec_3 = verts_out[need_points[2]] - verts_in[edg[1]]
    vec_4 = verts_out[need_points[3]] - verts_in[edg[1]]
    new_vecs = [vec_1, vec_2, vec_3, vec_4]

    angles = []
    for vec in new_vecs:
        angles.append(vec_edg.angle_signed(vec))

    if angles[0] < 0 and angles[2] < 0 or angles[0] >= 0 and angles[2] >= 0:
        new_edges = [need_points[0],need_points[2],need_points[3],need_points[1]]
    else:
        new_edges = [need_points[0],need_points[3],need_points[2],need_points[1]]
    
    if len(neighbours[edg[0]]) > 2:
        if position_old_points[edg[0]] == 0:
            verts_out.append(verts_in[edg[0]])
            current_index += 1
            position_old_points[edg[0]] = current_index
        new_edges.append(position_old_points[edg[0]])
        
    if len(neighbours[edg[1]]) > 2:
        if position_old_points[edg[1]] == 0:
            verts_out.append(verts_in[edg[1]])
            current_index += 1
            position_old_points[edg[1]] = current_index
        new_edges.insert(2, position_old_points[edg[1]])
    
    if normal(*[verts_out[i].to_3d() for i in new_edges])[2] < 0:
        new_edges = new_edges[::-1]
        
    edges_out.append(new_edges)    
    
verts_out = [[i.to_3d()[:] for i in verts_out]]
