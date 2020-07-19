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

import random
import numpy as np
from numba import njit

import bpy
import mathutils

# from mathutils import Vector
from bpy.props import FloatProperty, FloatVectorProperty, IntProperty, EnumProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (
    updateNode, Vector_generate,
    repeat_last, fullList)



@njit
def get_normal_of_3points(p1, p2, p3):
    return [
        ((p2[1]-p1[1])*(p3[2]-p1[2]))-((p2[2]-p1[2])*(p3[1]-p1[1])),
        ((p2[2]-p1[2])*(p3[0]-p1[0]))-((p2[0]-p1[0])*(p3[2]-p1[2])),
        ((p2[0]-p1[0])*(p3[1]-p1[1]))-((p2[1]-p1[1])*(p3[0]-p1[0]))
    ]        

@njit
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
    points = verts.reshape((3, -1))
    if points.shape[0] == 4:
        return get_normal_of_3points(points[0], points[1], points[3])
    
    # standard and fallback
    return get_normal_of_3points(points[0], points[1], points[2])

@njit
def np_lerp_v3_v3v3(a, b, t):
    """
    excepts: 2 arrays (maybe np) of 3 floats
    returns: returns single array with the linear interpolation between a and b by the ratio of t. 
    info: t can be between 0 and 1 (float) but can also be outside of that range for extrapolation.
    """
    s = 1.0 - t
    return [s * a[0] + t * b[0], s * a[1] + t * b[1], s * a[2] + t * b[2]]

@njit
def np_sum_v3_v3v3(a, b):
    """
    expects: 2 input arrays of 3 floats each.
    returns: 1 output np.array of 3 floats that represents the summation of a and b
    """
    return np.array((a[0]+b[0], a[1]+b[1], a[2]+b[2]), dtype=np.float32)


@njit
def get_average_vector(verts_array):
    """
    expects: flat np.array of float32
    returns: np.array shape (3, 1)
    """
    return verts_array.reshape((3,-1)).mean(axis=0)

@njit
def do_tri(face, lv_idx, make_inner):
    a, b, c = face
    d, e, f = lv_idx-2, lv_idx-1, lv_idx
    out_faces = [
        [a, b, e, d],
        [b, c, f, e],
        [c, a, d, f]
    ]
    if make_inner:
        out_faces.append([d, e, f])
    return out_faces

@njit
def do_quad(face, lv_idx, make_inner):
    a, b, c, d = face
    e, f, g, h = lv_idx-3, lv_idx-2, lv_idx-1, lv_idx
    out_faces = [
        [a, b, f, e],
        [b, c, g, f],
        [c, d, h, g],
        [d, a, e, h]
    ]
    if make_inner:
        out_faces.append([e, f, g, h])
    return out_faces

@njit
def do_ngon(face, lv_idx, make_inner):
    '''
    setting up the forloop only makes sense for ngons
    '''
    num_elements = len(face)
    face_elements = list(face)
    inner_elements = [lv_idx-n for n in range(num_elements-1, -1, -1)]
    # padding, wrap-around
    face_elements.append(face_elements[0])
    inner_elements.append(inner_elements[0])

    out_faces = []
    add_face = out_faces.append
    for j in range(num_elements):
        add_face([face_elements[j], face_elements[j+1], inner_elements[j+1], inner_elements[j]])

    if make_inner:
        temp_face = [idx[-1] for idx in out_faces]
        add_face(temp_face)
    
    return out_faces

