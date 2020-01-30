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
    '''
    returns pols area as [float, float,...]
    vertices: list as [vertex, vertex, ...], being each vertex [float, float, float].
    faces: list as [polygon, polygon,..], being each polygon [int, int, ...].
    sum_faces if True it will return the sum of the areas as [float]
    '''
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
    '''
    returns pols perimeter as [float, float,...]
    vertices: list as [vertex, vertex, ...], being each vertex [float, float, float].
    faces: list as [polygon, polygon,..], being each polygon [int, int, ...].
    sum_perimeters if True it will return the sum of the perimenters as [float]
    '''
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
    '''
    Explodes geometry.
    vertices: list as [vertex, vertex, ...], being each vertex [float, float, float].
    faces: list as [polygon, polygon,..], being each polygon [int, int, ...].
    returns [[vertex, vertex, vertex,..], [vertex, vertex, vertex,..], ...] and [[polygon], [polygon],...]
    '''
    verts = [[vertices[c] for c in p] for p in faces]
    pols = [[list(range(len(p)))] for p in faces]

    vals = [verts, pols]
    return vals

def pols_to_edges(obj, unique_edges=False):
    '''
    Generate edges from pols
    obj: list as [[polygon, polygon,..], [polygon,...],...], being each polygon [int, int, ...].
    unique_edges: if False will return all polygon edges if True will remove the doubled edges
    '''
    out = []
    for faces in obj:
        out_edges = []
        seen = set()
        for face in faces:
            for edge in zip(face, list(face[1:]) + list([face[0]])):
                if unique_edges and tuple(sorted(edge)) in seen:
                    continue
                if unique_edges:
                    seen.add(tuple(sorted(edge)))
                out_edges.append(edge)
        out.append(out_edges)
    return out

def pols_sides(faces, sum_sides=False):
    '''
    returns the number of sides of each polygon as [int, int, ... ]
    faces: list as [polygon, polygon,..], being each polygon [int, int, ...].
    sum_sides: if True will return the sum of sides of the whole object returning [int]
    '''
    vals = [len(p) for p in faces]
    if sum_sides:
        vals = [sum(vals)]
    return vals

def pols_adjacent(pols):
    '''
    returns the polygons that share a vertex with each polygon [[pol, pol,..], [pol,..]]
    pols: list as [polygon, polygon,..], being each polygon [int, int, ...].
    '''
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
        for edge in eds:
            idx = edges.index(edge)
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
    '''
    returns the number polygons that share a vertex with each polygon [int, int,..]]
    pols: list as [polygon, polygon,..], being each polygon [int, int, ...].
    '''
    return [len(p) for p in pols_adjacent(pols)]

def pols_neighbor(verts, pols):
    '''
    returns the polygons that share one edges with each polygon [[pol, pol,..], [pol,..]]
    pols: list as [polygon, polygon,..], being each polygon [int, int, ...].
    '''
    v_adj = adjacent_edg_pol(verts, pols)
    vals = []
    for pol in pols:
        pol_adj = []
        for v_id in pol:
            for related_pol in v_adj[v_id]:
                if not related_pol in pol_adj:
                    pol_adj.append(related_pol)

        pol_adj.remove(pol)
        vals.append(pol_adj)

    return vals

def pols_neighbor_num(verts, pols):
    '''
    returns the number of polygons that share one edges with each polygon [int, int,...]
    pols: list as [polygon, polygon,..], being each polygon [int, int, ...].
    '''
    return [len(p) for p in pols_neighbor(verts, pols)]

def pols_normals(vertices, faces):
    '''
    Returns Faces normals as [vector, vector,...]
    vertices: list as [vertex, vertex, ...], being each vertex [float, float, float].
    faces: list as [polygon, polygon,..], being each polygon [int, int, ...].
    '''
    bm = bmesh_from_pydata(vertices, [], faces, normal_update=True)
    vals = [tuple(face.normal) for face in bm.faces]
    bm.free()
    return vals

