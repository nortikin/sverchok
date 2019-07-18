# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bmesh
from mathutils import Vector
from mathutils.geometry import (
    intersect_line_line_2d)
from sverchok.data_structure import (
    match_long_repeat,
    match_long_cycle)
from sverchok.utils.modules.geom_utils import (
    pt_in_triangle,
    length_v2,
    sub_v3_v3v3,
    length_sq,
    interp_v3_v3v3)
from sverchok.utils.sv_mesh_utils import mesh_join
from sverchok.nodes.modifier_change.polygons_to_edges import pols_edges
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata, pydata_from_bmesh

def edges_from_ed_inter(ed_inter):
    '''create edges from intersections library'''
    edges_out = []
    intersection_lib = []
    intesection_indices = []
    first_edge = []
    for e in ed_inter:
        # sort by first element of tuple (distances)
        if len(e) > 2:
            e_s = sorted(e)
            #remove intersections that are too close
            e_s = [e for i, e in enumerate(e_s) if e[1] != e_s[i-1][1]]
            #indexes of the first set that are part of intersection set too
            # excep = [e[1] for i, e in enumerate(e_s) if i>0 and i < len(e_s)-1 and e[1]<v_or-1]
            intesections_in_edge = [e[1] for i, e in enumerate(e_s) if i > 0 and i < len(e_s)-1]
            intesection_indices += intesections_in_edge
            if len(e_s) > 0:
                fe = sorted((e_s[0][1], e_s[-1][1]))
                intersection_lib.append(list(e_s))
                for i in range(1, len(e_s)):
                    et = sorted((e_s[i-1][1], e_s[i][1]))
                    if  et not in edges_out:
                        edges_out.append(et)
                        first_edge.append(fe)
        else:
            e_s = e
            fe = sorted((e_s[0][1], e_s[-1][1]))
            intersection_lib.append(list(e_s))
            edges_out.append(fe)
            first_edge.append(fe)

    return edges_out, intersection_lib, intesection_indices, first_edge


def intersect_edges_2d(verts, edges, epsilon, len_edges_in):
    '''Iterate through edges  and expose them to intersect_line_line_2d'''
    verts_or = [Vector(v) for v in verts]
    ed_lengths = [(verts_or[e[1]] - verts_or[e[0]]).length for e in edges]
    # ed_lengths = edges_lengths(verts_or, edges)
    verts_out = verts
    ed_inter = [[] for e in edges]
    ed_index = range(len(edges))
    for e, d, i in zip(edges, ed_lengths, ed_index):
        # if there is no intersections this will create a normal edge
        ed_inter[i].append([0.0, e[0]])
        ed_inter[i].append([d, e[1]])
        v1 = verts_or[e[0]]
        v2 = verts_or[e[1]]
        cut_edge = i > len_edges_in-1
        if cut_edge:
            continue
        # if d == 0:
            # continue

        for j, e2 in enumerate(edges[i+1:], i+1):
            # if i <= j:
                # continue
            if cut_edge == (j > len_edges_in-1):
                continue

            if (e2[0] in e) or (e2[1] in e):
                continue

            d2 = ed_lengths[j]
            if d2 == 0:
                continue
            # if first_check(cut_edge, i, j, len_edges_in, d2, e, e2):
                # continue
            v3 = verts_or[e2[0]]
            v4 = verts_or[e2[1]]
            vx = intersect_line_line_2d(v1, v2, v3, v4)
            if vx:
                d_to_1 = (vx - v1.to_2d()).length
                d_to_2 = (vx - v3.to_2d()).length

                new_id = len(verts_out)
                if (vx.x, vx.y, v1.z) in verts_out:
                    new_id = verts_out.index((vx.x, vx.y, v1.z))
                else:
                    if d_to_1 < epsilon:
                        new_id = e[0]
                    elif d_to_1 > d - epsilon:
                        new_id = e[1]
                    elif d_to_2 < epsilon:
                        new_id = e2[0]
                    elif d_to_2 > d2 - epsilon:
                        new_id = e2[1]
                    if new_id == len(verts_out):
                        verts_out.append((vx.x, vx.y, v1.z))
                    else:
                        print("SA",new_id, i, j)
                # first item stores distance to origin, second the vertex id
                ed_inter[i].append([d_to_1, new_id])
                ed_inter[j].append([d_to_2, new_id])


    # edges_out, intersection_lib, excep = edges_from_ed_inter(ed_inter, len(verts_or))

    return verts_out, ed_inter


def cross_indices2(n, m):
    '''create crossed indices '''
    index = []
    for i in range(n):
        for j in range(0, m):
            index.append([i, j])

    return index


def list_matcher(a, list_match):
    '''list match behavior'''
    if list_match == "Long Cycle":
        return match_long_cycle(a)
    else:
        return match_long_repeat(a)


def create_new_indexes(verts_out, mask):
    '''compare vector with mask and create new index table'''
    new_index = []
    off = 0
    for i in range(len(verts_out)):
        if mask[i]:
            new_index.append(i - off)
        else:
            off += 1
            new_index.append(-1)
    return new_index


def flat_set(edge_pol):
    '''get all the mentioned indices in one list, with no index repetition'''
    flat_list = [index for pol in edge_pol for index in pol]
    return list(set(flat_list))


def pols_edges_especial(obj, unique_edges=False):
    '''gets the edges from polygons and also informs about the edges that are shared by many polygons'''
    out_edges = []
    seen = set()
    repeated = set()
    for face in obj:
        for edge in zip(face, list(face[1:]) + list([face[0]])):
            sorted_edge = sorted(edge)
            if unique_edges and tuple(sorted_edge) in seen:
                repeated.add(tuple(sorted_edge))
                continue
            if unique_edges:
                seen.add(tuple(sorted_edge))
            out_edges.append(sorted_edge)

    return out_edges, list(repeated)


def exclude_interior_edges(edges, interior):
    '''remove interior edges'''
    for e in interior:
        edges.remove(list(e))


