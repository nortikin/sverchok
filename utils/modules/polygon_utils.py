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
from sverchok.utils.modules.matrix_utils import vectors_to_matrix
from sverchok.utils.modules.vertex_utils import vertex_shell_factor

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


def perimeters_from_polygons(verts, polygons, sum_perimeters=False):

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

def pols_sides(faces):
    vals = [len(p) for p in faces]
    return vals

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
    print(pols_origin_modes_dict[origin])
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
    vals = tangent_modes_dict[direction](bm.faces)
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


def pols_edges(faces):
    vals = [[(c, cn) for c, cn in zip(face, face[1:]+[face[0]])] for face in faces]
    return vals

def pols_inverted(vertices, faces):
    vals = [list(reversed(f)) for f in faces]
    return vals

def pols_matrix(vertices, edges, faces, orientation):
    direc, origin = orientation
    bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)
    normals = [Vector(face.normal) for face in bm.faces]

    centers = pols_origin_modes_dict[origin][1](bm.faces)
    centers = [Vector(v) for v in centers]
    tangents = [Vector(v) for v in tangent_modes_dict[direc](bm.faces)]
    p0 = [center + tang for center, tang in zip(centers, tangents)]

    vals = vectors_to_matrix(centers, normals, p0)
    bm.free()
    return vals

def pols_matrix_median_align(vertices, edges, faces):
    bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)
    normals = [Vector(face.normal) for face in bm.faces]
    centers = [bm_face.calc_center_median() for bm_face in bm.faces]
    p0 = [Vector(vertices[face[1]])-Vector(vertices[face[0]]) + center for face,center in zip(faces, centers)]
    vals = vectors_to_matrix(centers, normals, p0)
    bm.free()
    return vals

def pols_matrix_p0_align(vertices, edges, faces):
    bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)
    normals = [Vector(face.normal) for face in bm.faces]
    centers = [Vector(vertices[face[0]]) for face in faces]
    p0 = [Vector(vertices[face[1]]) for face in faces]
    vals = vectors_to_matrix(centers, normals, p0)
    bm.free()
    return vals

tangent_modes_dict ={
    'Edge':         pols_tangent_edge,
    'Edge Diagonal':  pols_tangent_edge_diagonal,
    'Edge Pair':  pols_tangent_edge_pair,
    'Vert Diagonal':  pols_tangent_vert_diagonal,
    'Center - Origin':  pols_tangent_center_origin,
    }
pols_origin_modes_dict = {
    'Bounds Center':          (30, pols_center_bounds, 'Center of bounding box of faces'),
    'Median Center':          (31, pols_center_median, 'Mean of vertices of each face'),
    'Median Weighted Center': (32, pols_center_median_weighted, 'Mean of vertices of each face weighted by edges length'),
    'First Vertex':    (33, pols_first_vert,  'Mean of vertices of each face weighted by edges length'),
    'Last Vertex':     (34, pols_last_vert, 'Mean of vertices of each face weighted by edges length'),

}
faces_modes_dict = {
    'Geometry':        (0,  'vs', 'u', 'vp',   pols_vertices,            "Vertices Faces", "Geometry of each face. (explode)"),
    'Area':            (1,  's',  's', 'vps',  areas_from_polygons,      "Area", "Area of faces"),
    'Sides Number':    (2,  's',  's', 'p',    pols_sides,               "Sides", "Sides of faces"),
    'Perimeter':       (3,  's',  '',  'vps',   perimeters_from_polygons, 'Perimeter', 'Perimeter of faces'),
    'Normal':          (10, 'v',  '',  'vep',  pols_normals,              'Normal', 'Normal of faces'),
    'Normal Absolute': (11, 'v',  '',  'vep',  pols_absolute_normals,     'Normal_Abs', 'Median Center + Normal'),
    'Inverse':         (15, 'v',  '',  'vp',   pols_inverted,             'Faces', 'Reversed Polygons (Flipped)'),
    'Sharpness':       (20, 's',  '',  'vep',  pols_shell_factor,         'Sharpness ', 'Average of curvature of mesh in faces vertices'),
    'Center':          (30, 'v',  '',  'vepc', pols_center,               'Center', 'Center faces'),
    'Tangent':         (40, 'v',  '',  'vept', pols_tangent,              'Tangent', 'Face tangent.'),
    'Edges':           (50, 's',  'u', 'p',    pols_edges,                'Edges', 'Face Edges'),
    'Matrix':          (60, 'm',  'u', 'vepm', pols_matrix,     'Matrix', 'Matrix of face. Z axis on normal. X to first corner'),

}