@njit
def inset_special(vertices, faces, inset_rates, distances, ignores, make_inners, zero_mode="SKIP"):

    new_faces = []
    new_ignores = []
    new_insets = []

    # calculate new size of output vertices ------------------- TODO
    # value_to_add_shape = 0
    # for ignore, face in zip(ignores, faces): 
    #    if not ignore:
    #        value_to_add_shape += len(face)

    def new_inner_from(face, inset_by, distance, make_inner):
        '''
        face:       (idx list) face to work on
        inset_by:   (scalar) amount to open the face
        distance:   (scalar) push new verts on normal by this amount
        make_inner: create or drop internal face

        # dumb implementation first. should only loop over the verts of face 1 time
        to get
         - new faces
         - avg vertex location
         - but can't lerp until avg is known. so each input face is looped at least twice.
        '''
        current_verts_idx = len(vertices)
        
        n = len(face)
        verts = np.array([vertices[i] for i in face], dtype=np.float32)
        avg_vec = get_average_vector(verts.ravel())

        if abs(inset_by) < 1e-6:
            
            # right now this expects only convex shapes, do not expect concave input or colinear quads that look like tris
            # to handle correctly. See implementation where to fix this.
            normal = get_normal_of_polygon(verts.ravel())
            
            new_vertex = avg_vec.lerp(avg_vec + normal, distance)   # ------------------TODO
            vertices.append(new_vertex)
            new_vertex_idx = current_verts_idx
            new_faces
            for i, j in zip(face, face[1:]):
                new_faces.append([i, j, new_vertex_idx])
            new_faces.append([face[-1], face[0], new_vertex_idx])
            return

        # lerp and add to vertices immediately
        new_verts_prime = [avg_vec.lerp(v, inset_by) for v in verts]    # ------------------TODO

        if distance:
            local_normal = get_normal_of_polygon(...*new_verts_prime)   # ------------------TODO
            new_verts_prime = [v.lerp(v+local_normal, distance) for v in new_verts_prime]    # ------------------TODO

        vertices.extend(new_verts_prime)
        tail_idx = (current_verts_idx + n) - 1
        get_faces_prime = {3: do_tri, 4: do_quad}.get(n, do_ngon)
        new_faces_prime = get_faces_prime(face, tail_idx, make_inner)
        
        if make_inner:
            new_insets.append(new_faces_prime[-1])

        new_faces.extend(new_faces_prime)

    # end

    for idx, face in enumerate(faces):
        inset_by = inset_rates[idx]

        good_inset = (inset_by > 0) or (zero_mode == 'FAN')
        if good_inset and (not ignores[idx]):
            new_inner_from(face, inset_by, distances[idx], make_inners[idx])
        else:
            new_faces.append(face)
            new_ignores.append(face)

    return vertices, new_faces, new_ignores, new_insets


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

    # unused property.
    normal_modes = [
            ("Fast", "Fast", "Fast algorithm", 0),
            ("Exact", "Exact", "Slower, but exact algorithm", 1)
        ]

    inset : FloatProperty(
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

    # unused property.
    normal_mode : EnumProperty(name = "Normals",
            description = "Normals calculation algorithm",
            default = "Exact",
            items = normal_modes,
            update = updateNode)

    zero_modes = [
            ("SKIP", "Skip", "Do not process such faces", 0),
            ("FAN", "Fan", "Make a fan-like structure from such faces", 1)
        ]

    zero_mode : EnumProperty(name = "Zero inset faces",
            description = "What to do with faces when inset is equal to zero",
            default = "SKIP",
            items = zero_modes,
            update = updateNode)

    # axis = FloatVectorProperty(
    #   name='axis', description='axis relative to normal',
    #   default=(0,0,1), update=updateNode)

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
        o.new('SvStringsSocket', 'ignored')
        o.new('SvStringsSocket', 'inset')

    def draw_buttons_ext(self, context, layout):
        # layout.prop(self, "normal_mode")
        layout.prop(self, "zero_mode")

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
        ignored_out = []
        inset_out = []

        for v, p, inset_rates, distance_vals, ignores, make_inners in zip(*data):
            fullList(inset_rates, len(p))
            fullList(distance_vals, len(p))
            fullList(ignores, len(p))
            fullList(make_inners, len(p))

            func_args = {
                'vertices': v,
                'faces': p,
                'inset_rates': inset_rates,
                'distances': distance_vals,
                'make_inners': make_inners,
                'ignores': ignores,
                'zero_mode': self.zero_mode
            }

            res = inset_special(**func_args)

            if not res:
                res = v, p, [], []

            verts_out.append(res[0])
            polys_out.append(res[1])
            ignored_out.append(res[2])
            inset_out.append(res[3])

        # deal  with hooking up the processed data to the outputs
        o['vertices'].sv_set(verts_out)
        o['polygons'].sv_set(polys_out)
        o['ignored'].sv_set(ignored_out)
        o['inset'].sv_set(inset_out)



def register():
    bpy.utils.register_class(SvInsetSpecialMK2)


def unregister():
    bpy.utils.unregister_class(SvInsetSpecialMK2)