def verts_inside_pols_basic(verts_or, verts_cut, pols_cut):
    '''
    use the pt_in_triangle function to find find which vertex are inside,
    basic triangulation is performed for quads and ngons
    '''
    mask = []
    for vert in verts_or:
        inside = False
        for p in pols_cut:
            for i in range(2, len(p)):
                inside = pt_in_triangle(vert, verts_cut[p[0]], verts_cut[p[i-1]], verts_cut[p[i]])
                if inside:
                    break
            if inside:
                break
        if inside:
            mask.append(1)
        else:
            mask.append(0)
    return mask


def verts_inside_pols(verts, verts_cut, pols_cut, offset):
    '''Which vectors should be masked and inside which polygon they are'''
    mask = []
    # which verts does the pol have inside
    poly_lib = [[] for p in pols_cut]
    # in which polygon is the vert
    v_in_n_pol = [[] for p in verts]
    for vi, vert in enumerate(verts):
        inside = False
        sel_pol = -1
        for p in pols_cut:
            for i in range(2, len(p)):
                inside = pt_in_triangle(vert, verts_cut[p[0]], verts_cut[p[i-1]], verts_cut[p[i]])
                if inside:
                    sel_pol = pols_cut.index(p)
                    break
            if inside:
                break
        if inside:
            v_in_n_pol[vi].append(sel_pol)
            poly_lib[sel_pol].append(vi + offset)
            mask.append(1)
        else:
            mask.append(0)
    return poly_lib, mask, v_in_n_pol

def verts_inside_pols2(verts, verts_cut, pols_cut, offset):
    '''Which vectors should be masked and inside which polygon they are'''
    mask = []
    # which verts does the pol have inside
    poly_lib = [[] for p in pols_cut]
    # in which polygon is the vert
    v_in_n_pol = [[] for p in verts]
    for vi, vert in enumerate(verts):
        inside = False
        sel_pol = -1
        for p in pols_cut:
            inside_pol = False
            for i in range(2, len(p)):
                inside_pol = pt_in_triangle(vert, verts_cut[p[0]], verts_cut[p[i-1]], verts_cut[p[i]])
                if inside_pol:
                    
                    break
            if inside_pol:
                inside = inside or inside_pol
                sel_pol = pols_cut.index(p)
                v_in_n_pol[vi].append(sel_pol)
                poly_lib[sel_pol].append(vi + offset)
                
        if inside:
            
            mask.append(1)
        else:
            mask.append(0)
    return poly_lib, mask, v_in_n_pol


def edges_affected_by_pols(lib_pack, pols):
    '''find edges related to polygons corners'''
    original_edge, intersection_lib = lib_pack
    eds_out_all = []
    for p in pols:
        eds_out = []
        for i, c in enumerate(p):
            ed = [p[i - 1], c]
            ed1 = [c, p[i - 1]]
            # ind = original_edge.index(sorted(ed))
            # for k in range(1, len(intersection_lib[ind])):
                    # ed_out = (intersection_lib[ind][k-1][1], intersection_lib[ind][k][1])
                    # eds_out.append(ed_out)
            ind = -1
            if ed in original_edge:
                ind = original_edge.index(ed)
            else:
                if ed1 in original_edge:
                    ind = original_edge.index(ed1)
            if ind != -1:
                for k in range(1, len(intersection_lib[ind])):
                    ed_out = (intersection_lib[ind][k-1][1], intersection_lib[ind][k][1])
                    eds_out.append(ed_out)


        eds_out_all.append(eds_out)
    return eds_out_all


def vertex_affected_by_edges(edges_aff, n_pol_sp):
    '''vertex of polygon + vertex inside polygon'''
    vertex_affected = []
    for i, ea in enumerate(edges_aff):
        af = []
        for e in ea:
            af.append(e[0])
            af.append(e[1])
        af = list(set(af))
        if n_pol_sp:
            af += n_pol_sp[i]
        vertex_affected.append(af)

    return vertex_affected


def edges_affected_by_verts(vertex_affected_n, edges_out, first_edge, mask):
    edges = [[s for s in edges_out if s[0] in af and s[1] in af and mask[s[0]] and mask[s[1]]] for af in vertex_affected_n]
    first_edges = [[f for e, f  in zip(edges_out, first_edge) if e[0] in af and e[1] in af and mask[e[0]] and mask[e[1]]] for af in vertex_affected_n]

    return edges, first_edges




def filter_pols_inner(pols_or, mask, points_inside_p, edges_or, intersection_lib):
    '''Discriminate if a polygon is inside, outside or both (special)'''

    pols_out = []
    pols_out_specials = []
    specials_id = []


    for i, p in enumerate(pols_or):
        s = 0
        special = len(points_inside_p[i]) > 0
        if not special:
            for e1, e2 in zip(p, p[1:]+[p[0]]):
                s += mask[e1]
                ind = edges_or.index(sorted([e1, e2]))
                if len(intersection_lib[ind]) > 2:
                    special = True
                    break
        if not special:
            if s == len(p):
                pols_out.append(p)
        else:
            pols_out_specials.append(p)
            specials_id.append(i)

    return pols_out, pols_out_specials, specials_id

def filter_pols_inner_outside(pols_or, mask, points_inside_p, edges_or, intersection_lib):
    '''Discriminate if a polygon is inside, outside or both (special)'''

    pols_out = []
    pols_out_specials = []
    specials_id = []

    for i, p in enumerate(pols_or):
        s = 0
        special = len(points_inside_p[i]) > 0
        if not special:
            for e1, e2 in zip(p, p[1:]+[p[0]]):
                s += mask[e1]
                ind = edges_or.index(sorted([e1, e2]))
                if len(intersection_lib[ind]) > 2:
                    special = True
                    break
        if not special:
            if s < len(p):
                pols_out.append(p)
        else:
            pols_out_specials.append(p)
            specials_id.append(i)

    return pols_out, pols_out_specials, specials_id

def filter_inner_pols(pols_or, mask):
    '''Discriminate polygons that are inside'''
    pols_out = []
    for p in pols_or:
        s = 0
        for c in p:
            s += mask[c]
        if s == len(p):
            pols_out.append(p)

    return pols_out



