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

from math import pi,fmod
from itertools import chain
import collections

import bpy
from mathutils import Vector

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.utils.sv_mesh_utils import mesh_join

TWO_PI = 2 * pi

#it works with one object only
def separate_loos(verts,edges):
    ve = verts
    pe = edges
    verts_out = []
    edges_out = []

    # build links
    node_links = {}
    for edge_face in pe:
        for i in edge_face:

            if i not in node_links:
                node_links[i] = set()
            node_links[i].update(edge_face)

    nodes = set(node_links.keys())
    n = nodes.pop()
    node_set_list = [set([n])]
    node_stack = collections.deque()
    node_stack_append = node_stack.append
    node_stack_pop = node_stack.pop
    node_set = node_set_list[-1]
    # find separate sets
    while nodes:
        for node in node_links[n]:
            if node not in node_set:
                node_stack_append(node)
        if not node_stack:  # new mesh part
            n = nodes.pop()
            node_set_list.append(set([n]))
            node_set = node_set_list[-1]
        else:
            while node_stack and n in node_set:
                n = node_stack_pop()
            nodes.discard(n)
            node_set.add(n)
    # create new meshes from sets, new_pe is the slow line.
    if len(node_set_list) > 1:
        for node_set in node_set_list:
            mesh_index = sorted(node_set)
            vert_dict = {j: i for i, j in enumerate(mesh_index)}
            new_vert = [ve[i] for i in mesh_index]
            new_pe = [[vert_dict[n] for n in fe]
                      for fe in pe
                      if fe[0] in node_set]
            verts_out.append(new_vert)
            edges_out.append(new_pe)
    elif node_set_list:  # no reprocessing needed
        verts_out.append(ve)
        edges_out.append(pe)
        
    return verts_out, edges_out

def del_loose(verts,edges):
    indx = set(chain.from_iterable(edges))
    verts_out = ([v for i, v in enumerate(verts) if i in indx])
    v_index = dict([(j, i) for i, j in enumerate(sorted(indx))])
    edges_out = ([list(map(lambda n:v_index[n], p)) for p in edges])
    return [verts_out, edges_out]

def calc_angle(p1,p2):
    #Gives angle in pi2 format by hour hand from first point to second
    angle = p1.angle_signed(p2)
    return angle + TWO_PI if angle < 0 else angle

def cycles_list(value,list):
    #Cyle list as item is equal value gets first position
    cut_i = lsit.index(value)
    return list[cut_i:] + list[:cut_i]

def get_next_neighbour(start, neibs, turn='left'):
    #gives first right or left neighbour
    position = neibs.index(start)
    len_neibs = len(neibs)
    if turn == 'left':
        return neibs[int(fmod(position + 1, len_neibs))]
    elif turn == 'right':
        return neibs[int(fmod(position + len_neibs - 1, len_neibs))]

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

def gen_neighbours_from_edges(verts, edges):
    # output for triangle: [[i_neib_A, i_neib_C],
    #                       [i_neib_B, i_neib_C],
    #                       [i_neib_A, i_neib_C]]
    neighbours = [[] for _ in verts]
    for edg in edges:
        neighbours[edg[0]].append(edg[1])
        neighbours[edg[1]].append(edg[0])
    return neighbours

def bypass_outer_edges(pre_finish, start_i1, start_i2, neibs):
    #serching edges for creating polygons, 
    #if last point have only one neighbours or it equal start point - exit
    #pre_finish point need for understanding is loop closed or is not
    previous = start_i1
    next = start_i2
    is_end = False
    poly = [start_i1]
    used_edges = []
    while not(is_end):
        current = next

        #If endpoint
        if len(neibs[next]) == 1:
            next = previous
        else:
            next = get_next_neighbour(previous, neibs[current])
        poly.append(current)

        used_edges.append([previous,current])
        
        is_end = start_i1 == next and current == pre_finish
        
        previous = current
    
    #add last edg
    used_edges.append([current,start_i1])

    return poly, used_edges

def bypass_edges(start_i1, start_i2, neibs):
    #serching edges for creating polygons, 
    #if last point have only one neighbours or it equal start point - exit
    previous = start_i1
    next = start_i2
    is_end = False
    poly = [start_i1]
    while not(is_end):
        current = next
        next = get_next_neighbour(previous, neibs[current])
        poly.append(current)

        is_end = start_i1 == next        
        previous = current

    #create dictionary of used points
    used_verts = {}
    for v in set(poly):
        used_verts[v] = {'times':0, 'pos':[]}
    for i,v in enumerate(poly):
        used_verts[v]['times'] += 1
        used_verts[v]['pos'].append(i)

    #clean polygon
    #this help to know actual postion of points
    less_pos = 0
    for v in poly:
        if used_verts[v]['times'] > 1:
            
            first_pos = used_verts[v]['pos'][0] - less_pos + 1
            last_pos  = used_verts[v]['pos'][-1] - less_pos + 1
            
            loos_part = poly[first_pos:last_pos]
            less_pos += len(loos_part)
            #new poly
            poly = poly[:first_pos] + poly[last_pos:]
            #correct dictionary
            used_verts[v]['times'] = 1
            del used_verts[v]['pos'][1:]
            for loos_v in loos_part:
                used_verts[loos_v]['times'] -= 1
                #del used_verts[loos_v]['pos'][0] #slowly function?
                
    #Create used edges from polygon
    used_edges = [[i1,i2] for i1,i2 in zip(poly, poly[1:] + [poly[0]])]

    return poly, used_edges

def create_mask_used_edges(edges_dict, used_edges):
    for edg in used_edges:
        if tuple(edg) not in edges_dict:
            edg = list(reversed(edg))

        edges_dict[tuple(edg)] += 1

    return edges_dict

