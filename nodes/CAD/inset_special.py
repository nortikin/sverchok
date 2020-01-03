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
from bpy.props import FloatProperty, FloatVectorProperty, IntProperty, EnumProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (
    updateNode, Vector_generate,
    repeat_last, fullList)


''' very non optimal routines. beware. I know this '''

def inset_special(vertices, faces, inset_rates, distances, ignores, make_inners, zero_mode="SKIP"):

    new_faces = []
    new_ignores = []
    new_insets = []

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
            new_insets.append([d, e, f])
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
            new_insets.append([e, f, g, h])
        return out_faces

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
            new_insets.append(temp_face)

        return out_faces

    def new_inner_from(face, inset_by, distance, make_inner):
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

        if abs(inset_by) < 1e-6:
            normal = mathutils.geometry.normal(*verts)
            new_vertex = avg_vec.lerp(avg_vec + normal, distance)
            vertices.append(new_vertex)
            new_vertex_idx = current_verts_idx
            new_faces
            for i, j in zip(face, face[1:]):
                new_faces.append([i, j, new_vertex_idx])
            new_faces.append([face[-1], face[0], new_vertex_idx])
            return

        # lerp and add to vertices immediately
        new_verts_prime = [avg_vec.lerp(v, inset_by) for v in verts]

        if distance:
            local_normal = mathutils.geometry.normal(*new_verts_prime)
            new_verts_prime = [v.lerp(v+local_normal, distance) for v in new_verts_prime]

        vertices.extend(new_verts_prime)

        tail_idx = (current_verts_idx + n) - 1

        get_faces_prime = {3: do_tri, 4: do_quad}.get(n, do_ngon)
        new_faces_prime = get_faces_prime(face, tail_idx, make_inner)
        new_faces.extend(new_faces_prime)

    for idx, face in enumerate(faces):
        inset_by = inset_rates[idx]

        good_inset = (inset_by > 0) or (zero_mode == 'FAN')
        if good_inset and (not ignores[idx]):
            new_inner_from(face, inset_by, distances[idx], make_inners[idx])
        else:
            new_faces.append(face)
            new_ignores.append(face)

    new_verts = [v[:] for v in vertices]
    return new_verts, new_faces, new_ignores, new_insets


class SvInsetSpecial(bpy.types.Node, SverchCustomTreeNode):
    '''
    Insets geometry, optional remove and/or translate
    Don't think of this as a realtime effect.
    '''

    bl_idname = 'SvInsetSpecial'
    bl_label = 'Inset Special'
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

        all_verts = Vector_generate(i['vertices'].sv_get())
        all_polys = i['polygons'].sv_get()

        all_inset_rates = i['inset'].sv_get()
        all_distance_vals = i['distance'].sv_get()

        # silly auto ugrade.
        if not i['ignore'].prop_name:
            i['ignore'].prop_name = 'ignore'
            i['make_inner'].prop_name = 'make_inner'

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
    bpy.utils.register_class(SvInsetSpecial)


def unregister():
    bpy.utils.unregister_class(SvInsetSpecial)