def pols_absolute_normals(vertices, faces):
    '''
    Returns Faces center + faces normals as [vector, vector,...]
    vertices: list as [vertex, vertex, ...], being each vertex [float, float, float].
    faces: list as [polygon, polygon,..], being each polygon [int, int, ...].
    '''
    bm = bmesh_from_pydata(vertices, [], faces, normal_update=True)
    vals = [tuple(face.normal + face.calc_center_median()) for face in bm.faces]
    bm.free()
    return vals

def pols_shell_factor(vertices, faces):
    '''
    Average of vertex shell_factor
    vertices: list as [vertex, vertex, ...], being each vertex [float, float, float].
    edges: list as [edge, edge,..], being each edge [int, int].
    faces: list as [polygon, polygon,..], being each polygon [int, int, ...].
    returns vals as [float, float,...]
    '''
    v_shell = vertex_shell_factor(vertices, [], faces)
    vals = []
    for face in faces:
        p_shell = 0
        for v_id in face:
            p_shell += v_shell[v_id]
        vals.append(p_shell/len(face))

    return vals

def pols_center(vertices, faces, origin):
    '''
    Cemter of faces
    vertices: list as [vertex, vertex, ...], being each vertex [float, float, float].
    edges: list as [edge, edge,..], being each edge [int, int].
    faces: list as [polygon, polygon,..], being each polygon [int, int, ...].
    origin: String  that can be any key of pols_origin_modes_dict
    returns vals as [float, float,...]
    '''
    bm = bmesh_from_pydata(vertices, [], faces, normal_update=True)
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

def pols_perimeter(vertices, faces):
    '''
    returns pols perimeter.
    vertices: list as [vertex, vertex, ...], being each vertex [float, float, float].
    faces: list as [polygon, polygon,..], being each polygon [int, int, ...].
    '''
    bm = bmesh_from_pydata(vertices, [], faces, normal_update=True)
    vals = [bm_face.calc_perimeter() for bm_face in bm.faces]
    bm.free()
    return vals


def pols_tangent(vertices, faces, direction):
    '''
    returns pols tangents.
    vertices: list as [vertex, vertex, ...], being each vertex [float, float, float].
    faces: list as [polygon, polygon,..], being each polygon [int, int, ...].
    direction: String  that can be  any key of tangent_modes_dict
    '''
    bm = bmesh_from_pydata(vertices, [], faces, normal_update=True)
    vals = tangent_modes_dict[direction][1](bm.faces)
    bm.free()
    return vals

def pols_tangent_edge(bm_faces):
    return [tuple(bm_face.calc_tangent_edge()) for bm_face in bm_faces]

def pols_tangent_edge_diagonal(bm_faces):
    return [tuple(bm_face.calc_tangent_edge_diagonal()) for bm_face in bm_faces]

def pols_tangent_edge_pair(bm_faces):
    return [tuple(bm_face.calc_tangent_edge_pair()) for bm_face in bm_faces]

def pols_tangent_center_origin(bm_faces):
    return [tuple((Vector(bm_face.verts[0].co)-Vector(bm_face.calc_center_median())).normalized()) for bm_face in bm_faces]


def pols_tangent_vert_diagonal(bm_faces):
    return [tuple(bm_face.calc_tangent_vert_diagonal()) for bm_face in bm_faces]


def pols_is_boundary(vertices, faces):
    '''
    bridge to mesh filter node Faces class
    vertices: list as [vertex, vertex, ...], being each vertex [float, float, float].
    faces: list as [polygon, polygon,..], being each polygon [int, int, ...].
    '''
    bm = bmesh_from_pydata(vertices, [], faces, normal_update=True)
    interior, boundary, mask = Faces.process(bm, [], [])
    bm.free()
    return mask, interior, boundary