def coincident_verts(v_len, v_cut_len, verts_cut, verts_or, tolerance):
    '''check if cutting geometry share any vertex with original geometry'''

    repeated_verts = []
    replacer_verts = []
    verts_cross_i = cross_indices2(v_len, v_cut_len)

    dists = [length_v2((verts_cut[e[1]][0] - verts_or[e[0]][0], verts_cut[e[1]][1] - verts_or[e[0]][1])) for e in verts_cross_i]
    repeated_v = []
    for dist, indices in zip(dists, verts_cross_i):

        if dist < tolerance:
            repeated_v.append(indices)
            repeated_verts.append(indices[1]+v_len)
            replacer_verts.append(indices[0])

    return [repeated_verts, replacer_verts]
    # return [replacer_verts, repeated_verts]

def replace_edges_indices(edges_out, coincidences):
    '''return the edges with the first index of the coincidence'''
    repeated_verts, replacer_verts = coincidences
    ed_out = []
    for e in edges_out:
        e_f = []
        for v in e:
            vi = v
            if v in repeated_verts:
                ind = repeated_verts.index(v)
                vi = replacer_verts[ind]
            e_f.append(vi)
        ed_out.append(e_f)
    return ed_out

def fill_holes(vertices, edges, s):
    '''create pols from edge-net'''
    if not edges and not vertices:
        return False

    if len(edges[0]) != 2:
        return False

    bm = bmesh_from_pydata(vertices, edges, [])

    bmesh.ops.holes_fill(bm, edges=bm.edges[:], sides=s)
    verts, edges, faces = pydata_from_bmesh(bm)
    faces =[f for i, f in enumerate(faces) if bm.faces[i].calc_area() > 1e-6]

    bm.free()
    return (verts, edges, faces)

def recalc_normals(vertices, edges, faces):
    '''recalculate pols normals'''
    if len(faces) > 0:
        bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)

        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        new_vertices, new_edges, new_faces = pydata_from_bmesh(bm)
        bm.free()

        return (new_vertices, new_edges, new_faces)
    else:
        return vertices, edges, faces


def build_fill_poly(verts_out, edges_affected_n, new_index):
    '''Take edges and find a path between them'''
    new_pols = []
    for p in edges_affected_n:
        if len(p) < 3:
            continue
        sp = []
        _, _, sp = fill_holes(verts_out, p, len(p))
        sp = [[new_index[c] for c in pl]for pl in sp]
        new_pols += sp

    return new_pols


def build_fill_poly_old_index(verts_out, edges_affected_n):
    '''Take edges and find a path between them'''
    new_pols = []
    for p in edges_affected_n:
        if len(p) < 3:
            continue
        sp = []
        _, _, sp = fill_holes(verts_out, p, len(p))
        # sp = [[new_index[c] for c in pl]for pl in sp]
        new_pols += sp

    return new_pols


def create_lib_helpers(intersection_lib, v_out_len):
    '''Fill references for later faster search'''

    edges_in_verts = [[] for i in range(v_out_len)]

    for i, e in enumerate(intersection_lib):

        if len(e) > 2:
            for ind in e:
                edges_in_verts[ind[1]].append(i)

    return edges_in_verts


def remove_double_poly(pols_out_cut, new_pols):
    '''delete repeated polygons'''
    for p in pols_out_cut:
        for p2 in new_pols:
            if sorted(p2) == sorted(p):
                new_pols.remove(p2)


def update_pols_cut(pols_cut_special, v_len, coincidences):
    '''update pols_cut  index'''
    repeated_verts, replacer_verts = coincidences
    pols_cut_special_ai = [[c+v_len for c in p] for p in pols_cut_special]
    # '''remove repetitions on pols'''
    pols_cut_special_ai2 = []
    for p in pols_cut_special_ai:
        pols_cut_special_ai2_local = []
        for vi in p:
            if vi in repeated_verts:
                ind = repeated_verts.index(vi)
                vi = replacer_verts[ind]
            pols_cut_special_ai2_local.append(vi)
        pols_cut_special_ai2.append(pols_cut_special_ai2_local)

    return pols_cut_special_ai2


def create_mask_and_helpers(params, v_len, v_cut_len, v_out_len, intesection_index):
    '''which polygons are inside and where are they'''
    verts_or, _, pols_or, verts_cut, pols_cut = params

    verts_inside_pol_cut, mask_verts_or, _ = verts_inside_pols(verts_or, verts_cut, pols_cut, 0)

    verts_inside_pol_or, mask_of_cut, vert_cut_in_pols_or = verts_inside_pols(verts_cut, verts_or, pols_or, v_len)

    mask = mask_verts_or + mask_of_cut + [1]*(v_out_len - v_len - v_cut_len)

    for ex in intesection_index:
        mask[ex] = 1

    return mask, verts_inside_pol_cut, verts_inside_pol_or, vert_cut_in_pols_or


def create_mask_and_helpers_exclude(params, v_len, v_cut_len, v_out_len, intesection_index, v_cut_new_index):
    '''which polygons are inside and where are they'''
    verts_or, _, pols_or, verts_cut, pols_cut = params

    verts_inside_pol_cut, mask_verts_or, _ = verts_inside_pols(verts_or, verts_cut, pols_cut, 0)

    verts_inside_pol_or, mask_of_cut, vert_cut_in_pols_or = verts_inside_pols(verts_cut, verts_or, pols_or, v_len)

    mask = mask_verts_or + mask_of_cut + [1]*(v_out_len - v_len - v_cut_len)

    for ex in intesection_index:
        mask[ex] = 1

    verts_inside_pol_or = [[v for v in p if v_cut_new_index[v-v_len] != -1]for p in verts_inside_pol_or]


    return mask, verts_inside_pol_cut, verts_inside_pol_or, vert_cut_in_pols_or


def create_mask_for_edges(params, v_len, v_cut_len, v_out_len, intesection_index, exclude_cutter):
    '''which polygons are inside and where are they'''
    verts_or, _, _, verts_cut, pols_cut = params

    _, mask_verts_in, _ = verts_inside_pols(verts_or, verts_cut, pols_cut, 0)

    mask = mask_verts_in + [exclude_cutter]*v_cut_len + [1]*(v_out_len - v_len - v_cut_len)

    for ex in intesection_index:
        mask[ex] = 1

    return mask


