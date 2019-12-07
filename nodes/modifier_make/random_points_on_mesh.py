# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import random
from itertools import cycle, chain, repeat

import bpy
from mathutils import Vector
from mathutils.geometry import tessellate_polygon, area_tri

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode


def get_points(sv_verts, faces, number, seed, face_weight=None):
    """
    Return points distributed on given mesh
    :param sv_verts: list of vertices
    :param faces: list of faces
    :param number: int, number of points which should be putted on mesh
    :param seed: seed of random module
    :param face_weight: weights of inputs faces, float or int, if None then all faces have 1 weight
    :return: list of vertices, list of indexes for each generated point 
    which are point to a face where point was created
    """
    random.seed(seed)
    bl_verts = [Vector(co) for co in sv_verts]
    tri_faces, face_indexes, tri_weights = triangulate_mesh(bl_verts, faces, face_weight)
    if not tri_faces:
        return [[]], []
    face_numbers = distribute_points_accurate(bl_verts, tri_faces, number, tri_weights)
    out_verts = []
    out_face_index = []
    for face, fi, fnum in zip(tri_faces, face_indexes, face_numbers):
        new_points = get_random_vectors_on_tri(*[bl_verts[face[i]] for i in range(3)], fnum)
        out_verts.extend(new_points)
        out_face_index.extend([fi for _ in range(len(new_points))])
    return [co[:] for co in out_verts], out_face_index


def distribute_points_fast(bl_verts, tri_faces, number):
    # returns list of numbers which mean how many points should be created on face according its area
    # actually this function has much better performance but for whole algorithm it does not matter
    # leave this function unused
    face_areas = [area_tri(*[bl_verts[i] for i in f]) for f in tri_faces]
    total_area = sum(face_areas)
    face_numbers = [int(area * number / total_area) for area in face_areas]
    chosen_faces = random.choices(range(len(tri_faces)), face_areas, k=number-sum(face_numbers))
    for i in chosen_faces:
        face_numbers[i] += 1
    return face_numbers


def distribute_points_accurate(bl_verts, tri_faces, number, tri_weights):
    # returns list of numbers which mean how many points should be created on face according its area
    weighed_face_areas = [area_tri(*[bl_verts[i] for i in f]) * w for f, w in zip(tri_faces, tri_weights)]
    face_numbers = [0 for _ in tri_faces]
    chosen_faces = random.choices(range(len(tri_faces)), weighed_face_areas, k=number)
    for i in chosen_faces:
        face_numbers[i] += 1
    return face_numbers


def triangulate_mesh(bl_verts, faces, face_weight=None):
    # returns list of triangle faces and list of indexes which points to initial faces for each new triangle
    new_faces = []
    face_indexes = []  # index of old faces
    new_face_weight = []
    iter_weight = cycle([1]) if face_weight is None else chain(face_weight, cycle([face_weight[-1]]))
    for i, (f, w) in enumerate(zip(faces, iter_weight)):
        fverts = []  # list of list of vertices for tessellate algorithm
        iverts = []  # list of old index of point per new position of point
        # [[v1,v2,v3,v4]] - fverts
        # [0,1,4,3] - iverts
        fverts.append([bl_verts[i_f] for i_f in f])
        iverts.extend(f)
        for tri_f in tessellate_polygon(fverts):
            new_faces.append([iverts[itf] for itf in tri_f])
            face_indexes.append(i)
            new_face_weight.append(w if w >= 0 else 0)
    return new_faces, face_indexes, new_face_weight


def get_random_vectors_on_tri(v1, v2, v3, number):
    # returns random vertices for given triangle
    out = []
    for _ in range(number):
        u1 = random.random()
        u2 = random.random()
        u1 = u1 if u1 + u2 <= 1 else 1 - u1
        u2 = u2 if u1 + u2 <= 1 else 1 - u2
        side1 = v2 - v1
        side2 = v3 - v1
        out.append(v1 + side1 * u1 + side2 * u2)
    return out


class SvRandomPointsOnMesh(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: distribute points on given mesh
    points are created evenly according area faces

    based on Blender function - tessellate_polygon
    """
    bl_idname = 'SvRandomPointsOnMesh'
    bl_label = 'Random points on mesh'
    sv_icon = 'SV_RANDOM_NUM_GEN'

    points_number: bpy.props.IntProperty(name='Number', default=10, description="Number of random points",
                                         update=updateNode)
    seed: bpy.props.IntProperty(name='Seed', update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Verts')
        self.inputs.new('SvStringsSocket', 'Faces')
        self.inputs.new('SvStringsSocket', 'Face weight')
        self.inputs.new('SvStringsSocket', 'Number').prop_name = 'points_number'
        self.inputs.new('SvStringsSocket', 'Seed').prop_name = 'seed'
        self.outputs.new('SvVerticesSocket', 'Verts')
        self.outputs.new('SvStringsSocket', 'Face index')

    def process(self):
        if not all([self.inputs['Verts'].is_linked, self.inputs['Faces'].is_linked]):
            return
        out_verts = []
        out_face_index = []
        for v, f, n, s, w in zip(self.inputs['Verts'].sv_get(), self.inputs['Faces'].sv_get(),
                         self.inputs['Number'].sv_get(), self.inputs['Seed'].sv_get(),
                         self.inputs['Face weight'].sv_get() if self.inputs['Face weight'].is_linked else cycle([[1]])):
            new_vertices, face_index = get_points(v, f, n[0], s[0], w)
            out_verts.append(new_vertices)
            out_face_index.append(face_index)
        self.outputs['Verts'].sv_set(out_verts)
        self.outputs['Face index'].sv_set(out_face_index)


def register():
    bpy.utils.register_class(SvRandomPointsOnMesh)


def unregister():
    bpy.utils.unregister_class(SvRandomPointsOnMesh)
