# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


from mathutils import Vector
from mathutils.geometry import area_tri as area
from mathutils.geometry import tessellate_polygon as tessellate
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata
from sverchok.utils.modules.matrix_utils import vectors_center_axis_to_matrix
from sverchok.utils.modules.vertex_utils import vertex_shell_factor, adjacent_edg_pol
from sverchok.nodes.analyzer.mesh_filter import Faces


def areas_from_polygons(verts, polygons, sum_faces=False):

    areas = []
    concat_area = areas.append

    for polygon in polygons:
        num = len(polygon)
        if num == 3:
            concat_area(area(verts[polygon[0]], verts[polygon[1]], verts[polygon[2]]))
        elif num == 4:
            area_1 = area(verts[polygon[0]], verts[polygon[1]], verts[polygon[2]])
            area_2 = area(verts[polygon[0]], verts[polygon[2]], verts[polygon[3]])
            concat_area(area_1 + area_2)
        elif num > 4:
            ngon_area = 0.0
            subcoords = [Vector(verts[idx]) for idx in polygon]
            for tri in tessellate([subcoords]):
                ngon_area += area(*[verts[polygon[i]] for i in tri])
            concat_area(ngon_area)
        else:
            concat_area(0)

    if sum_faces:
        areas = [sum(areas)]

    return areas


def pols_perimeters(verts, polygons, sum_perimeters=False):

    perimeters = []
    concat_perimeters = perimeters.append

    for polygon in polygons:
        perimeter = 0
        for v_id, v_id2 in zip(polygon, polygon[1:]+[polygon[0]]):
            perimeter += (Vector(verts[v_id]) - Vector(verts[v_id2])).magnitude
        concat_perimeters(perimeter)
    if sum_perimeters:
        perimeters = [sum(perimeters)]
    return perimeters

def pols_vertices(vertices, faces):
    verts = [[vertices[c] for c in p] for p in faces]
    pols = [[list(range(len(p)))] for p in faces]

    vals = [verts, pols]
    return vals

def pols_sides(faces, sum_sides=False):
    vals = [len(p) for p in faces]
    if sum_sides:
        vals = [sum(vals)]
    return vals

def pols_adjacent(pols):
    vals = []
    edges = []
    pols_eds = []
    for pol in pols:
        pol_edgs = []
        for edge in zip(pol, pol[1:] + [pol[0]]):
            e_s = tuple(sorted(edge))
            pol_edgs.append(e_s)
            edges.append(e_s)
        pols_eds.append(pol_edgs)
    edges = list(set(edges))

    ad_faces = [[] for e in edges]
    for pol, eds in zip(pols, pols_eds):
        for e in eds:
            idx = edges.index(e)
            ad_faces[idx] += [pol]

    for pol, edgs in zip(pols, pols_eds):
        col_pol = []
        for edge in edgs:
            idx = edges.index(edge)
            col_pol.extend(ad_faces[idx])
            col_pol.remove(pol)
        vals.append(col_pol)

    return vals

def pols_adjacent_num(pols):
    return [len(p) for p in pols_adjacent(pols)]

def pols_neighbor(verts, pols):
    v_adj = adjacent_edg_pol(verts, pols)
    vals = []
    for pol in pols:
        pol_adj = []
        for c in pol:
            for related_pol in v_adj[c]:
                if not related_pol in pol_adj:
                    pol_adj.append(related_pol)

        pol_adj.remove(pol)
        vals.append(pol_adj)

    return vals

def pols_neighbor_num(verts, pols):
    return [len(p) for p in pols_neighbor(verts, pols)]

def pols_normals(vertices, edges, faces):
    bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)
    vals = [tuple(face.normal) for face in bm.faces]
    bm.free()
    return vals

def pols_absolute_normals(vertices, edges, faces):
    bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)
    vals = [tuple(face.normal + face.calc_center_median()) for face in bm.faces]
    bm.free()
    return vals

def pols_shell_factor(vertices, edges, faces):
    v_shell = vertex_shell_factor(vertices, edges, faces)
    vals = []
    for f in faces:
        p_shell = 0
        for c in f:
            p_shell += v_shell[c]
        vals.append(p_shell/len(f))

    return vals

def pols_center(vertices, edges, faces, origin):
    bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)
    vals = pols_origin_modes_dict[origin][1](bm.faces)
    bm.free()
    return vals

def pols_center_bounds(bm_faces):
    return [tuple(bm_face.calc_center_bounds()) for bm_face in bm_faces]

def pols_center_median(bm_faces):
    return [tuple(bm_face.calc_center_median()) for bm_face in bm_faces]

def pols_center_median_weighted(bm_faces):
    return [tuple(bm_face.calc_center_median_weighted()) for bm_face in bm_faces]

def pols_first_vert(bm_faces):
    return [tuple(bm_face.verts[0].co) for bm_face in bm_faces]

def pols_last_vert(bm_faces):
    return [tuple(bm_face.verts[-1].co) for bm_face in bm_faces]

def pols_perimeter(vertices, edges, faces):
    bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)
    vals = [bm_face.calc_perimeter() for bm_face in bm.faces]
    bm.free()
    return vals

def pols_tangent(vertices, edges, faces, direction):
    bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)
    vals = tangent_modes_dict[direction][1](bm.faces)
    bm.free()
    return vals