def update_geometry(verts, pols, edges, mask):
    '''mask geometry by vertices mask'''
    new_index = create_new_indexes(verts, mask)
    verts_out = [v for v, m in zip(verts, mask) if m]
    pols_out = [[new_index[s] for s in p] for p in pols]
    edges_out = mask_edges(edges, new_index)
    return verts_out, edges_out, pols_out

def mask_edges(edges, new_index):
    '''mask edges using new_index mask'''
    return [[new_index[e[0]], new_index[e[1]]] for e in edges if new_index[e[0]] != -1 and new_index[e[1]] != -1]
def mask_edges_old_index(edges, new_index):
    '''mask edges using new_index mask'''
    return [[e[0], e[1]] for e in edges if new_index[e[0]] != -1 and new_index[e[1]] != -1]

def filter_geometry_by_pol_data(pols, verts, edges):
    '''mask geometry using the polygon data as mask'''
    ind = flat_set(pols)
    mask = []
    for i in range(len(verts)):
        mask.append(i in ind)

    return update_geometry(verts, pols, edges, mask)


def create_edges_cut(pols_cut, exclude_cutter):
    if exclude_cutter:
        edges_cut, interior_edges = pols_edges_especial(pols_cut, True)
        exclude_interior_edges(edges_cut, interior_edges)
    else:
        edges_cut, _ = pols_edges_especial(pols_cut, True)

    return edges_cut


def invert_mask_and_inner_pols(mask, verts_cut_in_pols_or, v_len, v_cut_len):
    ''' invert mask and check cutting points inside original pols'''
    mask = [not m or ((i >= (v_len))and m) for i, m in enumerate(mask)]
    mask = [True or ((i >= (v_len))and m) for i, m in enumerate(mask)]
    for i in range(v_cut_len):
        if len(verts_cut_in_pols_or[i]) == 0:
            mask[v_len+i] = False
    return mask


def edges_affected(lib_pack, specials_in, inside_pol_special, edges_out, first_edge, mask):
    edges_aff = edges_affected_by_pols(lib_pack, specials_in)
    vertex_affected_n = vertex_affected_by_edges(edges_aff, inside_pol_special)
    edges_affected_n, first_edges_n = edges_affected_by_verts(vertex_affected_n, edges_out, first_edge, mask)
    return edges_affected_n, first_edges_n

def crop_verts(self, output_lists, params):
    '''return the vertices that lay inside the the cutting polygons'''
    verts_or, _, _, verts_cut, pols_cut = params

    if not self.mode_action == 'Union':
        mask = verts_inside_pols_basic(verts_or, verts_cut, pols_cut)
        if self.mode_action == 'Difference':
            mask = [not m for m in mask]

        verts_out = [v for v, m in zip(verts_or, mask) if m]
    else:
        verts_out = verts_or
    if not self.exclude_cutter:
        verts_out += verts_cut

    output_lists[0].append(verts_out)

def crop_edges(self, output_lists, params):
    '''return the edges inside the cutting polygons'''
    verts_or, edges_or, _, verts_cut, pols_cut = params
    v_len = len(verts_or)
    v_cut_len = len(verts_cut)


    edges_cut = create_edges_cut(pols_cut, self.exclude_cutter)
    verts_out, _, edges_out = mesh_join([verts_or, verts_cut], [], [edges_or, edges_cut])

    coincidences = coincident_verts(v_len, v_cut_len, verts_cut, verts_or, self.mask_t)
    edges_out = replace_edges_indices(edges_out, coincidences)


    verts_out, ed_inter = intersect_edges_2d(verts_out, edges_out, 1.0e-5, len(edges_or))
    edges_out, intersection_lib, intesection_indices, first_edge = edges_from_ed_inter(ed_inter)
    
    if not self.partial_mode == "Cut":
        mask_special = []
        for e in intersection_lib[:len(edges_or)]:
            if len(e) > 2:
                mask_special.append(e[0][1])
                mask_special.append(e[-1][1])

    v_out_len = len(verts_out)
    if not self.mode_action == 'Union':
        mask = create_mask_for_edges(params, v_len, v_cut_len, v_out_len, intesection_indices, not self.exclude_cutter)

        inside = self.mode_action == 'Intersect'
        if self.mode_action == 'Difference':
            mask = [not m if i < v_len else m for i, m in enumerate(mask)]


        if not self.partial_mode == "Cut":
            edges_out = edges_or
            mask = mask[:v_len]
            verts_out = verts_or
            include = self.partial_mode == "Include"
            if include:
                for m in mask_special:
                    mask[m] = include
            elif self.partial_mode == "Only":
                mask = [0]*v_len
                for m in mask_special:
                    mask[m] = 1
        # else:

            # for i in range(len(verts_cut)):
                # related = not self.exclude_cutter
                # for e in edges_out:
                    # if v_len+i in e:
                        # if mask[e[0]] and mask[e[1]]:
                            # related = True
                # mask[v_len+i] = related
        new_index = create_new_indexes(verts_out, mask)
        # edges_out = mask_edges(edges_out, new_index)
        if self.exclude_cutter:
            valid_e = valid_edge_exclude_cutter
        else:
            valid_e = valid_edge
        edges_out = [[new_index[e[0]], new_index[e[1]]] for e, f_e in zip(edges_out, first_edge) if new_index[e[0]] != -1 and new_index[e[1]] != -1 and  valid_e(e, v_len, v_cut_len, verts_out, verts_cut, pols_cut, f_e, inside)]
        verts_out = [v for v, m in zip(verts_out, mask) if m]
    output_lists[0].append(verts_out)
    output_lists[1].append(edges_out)

