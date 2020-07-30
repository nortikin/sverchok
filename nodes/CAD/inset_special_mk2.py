# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

# pylint: disable=c0301
# pylint: disable=c0103

import math
import random
import numpy as np
from numba import njit
import itertools

import bpy
import mathutils

# from mathutils import Vector
from bpy.props import FloatProperty, FloatVectorProperty, IntProperty, EnumProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (
    updateNode, Vector_generate,
    repeat_last, fullList)


def np_restructure_indices(faces):
    flat_faces = list(itertools.chain.from_iterable(faces))
    return np.array(flat_faces, dtype=np.int32), [len(f) for f in faces]
    

def np_length_v3(v):
    """
    gives you the length of the 3-element-vector
    
    input: vector-like
    output: scalar length
    """
    return math.sqrt((v[0] * v[0]) + (v[1] * v[1]) + (v[2] * v[2]))


def np_normalize_v3(v):
    """
    rescales the input (3-element-vector), so that the length of the vector "extents" is One.
    this doesn't change the direction of the vector, only the magnitude.
    """
    l = math.sqrt((v[0] * v[0]) + (v[1] * v[1]) + (v[2] * v[2]))
    return [v[0]/l, v[1]/l, v[2]/l]


def get_normal_of_3points(p1, p2, p3):
    """
    accepts: 3 input vectors
    returns: the direction of a face composed by the input vectors p1,2,3. The order of these vectors is important
             - the output normal is not automatically normalized to unit length. (maybe it should be)
    """
    return [
        ((p2[1]-p1[1])*(p3[2]-p1[2]))-((p2[2]-p1[2])*(p3[1]-p1[1])),
        ((p2[2]-p1[2])*(p3[0]-p1[0]))-((p2[0]-p1[0])*(p3[2]-p1[2])),
        ((p2[0]-p1[0])*(p3[1]-p1[1]))-((p2[1]-p1[1])*(p3[0]-p1[0]))
    ]        


def get_normal_of_polygon(verts):
    """
    expects: a flat array of verts.
    returns: the normal of that sequence, via a set of tests that determin how to calculate the normal
    - the most straight forward algorithm expects the number of verts to be three
    - with 4 verts, the assumption right now is: 
        1. the verts are convex
        2. if there are colinear edges, then a correct result will not be automatic, it will depend on
           on how we simplify the quad to a triangle. (0, 1, 3) strategy works
    - with ngons, a convex polygon will return correct normal, but any concave ngon will require tessellation
        note: tessellation is conceptually trivial, but not entirely trivial to implement 
.
    """
    points = verts.reshape((-1, 3))
    if points.shape[0] == 4:
        return get_normal_of_3points(points[0], points[1], points[3])
    
    # standard and fallback
    return get_normal_of_3points(points[0], points[1], points[2])


def np_lerp_v3_v3v3(a, b, t):
    """
    expects: 2 flat arrays of len=3 (maybe np) of 3 floats
    returns: returns single array with the linear interpolation between a and b by the ratio of t. 
    info: t can be between 0 and 1 (float) but can also be outside of that range for extrapolation.
    """
    s = 1.0 - t
    return [s * a[0] + t * b[0], s * a[1] + t * b[1], s * a[2] + t * b[2]]


def make_new_indices(offset, flat_face_indices, generate_inner):
    """
    non dependant on geometry, purely an indexing operation.
    does depend on current count of new verts, this is matched by passing the offset. 
    """
    new_faces = []
    for i in range(len(flat_face_indices)-1):
        new_faces.extend([flat_face_indices[i], flat_face_indices[i+1], offset + 1 + i, offset + i]) 
    
    new_faces.extend([flat_face_indices[-1], flat_face_indices[0], offset, offset + len(flat_face_indices) - 1])

    if generate_inner:
        new_faces.extend(list(range(offset, offset + len(flat_face_indices))))
    
    return new_faces


def move_verts(avg, flat_verts, i_distance, i_relative):
    """
    input is affected differently depending on whether inset should be relative or not.
    returns the flat new vertex ring
    """
    new_flat_verts = np.zeros(flat_verts.shape[0]).reshape((-1, 3))
    for idx, v in enumerate(flat_verts.reshape((-1, 3))):

        if i_relative == 0:
            direction = np_normalize_v3(avg - v)
            offset = direction * i_distance
        else:
            offset = np_lerp_v3_v3v3(v, avg, i_distance)
        
        new_flat_verts[idx] = offset

    return flat_verts + new_flat_verts.ravel()