def pols_edges(faces):
    '''
    extracts the edges from polygons order [0, 1, 2] -> [[0, 1], [1, 2], [2, 0]]
    faces: list as [polygon, polygon,..], being each polygon [int, int, ...].
    '''
    vals = [[(c, cn) for c, cn in zip(face, face[1:] + [face[0]])] for face in faces]
    return vals

def pols_inverted(faces):
    '''
    inverts the polygon order [0, 1, 2] -> [2, 1, 0]
    faces: list as [polygon, polygon,..], being each polygon [int, int, ...].
    '''
    vals = [list(reversed(f)) for f in faces]
    return vals

def pols_matrix(vertices, faces, orientation):
    '''
    Matrix aligned with faces
    vertices: list as [vertex, vertex, ...], being each vertex [float, float, float].
    faces: list as [polygon, polygon,..], being each polygon [int, int, ...].
    orientation: contains origin and direction
    origin: String  that can be any key of pols_origin_modes_dict
    direction: String  that can be  any key of tangent_modes_dict
    outputs each polygon matrix [matrix, matrix, matrix]
    '''
    origin, direc = orientation
    bm = bmesh_from_pydata(vertices, [], faces, normal_update=True)
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
    'First Vertex':           (33, pols_first_vert, 'First Vertex of Face'),
    'Last Vertex':            (34, pols_last_vert, 'First Vertex of Face'),
    }

# Name: (index, input_sockets, func_options, output_options, function, output_sockets, output_sockets_names, description)
faces_modes_dict = {
    'Geometry':           (0,  'vp', '',   'u', pols_vertices,         'vs',  'Vertices, Faces', "Geometry of each face. (explode)"),
    'Center':             (10, 'vp', 'c',  '',  pols_center,           'v',   'Center', 'Center faces'),
    'Normal':             (20, 'vp', '',   '',  pols_normals,          'v',   'Normal', 'Normal of faces'),
    'Normal Absolute':    (21, 'vp', '',   '',  pols_absolute_normals, 'v',   'Normal_Abs', 'Median Center + Normal'),
    'Tangent':            (30, 'vp', 't',  '',  pols_tangent,          'v',   'Tangent', 'Face tangent.'),
    'Matrix':             (40, 'vp', 'qt', 'u', pols_matrix,           'm',   'Matrix', 'Matrix of face. Z axis on normal. X to first corner'),
    'Area':               (50, 'vp', 's',  '',  areas_from_polygons,   's',   'Area', "Area of faces"),
    'Perimeter':          (51, 'vp', 's',  '',  pols_perimeters,       's',   'Perimeter', 'Perimeter of faces'),
    'Sides Number':       (52, 'p',  's',  '',  pols_sides,            's',   'Sides', "Number of sides of faces"),
    'Adjacent Faces Num': (53, 'p',  '',   '',  pols_adjacent_num,     's',   'Number', "Number of Faces that share a edge with face"),
    'Neighbor Faces Num': (54, 'vp', '',   '',  pols_neighbor_num,     's',   'Number', "Number of Faces that share a vertex with face"),
    'Sharpness':          (55, 'vp', '',   '',  pols_shell_factor,     's',   'Sharpness ', 'Average of curvature of mesh in faces vertices'),
    'Inverse':            (60, 'p',  '',   '',  pols_inverted,         's',   'Faces', 'Reversed Polygons (Flipped)'),
    'Edges':              (61, 'p',  '',   'u', pols_edges,            's',   'Edges', 'Face Edges'),
    'Adjacent Faces':     (62, 'p',  '',   'u', pols_adjacent,         's',   'Faces', 'Faces that share a edge with face'),
    'Neighbor Faces':     (63, 'vp', '',   'u', pols_neighbor,         's',   'Faces', 'Faces that share a vertex with face'),
    'Is Boundary':        (70, 'vp', '',   '',  pols_is_boundary,      'sss', 'Mask, Boundary, Interior', 'Is the face boundary'),
    }