def geometry_full_pols(self, params, v_out_len, intersection_lib, intesection_indices, v_cut_new_index):
    verts_or, edges_or, pols_or, verts_cut, _ = params
    v_len = len(verts_or)
    v_cut_len = len(verts_cut)
    mask, _, inside_pols_or, verts_cut_in_pols_or = create_mask_and_helpers_exclude(params, v_len, v_cut_len, v_out_len, intesection_indices, v_cut_new_index)

    if self.mode_action == 'Difference':
        mask = invert_mask_and_inner_pols(mask, verts_cut_in_pols_or, v_len, v_cut_len)

    pols_out, specials_in, _ = filter_pols_inner(pols_or, mask, inside_pols_or, edges_or, intersection_lib)
    if self.partial_mode == "Include":
        pols_out += specials_in
    elif self.partial_mode == "Only":
        pols_out = specials_in

    verts_out_new, edges_out_masked, pols_out = filter_geometry_by_pol_data(pols_out, verts_or, edges_or)

    return verts_out_new, edges_out_masked, pols_out

def valid_edge(e, v_len, v_cut_len, verts_out, verts_cut, pols_cut, f_edge, inside, coincidences):

    # if e[0] >= v_len + v_cut_len and e[1] >= v_len + v_cut_len and f_edge[0] < v_len and f_edge[1] < v_len:
    
    e0_cut = e[0] >= v_len or e[0] in coincidences[1]
    e1_cut = e[1] >= v_len or e[1] in coincidences[1]
    print("A", e, f_edge, e0_cut, e1_cut)
    # if e[0] >= v_len  and e1_cut and f_edge[0] < v_len and f_edge[1] < v_len:
    # if e0_cut and e[1] >= v_len and f_edge[0] < v_len and (f_edge[1] < v_len or f_edge[0] < v_len):
    if e0_cut and e[1] >= v_len and f_edge[0] < v_len and (f_edge[1] < v_len ) :
        # print("W", e, f_edge)
        
        mid_point = interp_v3_v3v3(verts_out[e[0]], verts_out[e[1]], 0.5)
        valid = verts_inside_pols_basic([mid_point], verts_cut, pols_cut)[0]
        perp = sub_v3_v3v3(verts_out[e[1]],verts_out[e[0]])
        mid2 = [mid_point[0] + perp[1]*0.001, mid_point[1] + perp[0]*0.001, mid_point[2]]
        mid3 = [mid_point[0] + perp[1]*0.001, mid_point[1] - perp[0]*0.001, mid_point[2]]
        valid2 = verts_inside_pols_basic([mid2,mid3], verts_cut, pols_cut)
        print("W", e, f_edge, valid, valid2)
        # valid = False
        if valid == inside:
            print("W2", e, f_edge, valid)
        
        return valid == inside
    elif not inside:
        # mid_point = interp_v3_v3v3(verts_out[e[0]], verts_out[e[1]], 0.5)
        # valid = verts_inside_pols_basic([mid_point], verts_cut, pols_cut)[0]
        # return valid == inside
        if v_len + v_cut_len <= e[1] and f_edge[0] < v_len:
            print("X", e)
            mid_point = interp_v3_v3v3(verts_out[e[0]], verts_out[e[1]], 0.5)
            valid = verts_inside_pols_basic([mid_point], verts_cut, pols_cut)[0]
            return valid == inside
        elif e[0] in coincidences[1] and f_edge[1] < v_len:
            
            mid_point = interp_v3_v3v3(verts_out[e[0]], verts_out[e[1]], 0.5)
            valid = verts_inside_pols_basic([mid_point], verts_cut, pols_cut)[0]
            print("Z", e, f_edge[0],f_edge[1],valid)
            return valid == inside
            
        elif e0_cut or e1_cut:
            mid_point = interp_v3_v3v3(verts_out[e[0]], verts_out[e[1]], 0.5)
            valid = verts_inside_pols_basic([mid_point], verts_cut, pols_cut)[0]
            perp = sub_v3_v3v3(verts_out[e[1]],verts_out[e[0]])
            perp2=list(Vector(perp).cross(Vector((0,0,1))).normalized())
            print(perp, perp2)
            mid2 = [mid_point[0] + perp2[0]*0.001, mid_point[1] + perp2[1]*0.001, mid_point[2]]
            mid3 = [mid_point[0] - perp2[0]*0.001, mid_point[1] - perp2[1]*0.001, mid_point[2]]
            # mid2 = [mid_point[0] + perp[1]*0.001, mid_point[1] + perp[0]*0.001, mid_point[2]]
            # mid3 = [mid_point[0] + perp[1]*0.001, mid_point[1] - perp[0]*0.001, mid_point[2]]
            valid2 = verts_inside_pols_basic([mid2,mid3], verts_cut, pols_cut)
            print("WX", e, f_edge, valid, valid2)
            return not all(valid2)
            
        
            
        # elif e[0] in coincidences[1] and e[1] in coincidences[1]:
            # return True
            
        
        else:
            return True
    else:
            return True

def valid_edge_exclude_cutter(e, v_len, v_cut_len, verts_out, verts_cut, pols_cut, f_edge, inside):

    if e[0] >= v_len + v_cut_len and e[1] >= v_len + v_cut_len and f_edge[0] < v_len and f_edge[1] < v_len:

        mid_point = interp_v3_v3v3(verts_out[e[0]], verts_out[e[1]], 0.5)
        valid = verts_inside_pols_basic([mid_point], verts_cut, pols_cut)[0]

        return valid == inside
    else:
        if v_len + v_cut_len > f_edge[0] > v_len and v_len + v_cut_len > f_edge[1] > v_len:
            return False
        else:
            return True
        
def remove_floating_pols(periemter_pols, verts_cut_in_pols_or, new_pols, new_index, v_len):
    for p in periemter_pols:
        in_pol = verts_cut_in_pols_or[p[0]]
        if in_pol:
            for i, np in enumerate(new_pols):
                if len(p) == len(np):
                    embed_pol = all(new_index[c+v_len] in np for c in p[1:])
                    if embed_pol:
                        new_pols.remove(np)
                        break

