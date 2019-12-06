# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import random

import bpy
from mathutils import Vector
from mathutils.geometry import tessellate_polygon, area_tri

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode


def get_points(sv_verts, faces, number, seed):
    """
    Return points distributed on given mesh
    :param sv_verts: list of vertices
    :param faces: list of faces
    :param number: int, number of points which should be putted on mesh
    :param seed: seed of random module
    :return: list of vertices, list of indexes for each generated point 
    which are point to a face where point was created
    """
    random.seed(seed)
    bl_verts = [Vector(co) for co in sv_verts]
    tri_faces, face_indexes = triangulate_mesh(bl_verts, faces)
    face_numbers = distribute_points(bl_verts, tri_faces, number)
    out_verts = []
    out_face_index = []
    for face, fi, fnum in zip(tri_faces, face_indexes, face_numbers):
        new_points = get_random_vectors_on_tri(*[bl_verts[face[i]] for i in range(3)], fnum)
        out_verts.extend(new_points)
        out_face_index.extend([fi for _ in range(len(new_points))])
    return [co[:] for co in out_verts], out_face_index


def distribute_points(bl_verts, tri_faces, number):
    # returns list of numbers which mean how many points should be created on face according its area
    face_areas = [area_tri(*[bl_verts[i] for i in f]) for f in tri_faces]
    total_area = sum(face_areas)
    face_numbers = [int(area * number / total_area) for area in face_areas]
    chosen_faces = random.choices(range(len(tri_faces)), face_areas, k=number-sum(face_numbers))
    for i in chosen_faces:
        face_numbers[i] += 1
    return face_numbers


def triangulate_mesh(bl_verts, faces):
    # returns list of triangle faces and list of indexes which points to initial faces for each new triangle
    new_faces = []
    face_indexes = []  # index of old faces
    for i, f in enumerate(faces):
        fverts = []  # list of list of vertices for tessellate algorithm
        iverts = []  # list of old index of point per new position of point
        # [[v1,v2,v3,v4]] - fverts
        # [0,1,4,3] - iverts
        fverts.append([bl_verts[i_f] for i_f in f])
        iverts.extend(f)
        for tri_f in tessellate_polygon(fverts):
            new_faces.append([iverts[itf] for itf in tri_f])
            face_indexes.append(i)
    return new_faces, face_indexes


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
    bl_icon = 'SNAP_FACE_CENTER'

    points_number: bpy.props.IntProperty(name='Number', default=10, description="Number of random points",
                                         update=updateNode)
    seed: bpy.props.IntProperty(name='Seed', update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Verts')
        self.inputs.new('SvStringsSocket', 'Faces')
        self.inputs.new('SvStringsSocket', 'Number').prop_name = 'points_number'
        self.inputs.new('SvStringsSocket', 'Seed').prop_name = 'seed'
        self.outputs.new('SvVerticesSocket', 'Verts')
        self.outputs.new('SvStringsSocket', 'Face index')

    def process(self):
        if not all([self.inputs['Verts'].is_linked, self.inputs['Faces'].is_linked]):
            return
        out_verts = []
        out_face_index = []
        for v, f, n, s in zip(self.inputs['Verts'].sv_get(), self.inputs['Faces'].sv_get(),
                              self.inputs['Number'].sv_get(), self.inputs['Seed'].sv_get()):
            new_vertices, face_index = get_points(v, f, n[0], s[0])
            out_verts.append(new_vertices)
            out_face_index.append(face_index)
        self.outputs['Verts'].sv_set(out_verts)
        self.outputs['Face index'].sv_set(out_face_index)


def register():
    bpy.utils.register_class(SvRandomPointsOnMesh)


def unregister():
    bpy.utils.unregister_class(SvRandomPointsOnMesh)
