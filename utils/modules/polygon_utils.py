# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


from mathutils import Vector
from mathutils.geometry import area_tri as area
from mathutils.geometry import tessellate_polygon as tessellate


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
        for v_id, v_id2 in zip(polygon,polygon[1:]+[polygon[0]]):
            perimeter += (Vector(verts[v_id]) - Vector(verts[v_id2])).magnitude
        concat_perimeters(perimeter)



    return perimeters