def croped_pols(params, edges_out, intersection_lib, intesection_indices, verts_out, original_edge, first_edge, coincidences, v_cut_perimeter_len, inside, check_concavity, mask_cut, periemter_pols):
    '''build the new polygons'''
    verts_or, edges_or, pols_or, verts_cut, pols_cut = params
    v_len = len(verts_or)
    v_cut_len = len(verts_cut)
    v_out_len = len(verts_out)
    mask, _, inside_pols_or, verts_cut_in_pols_or = create_mask_and_helpers(params, v_len, v_cut_len, v_out_len, intesection_indices)
    print(inside_pols_or)
    print(verts_cut_in_pols_or)
    lib_pack = (original_edge, intersection_lib)
        
    if not inside:  
        mask_i = [m for m in mask]
        mask = invert_mask_and_inner_pols(mask, verts_cut_in_pols_or, v_len, v_cut_len)
        # for cv, ov, in zip(*coincidences):
            # mask[cv] = 1
            # mask[ov] = 0
    else:
        for cv, ov, in zip(*coincidences):
            mask[cv] = 0
            mask[ov] = 1
        
    for i, m in enumerate(mask_cut):
        print (i,m)
        mask[v_len+i] = mask[v_len+i] and m

    new_index = create_new_indexes(verts_out, mask)
    pols_out, specials_in, specials_id = filter_pols_inner(pols_or, mask, inside_pols_or, edges_or, intersection_lib)
    if not inside:
        pols_out, specials_in, specials_id = filter_pols_inner_outside(pols_or, mask_i, inside_pols_or, edges_or, intersection_lib)
    inside_pol_special = [inside_pols_or[i] for i in specials_id]
    verts_out_new = [v for v, m in zip(verts_out, mask) if m]

    edges_out_masked = mask_edges(edges_out, new_index)

    edges_affected_n, first_e = edges_affected(lib_pack, specials_in, inside_pol_special, edges_out, first_edge, mask)
    # print("ea", edges_affected_n[3])
    e_out =[[(new_index[e[0]], new_index[e[1]])  for ne, e in enumerate(pg) ]for np, pg in enumerate(edges_affected_n)]
    # print(e_out[3])
    print(([e  for p in edges_affected_n for e in p]))
    # print(edges_affected_n[4])
        
    if check_concavity:
        edges_affected_n = [[(e[0], e[1])  for ne, e in enumerate(pg) if valid_edge(e, v_len, v_cut_perimeter_len, verts_out, verts_cut, pols_cut, first_e[np][ne], inside, coincidences)] for np, pg in enumerate(edges_affected_n)]
        
    # e_out =[[(new_index[e[0]], new_index[e[1]])  for ne, e in enumerate(pg) ]for np, pg in enumerate(edges_affected_n)]
    # print(e_out[3])
    new_pols = build_fill_poly(verts_out, edges_affected_n, new_index)
    new_pols_old_id = build_fill_poly_old_index(verts_out, edges_affected_n)
    pols_out = [[new_index[vi] for vi in p] for p in pols_out]
    if not inside:
        print(periemter_pols)
        remove_floating_pols(periemter_pols, verts_cut_in_pols_or, new_pols, new_index, v_len)
                    
    pols_out = new_pols + pols_out
        
      # if check_concavity:
        # verts_out_new, edges_out_masked, pols_out = filter_geometry_by_pol_data(pols_out, verts_out_new, edges_out_masked)

    verts_out_new, edges_out_masked, pols_out = recalc_normals(verts_out_new, edges_out_masked, pols_out)
    return verts_out_new, e_out, pols_out, specials_in

def croped_pols_old2(params, edges_out, intersection_lib, intesection_indices, verts_out, original_edge, first_edge, coincidences, v_cut_perimeter_len, inside, check_concavity, mask_cut, periemter_pols):
    '''build the new polygons'''
    verts_or, edges_or, pols_or, verts_cut, pols_cut = params
    v_len = len(verts_or)
    v_cut_len = len(verts_cut)
    v_out_len = len(verts_out)
    mask, _, inside_pols_or, verts_cut_in_pols_or = create_mask_and_helpers(params, v_len, v_cut_len, v_out_len, intesection_indices)
    print(inside_pols_or)
    print(verts_cut_in_pols_or)
    lib_pack = (original_edge, intersection_lib)
        
    if not inside:  
        mask_i = [m for m in mask]
        mask = invert_mask_and_inner_pols(mask, verts_cut_in_pols_or, v_len, v_cut_len)
        # for cv, ov, in zip(*coincidences):
            # mask[cv] = 1
            # mask[ov] = 0
    else:
        for cv, ov, in zip(*coincidences):
            mask[cv] = 0
            mask[ov] = 1
        
    for i, m in enumerate(mask_cut):
        print (i,m)
        mask[v_len+i] = mask[v_len+i] and m

    new_index = create_new_indexes(verts_out, mask)
    pols_out, specials_in, specials_id = filter_pols_inner(pols_or, mask, inside_pols_or, edges_or, intersection_lib)
    if not inside:
        pols_out, specials_in, specials_id = filter_pols_inner_outside(pols_or, mask_i, inside_pols_or, edges_or, intersection_lib)
    inside_pol_special = [inside_pols_or[i] for i in specials_id]
    verts_out_new = [v for v, m in zip(verts_out, mask) if m]

    edges_out_masked = mask_edges(edges_out, new_index)

    edges_affected_n, first_e = edges_affected(lib_pack, specials_in, inside_pol_special, edges_out, first_edge, mask)
    if check_concavity:
        edges_affected_n = [[(e[0], e[1])  for ne, e in enumerate(pg) if valid_edge(e, v_len, v_cut_perimeter_len, verts_out, verts_cut, pols_cut, first_e[np][ne], inside, coincidences)] for np, pg in enumerate(edges_affected_n)]
    # e_out =[[(new_index[e[0]], new_index[e[1]])  for ne, e in enumerate(pg) ]for np, pg in enumerate(edges_affected_n)]
    # new_pols = build_fill_poly(verts_out, edges_affected_n, new_index)
    new_pols = build_fill_poly_old_index(verts_out, edges_affected_n)
    # pols_out = [[new_index[vi] for vi in p] for p in pols_out]
    if not inside:
        remove_floating_pols(periemter_pols, verts_cut_in_pols_or, new_pols, new_index, v_len)
                    
    pols_out = new_pols + pols_out
        
    # if check_concavity:
        # verts_out_new, edges_out_masked, pols_out = filter_geometry_by_pol_data(pols_out, verts_out, edges_out)

    # verts_out_new, edges_out_masked, pols_out = recalc_normals(verts_out_new, edges_out_masked, pols_out)
    return  pols_out
    