def get_outer_poly(verts, edges):

    verts_y = [v.y for v in verts]

    #Create sorted hour hand list of neighbours for each vector
    #Create list of angles between frist neighbour and others
    neighbours = gen_neighbours_from_edges(verts,edges)
    angle_neibs = [[] for _ in verts]
    for i,current_n in enumerate(neighbours):
        neighbours[i],angle_neibs[i] = sort_neib(verts[i], current_n, verts)
    
    #Serching index of top vector in graph
    max_v_index = verts_y.index(max(verts_y))
    #Angle between X direction and first neighbour of top vector
    angle_x = calc_angle(Vector((1,0)),verts[neighbours[max_v_index][0]] - verts[max_v_index])
    # Angle between X direction and all neighbours of top vector, can be more than 2pi degree
    angles_x = [ang + angle_x for ang in angle_neibs[max_v_index]]
    #normolize to 360 degree
    angles_x = [fmod(ang,2 * pi) for ang in angles_x]
    #niearest neigbour of top vector to X direction 
    neib_x = neighbours[max_v_index][angles_x.index(min(angles_x))]
    neib_prex = neighbours[max_v_index][angles_x.index(max(angles_x))]
    outer_poly, used_edges = bypass_outer_edges(neib_prex,max_v_index,neib_x,neighbours)

    used_edges_mask = {}
    for edg in edges:
        used_edges_mask[tuple(edg)] = 0

    used_edges_mask = create_mask_used_edges(used_edges_mask, used_edges)

    return outer_poly , used_edges_mask, neighbours

def get_filled_graph(data_in):
    #Sub_object is also object but divded from start object
    sub_verts = []
    sub_edges = []
    verts_out = []
    polys_out = []
    #Cleaning snd separating mesh
    for v_obj, e_obj in zip(*data_in):

        outer_poly, used_edges_mask, neighbours = get_outer_poly(v_obj, e_obj)

        #Checking bridg edges
        if 2 in used_edges_mask.values():
            #Del bridg edges
            len_edges = len(e_obj)
            for i,edg in enumerate(reversed(e_obj)):
                if used_edges_mask[tuple(edg)] == 2:
                    del e_obj[len_edges - 1 - i]

        #Del loose verts
        v_obj, e_obj = del_loose(v_obj, e_obj)

        #Dived loos parts
        if v_obj:
            v_obj, e_obj = separate_loos(v_obj,e_obj)

        sub_verts.extend(v_obj)
        sub_edges.extend(e_obj)

    #del empty objects
    sub_objects = [[v_obj, e_obj] for v_obj, e_obj in zip(sub_verts,sub_edges) if v_obj]

    for v_obj, e_obj in sub_objects:
    
        #serch outer poly again
        outer_poly, used_edges_mask, neighbours = get_outer_poly(v_obj, e_obj)   
        #filling graph
        steck = [[i1,i2] for i1,i2 in zip(outer_poly,outer_poly[1:] + [outer_poly[0]])]
        polys = []
        while steck:
            poly, used_edges = bypass_edges(steck[-1][1],steck[-1][0],neighbours)
            polys.append(poly)
            used_edges_mask = create_mask_used_edges(used_edges_mask, used_edges)
            del steck[-1]
        
            #Add new edg in steck
            for edg in used_edges:
                real_edg = edg
                if tuple(edg) not in used_edges_mask:
                    edg = list(reversed(edg))
            
                if used_edges_mask[tuple(edg)] < 2:
                    steck.append(real_edg)
            
            #Check useing edges in steck
            len_steck = len(steck)
            for i,edg in enumerate(reversed(steck)):
                real_edg = edg
                if tuple(edg) not in used_edges_mask:
                    edg = list(reversed(edg))
            
                if used_edges_mask[tuple(edg)] >= 2:
                    del steck[len_steck - 1 - i]
    
        verts_out.append([[*v[:],0] for v in v_obj])
        polys_out.append(polys)

    verts_out, _, polys_out = mesh_join(verts_out,[], polys_out)
    
    return verts_out, polys_out

class SvPlanarEdgenetToPolygons(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Planar edgenet to polygons
    Tooltip: Something like fill holes node

    Only X and Y dimensions of input points will be taken for work.
    """
    bl_idname = 'SvPlanarEdgenetToPolygons'
    bl_label = 'Planar edgenet to polygons'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_PLANAR_EDGES_TO_POLY'

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Vers')
        self.inputs.new('SvStringsSocket', "Edgs")
        self.outputs.new('SvVerticesSocket', 'Vers')
        self.outputs.new('SvStringsSocket', "Faces")

    def process(self):

        if not (self.inputs['Vers'].is_linked or self.inputs['Edgs'].is_linked):
            return        
        
        if not any(socket.is_linked for socket in self.outputs):
            return

        verts_in = self.inputs['Vers'].sv_get()
        edges_in = self.inputs['Edgs'].sv_get()
        verts_out = []
        polys_out = []
        
        verts_in = [[Vector(v).to_2d() for v in v_obj] for v_obj in verts_in]
        #This fumction also creat sub_obejects actually
        data_in = [separate_loos(v_obj, e_obj) for v_obj, e_obj in zip(verts_in, edges_in)]

        for sub_data in data_in:
            verts, polys = get_filled_graph(sub_data)
            verts_out.append(verts)
            polys_out.append(polys)

        self.outputs['Vers'].sv_set(verts_out)
        self.outputs['Faces'].sv_set(polys_out)

def register():
    bpy.utils.register_class(SvPlanarEdgenetToPolygons)

def unregister():
    bpy.utils.unregister_class(SvPlanarEdgenetToPolygons)
