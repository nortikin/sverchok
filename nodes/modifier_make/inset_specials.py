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

import bpy
import mathutils

from mathutils import Vector
from bpy.props import FloatProperty


from node_tree import SverchCustomTreeNode
from data_structure import (updateNode, Vector_generate, repeat_last,
                            SvSetSocketAnyType, SvGetSocketAnyType,
                            fullList)


''' very non optimal routines. beware. I know this '''


def inset_special(vertices, faces, inset_rates, axis, distance, make_inner):

    new_faces = []
    # print(len(faces), len(inset_rates))

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
        vertices.extend(new_verts_prime)

        tail_idx = (current_verts_idx + n) - 1

        get_faces_prime = {3: do_tri, 4: do_quad}.get(n, do_ngon)
        new_faces_prime = get_faces_prime(face, tail_idx, make_inner)
        new_faces.extend(new_faces_prime)

    for idx, face in enumerate(faces):
        inset_by = inset_rates[idx][0]  # WARNING, levels issue
        if inset_by > 0:
            new_inner_from(face, inset_by, axis, distance, make_inner)

    new_verts = [v[:] for v in vertices]
    # print('new_faces=', new_faces)
    return new_verts, new_faces


class SvInsetSpecial(bpy.types.Node, SverchCustomTreeNode):
    '''
    Insets geometry, optional remove and/or translate
    Don't think of this as a realtime effect.
    '''

    bl_idname = 'SvInsetSpecial'
    bl_label = 'InsetSpecial'
    bl_icon = 'OUTLINER_OB_EMPTY'

    inset = FloatProperty(
        name='Inset', description='inset amount', default=0.1, update=updateNode)

    def init(self, context):

        self.inputs.new('StringsSocket', 'inset').prop_name = 'inset'
        self.inputs.new('VerticesSocket', 'vertices', 'vertices')
        self.inputs.new('StringsSocket', 'polygons', 'polygons')

        self.outputs.new('VerticesSocket', 'vertices', 'vertices')
        self.outputs.new('StringsSocket', 'polygons', 'polygons')

    def update(self):
        if not 'polygons' in self.outputs:
            return
        if not any((s.links for s in self.outputs)):
            return

        i = self.inputs
        o = self.outputs
        if all([i['vertices'].links, i['polygons'].links, o['vertices'].links]):
            self.process()

    def process(self):
        inputs = self.inputs
        outputs = self.outputs

        verts = Vector_generate(SvGetSocketAnyType(self, inputs['vertices']))
        polys = SvGetSocketAnyType(self, inputs['polygons'])

        if self.inputs['inset'].links:
            inset_rates = self.inputs['inset'].sv_get()
        else:
            inset_rates = [[self.inset]]

        # print(inset_rates)

        # unvectorized implementation, expects only one set of
        # verts+faces+inset_rates , inset_rates can be a list of floats.
        # for non-uniform excavation.
        verts_out = []
        polys_out = []
        fullList(inset_rates, len(polys[0]))

        #verts, faces, axis=None, distance=0, make_inner=False
        func_args = {
            'vertices': verts[0],
            'faces': polys[0],
            'inset_rates': inset_rates,
            'axis': None,
            'distance': 0,
            'make_inner': False
        }
        # print(func_args)
        res = inset_special(**func_args)

        if not res:
            return

        # unvectorized.
        verts_out, polys_out = res

        # this section deals purely with hooking up the processed data to the
        # ouputs
        SvSetSocketAnyType(self, 'vertices', [verts_out])

        if outputs['polygons'].links:
            SvSetSocketAnyType(self, 'polygons', [polys_out])

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(SvInsetSpecial)


def unregister():
    bpy.utils.unregister_class(SvInsetSpecial)

if __name__ == '__main__':
    register()