def make_new_verts(flat_verts_for_face, i_distance, p_distance, EPSILON, inset_relative):
    """
    get average location
    get face normal
    """
    if abs(i_distance) <= EPSILON:
        # dont inset, just reuse existing locations
        new_flat_verts = flat_verts_for_face
    else:
        # adjust new verts according to i_distance
        avg_location = flat_verts_for_face.reshape((-1, 3)).mean(axis=0)
        new_flat_verts = move_verts(avg_location, flat_verts_for_face, i_distance, inset_relative)

    if abs(p_distance) <= EPSILON:
        pass
    else:
        # get approximate verts normal, resize to make offset, add to new_flat_verts
        face_normal = get_normal_of_polygon(flat_verts_for_face)
        face_normal = np_normalize_v3(face_normal)
        offset_vector = face_normal * p_distance
        new_flat_verts = (new_flat_verts.reshape((-1, 3)) + np.array(offset_vector)).ravel()

    return new_flat_verts
    
def fast_inset(
    original_verts_list,            # a flat list or vector coordinates 
    original_face_indices_list,     # a flat list of all face indices
    original_face_lengths_list,     # a flat list of the lengths of all incoming polygons
    skip_list,                      # a list used to determin if we can skip a polygon, keep unchanged
    inset_by_distance_list,         # each original polygonis is inset by this, and generates a new v-ring
    push_by_distance_list,          # push each newly generated v-ring away from original polygon normal 
    generate_inner_face_list,       # decide if the new ring gets a new face.
    inset_relative,                 # 0 = absolute, 1 = relative
    ):

    """
    v-ring is a vertex ring.
    inset_relative, can be 0=absolute or 1=relative.
        in absolute mode inset_distance will extend in real world units towards the average vector of the original face
        in relative mode inset of 0.5 is halfway between original face's vector to the average. 1 is exactly in the average   
    output:
       flat verts | flat face_indices | flat start_end_loops | flat mask new inners
    """
    EPSILON = 1.0E-6
    original_verts_list = original_verts_list.reshape((-1, 3)) 
    num_original_verts = original_verts_list.shape[0]

    idx_offset = 0
    lengths_new_faces = []
    new_flat_face_indices = []
    new_verts = []
    new_inner_masks = []

    for idx, skip in skip_list:
        if skip:
            new_inner_masks.append(0)
            continue    

        len_cur_face = original_face_lengths_list[idx]
        generate_inner = generate_inner_face_list[idx]
        if generate_inner:
            lengths_new_faces.extend(([4,] * len_cur_face) + [len_cur_face])
            new_inner_masks.extend(([0,] * len_cur_face) + [1])
        else:
            lengths_new_faces.extend(([4,] * len_cur_face))
            new_inner_masks.extend(([0,] * len_cur_face))

        flat_face_indices = original_face_indices_list[idx_offset: idx_offset + len_cur_face]
        new_flat_face_indices.extend(make_new_indices(num_original_verts + idx_offset, flat_face_indices, generate_inner))
        flat_verts_for_face = np.take(original_verts_list, flat_face_indices, axis=0).ravel()
        new_verts.extend(make_new_verts(flat_verts_for_face, inset_by_distance_list[idx], push_by_distance_list[idx], EPSILON, inset_relative))
        idx_offset += len_cur_face

    # [ ] add new verts to original_vertex_list
    # [ ] add new face indices to original_face_indices_list
    # [ ] add new face lengths to original_face_length_list
    # [ ] add face mask to output inners.

    # output vertes, polygons, inset_mask
    ...


