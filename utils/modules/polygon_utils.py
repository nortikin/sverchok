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


def perimeters_from_polygons(verts, polygons):

    perimeters = []
    concat_perimeters = perimeters.append

    for polygon in polygons:
        perimeter = 0
        for v_id, v_id2 in zip(polygon, polygon[1:]+[polygon[0]]):
            perimeter += (Vector(verts[v_id]) - Vector(verts[v_id2])).magnitude
        concat_perimeters(perimeter)

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

def pols_center_bounds(vertices, edges, faces):
    bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)
    vals = [tuple(bm_face.calc_center_bounds()) for bm_face, face in zip(bm.faces, faces)]
    bm.free()
    return vals

def pols_center_median(vertices, edges, faces):
    bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)
    vals = [tuple(bm_face.calc_center_median()) for bm_face in bm.faces]
    bm.free()
    return vals

def pols_center_median_weighted(vertices, edges, faces):
    bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)
    vals = [tuple(bm_face.calc_center_median_weighted()) for bm_face, face in zip(bm.faces, faces)]
    bm.free()
    return vals

def pols_perimeter(vertices, edges, faces):
    bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)
    vals = [bm_face.calc_perimeter() for bm_face, face in zip(bm.faces, faces)]
    bm.free()
    return vals

def pols_tangent_edge(vertices, edges, faces):
    bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)
    vals = [tuple(bm_face.calc_tangent_edge()) for bm_face, face in zip(bm.faces, faces)]
    bm.free()
    return vals

def pols_tangent_edge_diagonal(vertices, edges, faces):
    bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)
    vals = [tuple(bm_face.calc_tangent_edge_diagonal()) for bm_face, face in zip(bm.faces, faces)]
    bm.free()
    return vals

def pols_tangent_edge_pair(vertices, edges, faces):
    bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)
    vals = [tuple(bm_face.calc_tangent_edge_pair()) for bm_face, face in zip(bm.faces, faces)]
    bm.free()
    return vals

def pols_tangent_vert_diagonal(vertices, edges, faces):
    bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)
    vals = [tuple(bm_face.calc_tangent_vert_diagonal()) for bm_face, face in zip(bm.faces, faces)]
    bm.free()
    return vals

def pols_edges(faces):
    vals = [[(c, cn) for c, cn in zip(face, face[1:]+[face[0]])] for face in faces]
    return vals

def pols_matrix_median_p0(vertices, edges, faces):
    bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)
    normals = [Vector(face.normal) for face in bm.faces]
    centers = [bm_face.calc_center_median() for bm_face in bm.faces]
    p0 = [vertices[face[0]] for face in faces]
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

faces_modes_dict = {
    "Vertices":               (200, 'vs', "u", 'vp',  pols_vertices, "Vertices Faces", "Vertices of faces"),
    "Area":                   (201, 's',  's', 'ves', areas_from_polygons, "Area", "Area of faces"),
    "Sides":                  (202, 's', 's',  'p',   pols_sides, "Sides", "Sides of faces"),
    'Perimeter':              (203, 's', '',   'vp',  perimeters_from_polygons, 'Perimeter', 'Perimeter of faces'),
    'Normal':                 (204, 'v', '',   'vep', pols_normals, 'Normal', 'Normal of faces'),
    'Normal Absolute':        (205, 'v', '',   'vep', pols_absolute_normals, 'Normal_Abs', 'Median Center + Normal'),
    'Center Bounds':          (208, 'v', '',   'vep', pols_center_bounds, 'Center', 'Center of bounding box of faces'),
    'Center Median':          (209, 'v', '',   'vep', pols_center_median, 'Center', 'Mean of vertices of each face'),
    'Center Median Weighted': (210, 'v', '',   'vep', pols_center_median_weighted, 'Center', 'Mean of vertices of each face weighted by edges length'),
    'Perimeter Bmesh':        (211, 's', '',   'vep', pols_perimeter, 'Perimeter Bmesh', 'Perimeter'),
    'Tangent edge':           (212, 'v', '',   'vep', pols_tangent_edge,          'Tangent', 'Face tangent based on longest edge.'),
    'Tangent edge diagonal':  (213, 'v', '',   'vep', pols_tangent_edge_diagonal, 'Tangent', 'Face tangent based on the edge farthest from any vertex'),
    'Tangent edge pair':      (214, 'v', '',   'vep', pols_tangent_edge_pair,     'Tangent', ' Face tangent based on the two longest disconnected edges'),
    'Tangent vert diagonal':  (215, 'v', '',   'vep', pols_tangent_vert_diagonal, 'Tangent', 'Face tangent based on the two most distent vertices'),
    'Edges':                  (216, 's', 'u',  'p',   pols_edges,                 'Edges', 'Face Edges'),
    'Matrix Median p0':       (217, 'm', 'u',  'vep', pols_matrix_median_p0,      'Matrix', 'Matrix in median center of face. Z axis on normal. X to frist corner'),
    'Matrix Median Align':    (218, 'm', 'u',  'vep', pols_matrix_median_align,   'Matrix', 'Matrix in median center of face. Z axis on normal. X aligned with frist edge'),
    'Matrix p0 Align':        (219, 'm', 'u',  'vep', pols_matrix_p0_align,       'Matrix', 'Matrix in frist corner of face. Z axis on normal. X aligned with frist edge'),

}