def pols_tangent_edge(bm_faces):
    return [tuple(bm_face.calc_tangent_edge()) for bm_face in bm_faces]

def pols_is_boundary(vertices, edges, faces):
    bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)
    interior, boundary, mask = Faces.process(bm, [], [])
    bm.free()
    return mask, interior, boundary

def pols_tangent_edge_diagonal(bm_faces):
    return [tuple(bm_face.calc_tangent_edge_diagonal()) for bm_face in bm_faces]

def pols_tangent_edge_pair(bm_faces):
    return [tuple(bm_face.calc_tangent_edge_pair()) for bm_face in bm_faces]

def pols_tangent_center_origin(bm_faces):
    return [tuple((Vector(bm_face.verts[0].co)-Vector(bm_face.calc_center_median())).normalized()) for bm_face in bm_faces]


def pols_tangent_vert_diagonal(bm_faces):
    return [tuple(bm_face.calc_tangent_vert_diagonal()) for bm_face in bm_faces]


def pols_edges(faces):
    vals = [[(c, cn) for c, cn in zip(face, face[1:]+[face[0]])] for face in faces]
    return vals

def pols_inverted(faces):
    vals = [list(reversed(f)) for f in faces]
    return vals

def pols_matrix(vertices, edges, faces, orientation):
    origin, direc = orientation
    bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)
    normals = [Vector(face.normal) for face in bm.faces]
    centers = pols_origin_modes_dict[origin][1](bm.faces)
    tangents = tangent_modes_dict[direc][1](bm.faces)
    vals = vectors_center_axis_to_matrix(centers, normals, tangents)
    bm.free()
    return vals


tangent_modes_dict = {
    'Edge':            (1, pols_tangent_edge, 'Face tangent based on longest edge'),
    'Edge Diagonal':   (2, pols_tangent_edge_diagonal, 'Face tangent based on the edge farthest from any vertex'),
    'Edge Pair':       (3, pols_tangent_edge_pair, 'Face tangent based on the two longest disconnected edges'),
    'Vert Diagonal':   (4, pols_tangent_vert_diagonal, 'Face tangent based on the two most distant vertices'),
    'Center - Origin': (5, pols_tangent_center_origin, 'Face tangent based on the mean center and first corner'),
    }
pols_origin_modes_dict = {
    'Bounds Center':          (30, pols_center_bounds, 'Center of bounding box of faces'),
    'Median Center':          (31, pols_center_median, 'Mean of vertices of each face'),
    'Median Weighted Center': (32, pols_center_median_weighted, 'Mean of vertices of each face weighted by edges length'),
    'First Vertex':           (33, pols_first_vert,  'First Vertex of Face'),
    'Last Vertex':            (34, pols_last_vert, 'First Vertex of Face'),

}
faces_modes_dict = {
    'Geometry':           (0,  'vs', 'u', '',   'vp',  pols_vertices,         'Vertices, Faces', "Geometry of each face. (explode)"),
    'Center':             (10, 'v',  '',  'c',  'vep', pols_center,           'Center', 'Center faces'),
    'Normal':             (20, 'v',  '',  '',   'vep', pols_normals,          'Normal', 'Normal of faces'),
    'Normal Absolute':    (21, 'v',  '',  '',   'vep', pols_absolute_normals, 'Normal_Abs', 'Median Center + Normal'),
    'Tangent':            (30, 'v',  '',  't',  'vep', pols_tangent,          'Tangent', 'Face tangent.'),
    'Matrix':             (40, 'm',  'u', 'qt', 'vep', pols_matrix,           'Matrix', 'Matrix of face. Z axis on normal. X to first corner'),
    'Area':               (50, 's',  '',  's',  'vps', areas_from_polygons,   'Area', "Area of faces"),
    'Perimeter':          (51, 's',  '',  's',  'vp',  pols_perimeters,       'Perimeter', 'Perimeter of faces'),
    'Sides Number':       (52, 's',  '',  's',  'p',   pols_sides,            'Sides', "Number of sides of faces"),
    'Adjacent Faces Num': (53, 's',  '',  '',   'p',   pols_adjacent_num,     'Number', "Number of Faces that share a edge with face"),
    'Neighbor Faces Num': (54, 's',  '',  '',   'vp',  pols_neighbor_num,     'Number', "Number of Faces that share a vertex with face"),
    'Sharpness':          (55, 's',  '',  '',   'vep', pols_shell_factor,     'Sharpness ', 'Average of curvature of mesh in faces vertices'),
    'Inverse':            (60, 'v',  '',  '',   'p',   pols_inverted,         'Faces', 'Reversed Polygons (Flipped)'),
    'Edges':              (61, 's',  'u', '',   'p',   pols_edges,            'Edges', 'Face Edges'),
    'Adjacent Faces':     (62, 's',  'u', '',   'p',   pols_adjacent,         'Edges', 'Faces that share a edge with face'),
    'Neighbor Faces':     (63, 's',  'u', '',   'vp',  pols_neighbor,         'Edges', 'Faces that share a vertex with face'),
    'Is Boundary':        (70, 'sss', '', '',   'vep', pols_is_boundary,      'Mask, Boundary, Interior', 'Is the face boundary'),

}