class SvInsetSpecialMK2(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: inset spec mk2
    Tooltip: Insets geometry, optional remove inset

    this is an attempt to use numba and numpy for these calculations
    
    """

    bl_idname = 'SvInsetSpecialMK2'
    bl_label = 'Inset Special +'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_INSET'

    inset: FloatProperty(
        name='Inset',
        description='inset amount',
        min = 0.0,
        default=0.1, update=updateNode)
    distance: FloatProperty(
        name='Distance',
        description='Distance',
        default=0.0, update=updateNode)

    ignore: IntProperty(name='Ignore', description='skip polygons', default=0, update=updateNode)
    make_inner: IntProperty(name='Make Inner', description='Make inner polygon', default=1, update=updateNode)

    inset_relative_modes = [
        ("ABSOLUTE", "ABSOLUTE", "Use world distance values to lerp towards the middle", 0)
        ("RELATIVE", "RELATIVE", "Use ratio between midpolygon and vertices of polygon", 1),
    ]

    inset_relative_mode : EnumProperty(
        name="Inset relative modes",
        description="What to do with the inset value, relative or absolute world units",
        default="ABSOLUTE",
        items=inset_relative_modes,
        update=updateNode)

    replacement_nodes = [
        ('SvExtrudeSeparateNode',
            dict(vertices='Vertices', polygons='Polygons'),
            dict(vertices='Vertices', polygons='Polygons')),
        ('SvExtrudeSeparateLiteNode',
            dict(vertices='Vertices', polygons='Polygons'),
            dict(vertices='Vertices', polygons='Polygons')),
        ('SvInsetFaces',
            dict(vertices='Verts', polygons='Faces'),
            dict(vertices='Verts', polygons='Faces'))
    ]

    def sv_init(self, context):
        i = self.inputs
        i.new('SvStringsSocket', 'inset').prop_name = 'inset'
        i.new('SvStringsSocket', 'distance').prop_name = 'distance'
        i.new('SvVerticesSocket', 'vertices')
        i.new('SvStringsSocket', 'polygons')
        i.new('SvStringsSocket', 'ignore').prop_name = 'ignore'
        i.new('SvStringsSocket', 'make_inner').prop_name = 'make_inner'

        o = self.outputs
        o.new('SvVerticesSocket', 'vertices')
        o.new('SvStringsSocket', 'polygons')
        o.new('SvStringsSocket', 'inset')

    def draw_buttons_ext(self, context, layout):
        # layout.prop(self, "normal_mode")
        layout.prop(self, "inset_relative_mode", expand=True)

    def process(self):
        i = self.inputs
        o = self.outputs

        if not o['vertices'].is_linked:
            return

        all_verts = i['vertices'].sv_get()
        all_polys = i['polygons'].sv_get()
        all_inset_rates = i['inset'].sv_get()
        all_distance_vals = i['distance'].sv_get()
        all_ignores = i['ignore'].sv_get()
        all_make_inners = i['make_inner'].sv_get()

        data = all_verts, all_polys, all_inset_rates, all_distance_vals, all_ignores, all_make_inners

        verts_out = []
        polys_out = []
        inset_out = []

        for v, p, inset_rates, distance_vals, ignores, make_inners in zip(*data):
            fullList(inset_rates, len(p))
            fullList(distance_vals, len(p))
            fullList(ignores, len(p))
            fullList(make_inners, len(p))

            original_face_indices_list, original_face_lengths_list = np_restructure_indices(p)

            res = fast_inset(
                np.array(v).ravel(),            # original_verts_list      | a flat list or vector coordinates 
                original_face_indices_list,     #                  -       | a flat list of all face indices
                original_face_lengths_list,     #                  -       | a flat list of the lengths of all incoming polygons
                ignores,                        # skip_list                | a list used to determin if we can skip a polygon, keep unchanged
                inset_rates,                    # inset_by_distance_list   | each original polygonis is inset by this, and generates a new v-ring
                distance_vals,                  # push_by_distance_list    | push each newly generated v-ring away from original polygon normal 
                make_inners,                    # generate_inner_face_list | decide if the new ring gets a new face.
                self.inset_relative_mode        #                          | 0 = absolute, 1 = relative
            )

            if not res:
                res = v, p, [], []

            verts_out.append(res[0])
            polys_out.append(res[1])
            inset_out.append(res[3])

        # deal  with hooking up the processed data to the outputs
        o['vertices'].sv_set(verts_out)
        o['polygons'].sv_set(polys_out)
        o['inset'].sv_set(inset_out)



def register():
    bpy.utils.register_class(SvInsetSpecialMK2)


def unregister():
    bpy.utils.unregister_class(SvInsetSpecialMK2)