def croped_pols_union(params, edges_out, intersection_lib, intesection_indices, verts_out, original_edge, first_edge, coincidences, v_cut_perimeter_len, inside, check_concavity, mask_cut, periemter_pols):
    '''build the new polygons'''
    verts_or, edges_or, pols_or, verts_cut, pols_cut = params
    v_len = len(verts_or)
    v_cut_len = len(verts_cut)
    v_out_len = len(verts_out)
    mask, _, inside_pols_or, verts_cut_in_pols_or = create_mask_and_helpers(params, v_len, v_cut_len, v_out_len, intesection_indices)
    print(inside_pols_or)
    print(verts_cut_in_pols_or)
    lib_pack = (original_edge, intersection_lib)
    mask = [True for m in mask]    
    # if not inside:  
        # mask_i = [m for m in mask]
        # mask = invert_mask_and_inner_pols(mask, verts_cut_in_pols_or, v_len, v_cut_len)
        # for cv, ov, in zip(*coincidences):
            # mask[cv] = 1
            # mask[ov] = 0
    
    for cv, ov, in zip(*coincidences):
        mask[cv] = 0
        mask[ov] = 1
        
    # for i, m in enumerate(mask_cut):
        # print (i,m)
        # mask[v_len+i] = mask[v_len+i] and m

    new_index = create_new_indexes(verts_out, mask)
    pols_out, specials_in, specials_id = filter_pols_inner(pols_or, mask, inside_pols_or, edges_or, intersection_lib)
    # if not inside:
        # pols_out, specials_in, specials_id = filter_pols_inner_outside(pols_or, mask_i, inside_pols_or, edges_or, intersection_lib)
    inside_pol_special = [inside_pols_or[i] for i in specials_id]
    verts_out_new = [v for v, m in zip(verts_out, mask) if m]

    edges_out_masked = mask_edges(edges_out, new_index)

    edges_affected_n, first_e = edges_affected(lib_pack, specials_in, inside_pol_special, edges_out, first_edge, mask)
    # if check_concavity:
        # edges_affected_n = [[(e[0], e[1])  for ne, e in enumerate(pg) if valid_edge(e, v_len, v_cut_perimeter_len, verts_out, verts_cut, pols_cut, first_e[np][ne], inside, coincidences)] for np, pg in enumerate(edges_affected_n)]
   
    new_pols = build_fill_poly(verts_out, edges_affected_n, new_index)
    
    pols_out = [[new_index[vi] for vi in p] for p in pols_out]
    
    remove_floating_pols(periemter_pols, verts_cut_in_pols_or, new_pols, new_index, v_len)
                    
    pols_out = new_pols + pols_out
        
    verts_out_new, edges_out_masked, pols_out = filter_geometry_by_pol_data(pols_out, verts_out_new, edges_out_masked)

    verts_out_new, edges_out_masked, pols_out = recalc_normals(verts_out_new, edges_out_masked, pols_out)
    return verts_out_new, edges_out_masked, pols_out, specials_in

def croped_pols_old(self, params, edges_out, intersection_lib, intesection_indices, verts_out, original_edge, first_edge, coincidences, v_cut_perimeter_len, inside):
    '''build the new polygons'''
    verts_or, edges_or, pols_or, verts_cut, pols_cut = params
    v_len = len(verts_or)
    v_cut_len = len(verts_cut)
    v_out_len = len(verts_out)
    mask, _, inside_pols_or, verts_cut_in_pols_or = create_mask_and_helpers(params, v_len, v_cut_len, v_out_len, intesection_indices)

    if not inside:
        mask = invert_mask_and_inner_pols(mask, verts_cut_in_pols_or, v_len, v_cut_len)

    for c in coincidences[1]:
        mask[c] = 1
    if self.mode_action == 'Union':
        mask[v_len:v_len+v_cut_len] = [1]* v_cut_len

    lib_pack = (original_edge, intersection_lib)


    pols_out, specials_in, specials_id = filter_pols_inner(pols_or, mask, inside_pols_or, edges_or, intersection_lib)
    inside_pol_special = [inside_pols_or[i] for i in specials_id]



    edges_affected_n, first_e = edges_affected(lib_pack, specials_in, inside_pol_special, edges_out, first_edge, mask)

    edges_affected_n = [[(e[0], e[1])  for ne, e in enumerate(pg) if valid_edge(e, v_len, v_cut_perimeter_len, verts_out, verts_cut, pols_cut, first_e[np][ne], inside, coincidences)] for np, pg in enumerate(edges_affected_n)]

    new_pols = build_fill_poly_old_index(verts_out, edges_affected_n)

    pols_out = new_pols + pols_out

    return pols_out

def croped_pols_old_reversed(self, params, edges_out, intersection_lib, intesection_indices, verts_out, original_edge, first_edge, coincidences, inside, edges_cut):
    '''build the new polygons'''
    verts_or, _, _, verts_cut, pols_cut = params
    v_len = len(verts_or)
    v_cut_len = len(verts_cut)
    v_out_len = len(verts_out)
    mask, inside_pols_cut, _, verts_cut_in_pols_or = create_mask_and_helpers(params, v_len, v_cut_len, v_out_len, intesection_indices)

    if not inside:
        mask = invert_mask_and_inner_pols(mask, verts_cut_in_pols_or, v_len, v_cut_len)

    for c in coincidences[1]:
        mask[c] = 1
    # if self.mode_action == 'Union':
        # mask[v_len:v_len+v_cut_len] = [1]* v_cut_len


    lib_pack = (original_edge, intersection_lib)

    mask_in_specials = mask[v_len:v_len+v_cut_len]
    # mask_in_specials = [1]* v_cut_len


    pols_out_cut, pols_cut_special, _ = filter_pols_inner(pols_cut, mask_in_specials, inside_pols_cut, edges_cut, intersection_lib[v_len:])

    pols_cut_special_ai = update_pols_cut(pols_cut_special, v_len, coincidences)
    edges_affected_n_cut, _ = edges_affected(lib_pack, pols_cut_special_ai, [], edges_out, first_edge, mask)
    edges_affected_n = edges_affected_n_cut

    new_pols = build_fill_poly_old_index(verts_out, edges_affected_n)

    remove_double_poly(pols_out_cut, new_pols)

    # pols_out = pols_out + pols_out_cut + new_pols
    # new_pols = pols_out_cut + new_pols

    # pols_out = new_pols + pols_out + pols_out_cut
    pols_out = new_pols #+ pols_out_cut

    return pols_out

