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

import bpy
import mathutils

from mathutils import Vector
from bpy.props import FloatProperty, FloatVectorProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (
    updateNode, Vector_generate,
    repeat_last, fullList)


''' very non optimal routines. beware. I know this '''


def inset_special(vertices, faces, inset_rates, axis, distances, make_inner):

    new_faces = []

    def get_average_vector(verts, n):
        dummy_vec = Vector()
        for v in verts:
            dummy_vec = dummy_vec + v
        return dummy_vec * 1/n

    def do_tri(face, lv_idx, make_inner):
        a, b, c = face
        d, e, f = lv_idx-2, lv_idx-1, lv_idx
        out_faces = []
        out_faces.append([a, b, e, d])
        out_faces.append([b, c, f, e])
        out_faces.append([c, a, d, f])
        if make_inner:
            out_faces.append([d, e, f])
        return out_faces

    def do_quad(face, lv_idx, make_inner):
        a, b, c, d = face
        e, f, g, h = lv_idx-3, lv_idx-2, lv_idx-1, lv_idx
        out_faces = []
        out_faces.append([a, b, f, e])
        out_faces.append([b, c, g, f])
        out_faces.append([c, d, h, g])
        out_faces.append([d, a, e, h])
        if make_inner:
            out_faces.append([e, f, g, h])
        return out_faces

    def do_ngon(face, lv_idx, make_inner):
        '''
        setting up the forloop only makes sense for ngons
        idx0, idx1, last_vertex_idx-(n-1), last_vertex_idx-n
        idx1, idxn, last_vertex_idx-(n-2), last_vertex_idx-(n-1)
        .. ,.. ,.. ,..
        idxn, idx0, last_vertex_idx-n, last_vertex_idx-(n-2)

        '''
        print('ngons are not yet supported')
        return []

    def new_inner_from(face, inset_by, axis, distance, make_inner):
        '''
        face:       (idx list) face to work on
        inset_by:   (scalar) amount to open the face
        axis:       (vector) axis relative to face normal
        distance:   (scalar) push new verts on axis by this amount
        make_inner: create extra internal face

        # dumb implementation first. should only loop over the verts of face 1 time
        to get
         - new faces
         - avg vertex location
         - but can't lerp until avg is known. so each input face is looped at least twice.
        '''
        current_verts_idx = len(vertices)
        n = len(face)
        verts = [vertices[i] for i in face]
        avg_vec = get_average_vector(verts, n)

        # lerp and add to vertices immediately
        new_verts_prime = [avg_vec.lerp(v, inset_by) for v in verts]

        if distance:
            local_normal = mathutils.geometry.normal(*new_verts_prime[:3])
            if axis:
                local_normal = (avg_vec + local_normal + Vector(axis)).normalized()

            new_verts_prime = [v.lerp(v+local_normal, distance) for v in new_verts_prime]

        vertices.extend(new_verts_prime)

        tail_idx = (current_verts_idx + n) - 1

        get_faces_prime = {3: do_tri, 4: do_quad}.get(n, do_ngon)
        new_faces_prime = get_faces_prime(face, tail_idx, make_inner)
        new_faces.extend(new_faces_prime)

    for idx, face in enumerate(faces):
        inset_by = inset_rates[idx][0]  # WARNING, levels issue
        if inset_by > 0:

            push_by = distances[idx][0]  # WARNING, levels issue
            # if axis:
            #     axial = axis[idx][0]

            #     # print(axial)
            #     if (axial[0] == axial[1] == axial[2]) == 0.0:
            #         axial = None
            # else:
            #     axial = None

            # print(axial)
            axial = None

            # axial = (random.random(),random.random(), 0.0)
            new_inner_from(face, inset_by, axial, push_by, make_inner)

    new_verts = [v[:] for v in vertices]
    # print('new_faces=', new_faces)
    return new_verts, new_faces


class SvInsetSpecial(bpy.types.Node, SverchCustomTreeNode):
    '''
    Insets geometry, optional remove and/or translate
    Don't think of this as a realtime effect.
    '''

    bl_idname = 'SvInsetSpecial'
    bl_label = 'Inset Special'
    bl_icon = 'OUTLINER_OB_EMPTY'

    inset = FloatProperty(
        name='Inset',
        description='inset amount',
        default=0.1, update=updateNode)
    distance = FloatProperty(
        name='Distance',
        description='Distance',
        default=0.0, update=updateNode)

    # axis = FloatVectorProperty(
    #   name='axis', description='axis relative to normal',
    #   default=(0,0,1), update=updateNode)

    def init(self, context):

        self.inputs.new('StringsSocket', 'inset').prop_name = 'inset'
        self.inputs.new('StringsSocket', 'distance').prop_name = 'distance'
        # self.inputs.new('VerticesSocket', 'axis').prop_name = 'axis'
        self.inputs.new('VerticesSocket', 'vertices', 'vertices')
        self.inputs.new('StringsSocket', 'polygons', 'polygons')

        self.outputs.new('VerticesSocket', 'vertices', 'vertices')
        self.outputs.new('StringsSocket', 'polygons', 'polygons')

    def get_value_for(self, param, fallback):
        return self.inputs[param].sv_get() if self.inputs[param].links else fallback

    def process(self):
        i = self.inputs
        o = self.outputs

        if not o['vertices'].is_linked:
            return

        verts = Vector_generate(i['vertices'].sv_get())
        polys = i['polygons'].sv_get()

        ''' get_value_for( param name, fallback )'''
        inset_rates = self.get_value_for('inset', [[self.inset]])
        distance_vals = self.get_value_for('distance', [[self.distance]])

        #if self.inputs['axis'].links:
        #    axees = self.get_value_for('axis', [[self.axis]])
        #else:
        #    axees = None

        # print(inset_rates)
        # unvectorized implementation, expects only one set of verts + faces + etc
        fullList(inset_rates, len(polys[0]))
        fullList(distance_vals, len(polys[0]))
        #fullList(axees, len(polys[0]))

        #verts, faces, axis=None, distance=0, make_inner=False
        verts_out = []
        polys_out = []

        func_args = {
            'vertices': verts[0],
            'faces': polys[0],
            'inset_rates': inset_rates,
            'axis': None,
            'distances': distance_vals,
            'make_inner': False
        }

        res = inset_special(**func_args)

        if not res:
            return

        verts_out, polys_out = res

        # deal  with hooking up the processed data to the outputs
        o['vertices'].sv_set([verts_out])

        if o['polygons'].is_linked:
            o['polygons'].sv_set([polys_out])


def register():
    bpy.utils.register_class(SvInsetSpecial)


def unregister():
    bpy.utils.unregister_class(SvInsetSpecial)