def crop_pols(self, output_lists, params):
    '''intersect edges, check old polygons and build the new ones'''

    verts_or, edges_or, pols_or, verts_cut, pols_cut = params
    v_len = len(verts_or)
    v_cut_len = len(verts_cut)

    #create edges from pols
    if not edges_or and pols_or:
        edges_or = pols_edges([pols_or], True)[0]
    else:
        edges_or = [sorted(e) for e in edges_or]
        params = [verts_or, edges_or, pols_or, verts_cut, pols_cut]
    remove_inner_edges = self.mode_action == 'Difference' or (self.mode_action == 'Intersect' and self.exclude_cutter) or not self.partial_mode == "Cut"
    edges_cut = create_edges_cut(pols_cut, remove_inner_edges) or self.mode_action == 'Union'
    v_cut_new_index = []
    if remove_inner_edges:
        ec = flat_set(edges_cut)
        mask = [True in ec for i in range(v_cut_len)]
        new_index = create_new_indexes(verts_cut, mask)
        # edges_cut = mask_edges(edges_cut, new_index)
        # verts_cut = [v for v, m in zip(verts_cut, mask) if m]
        # v_cut_len = len(verts_cut)
        v_cut_new_index = new_index
        mask_cut = [i in ec for i in range(v_cut_len)]
        new_index = create_new_indexes(verts_cut, mask_cut)
        v_perimeter_cut = [v for v, m in zip(verts_cut,mask) if m]
        perimeter_edges = mask_edges_old_index(edges_cut, new_index)
        periemter_pols = build_fill_poly_old_index(verts_cut, [perimeter_edges])
        print(periemter_pols)
    else:
        mask_cut = [True for i in range(v_cut_len)]
        periemter_pols=[]
        # params = [verts_or, edges_or, pols_or, verts_cut, pols_cut]

    verts_out, _, edges_out = mesh_join([verts_or, verts_cut], [], [edges_or, edges_cut])

    #check coincidences
    if self.check_coincidences:
        coincidences = coincident_verts(v_len, v_cut_len, verts_cut, verts_or, self.mask_t)
        original_edge = replace_edges_indices(edges_out, coincidences)
    else:
        coincidences = [[], []]
        original_edge = edges_out

    verts_out, ed_inter = intersect_edges_2d(verts_out, original_edge, self.mask_t, len(edges_or))
    edges_out, intersection_lib, intesection_indices, first_edge = edges_from_ed_inter(ed_inter)

    v_out_len = len(verts_out)
    if self.mode_action == 'Union':
        # verts_out_new, edges_out_masked, pols_out, _ = croped_pols_union(params, edges_out, intersection_lib, intesection_indices, verts_out, original_edge, first_edge, coincidences, v_cut_len, self.mode_action == 'Intersect', self.check_concavity, mask_cut, periemter_pols)
        # pols_out = croped_pols_old2(params, edges_out, intersection_lib, intesection_indices, verts_out, original_edge, first_edge, coincidences, v_cut_len, True, self.check_concavity, mask_cut, periemter_pols)
        pols_out = croped_pols_old2(params, edges_out, intersection_lib, intesection_indices, verts_out, original_edge, first_edge, coincidences, v_cut_len, False, self.check_concavity, mask_cut, periemter_pols)
        pols_out2 = croped_pols_old2(params, edges_out, intersection_lib, intesection_indices, verts_out, original_edge, first_edge, coincidences, v_cut_len, True, self.check_concavity, mask_cut, periemter_pols)
        print([p for p in pols_out])
        # print(pols_out2)
        remove_double_poly(pols_out2, pols_out)
        pols_out += pols_out2
        # pols_out = croped_pols_old(self, params, edges_out, intersection_lib, intesection_indices, verts_out, original_edge, first_edge, coincidences, v_cut_len, False)
        # pols_out2 = croped_pols_old(self, params, edges_out, intersection_lib, intesection_indices, verts_out, original_edge, first_edge, coincidences, v_cut_len, True)
        # pols_out += pols_out2
        
        # pols_reversed = croped_pols_old_reversed(self, params, edges_out, intersection_lib, intesection_indices, verts_out, original_edge, first_edge, coincidences, False, edges_cut)
        # remove_double_poly(pols_reversed, pols_out)
        # pols_out = pols_out + pols_reversed
        # pols_out = pols_reversed
        
        verts_out_new = verts_out
        edges_out_masked = edges_out
        # verts_out_new, edges_out_masked, pols_out = filter_geometry_by_pol_data(pols_out, verts_out, edges_out)
        # verts_out_new, edges_out_masked, pols_out = recalc_normals(verts_out_new, edges_out_masked, pols_out)

    else:
        if not self.partial_mode == "Cut":

            verts_out_new, edges_out_masked, pols_out = geometry_full_pols(self, params, v_out_len, intersection_lib, intesection_indices, v_cut_new_index)
        else:
            verts_out_new, edges_out_masked, pols_out, _ = croped_pols(params, edges_out, intersection_lib, intesection_indices, verts_out, original_edge, first_edge, coincidences, v_cut_len, self.mode_action == 'Intersect', self.check_concavity, mask_cut, periemter_pols)

    output_lists[0].append(verts_out_new)
    output_lists[1].append(edges_out_masked)
    output_lists[2].append(pols_out)
