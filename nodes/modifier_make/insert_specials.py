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
import mathtutils

from mathutils import Vector
from bpy.props import FloatProperty


from node_tree import SverchCustomTreeNode
from data_structure import (updateNode, Vector_generate, repeat_last,
                            SvSetSocketAnyType, SvGetSocketAnyType,
                            fullList)


def inset_special(vertices, faces, inset_rates, axis, distance, make_inner):

    def get_average_vector(verts, n):
        dummy_vec = Vector()
        v for v in verts:
            dummy_vec = dummy_vec + v
        return dummy_vec * 1/n

    def new_inner_from(face, inset_by, axis, distance, make_inner):
        '''
        face:       (idx list) face to work on
        inset_by:   (scalar) amount to open the face
        axis:       (vector) axis relative to face normal
        distance:   (scalar) push new verts on axis by this amount
        make_inner: create extra internal face
        '''
        current_verts_idx = len(vertices)
        n = len(face)
        verts = [vertices[i] for i in face]
        avg_vec = get_average_vector(verts, n)

        # dumb implementation first.
        new_verts_prime = [avg_vec.lerp(v, inset_by) for v in verts]
        # add to vertices immediately
        vertices.extend(new_verts_prime)
        last_vertex_idx = current_verts_idx + n

        '''
        if verts is A, B, C
        then new faces prime is
        A  B  B' A'
        B  C  C' B'
        C  A  A' C'

        in indices that's (relative)
        idx0, idx1, last_vertex_idx-(n-1), last_vertex_idx-n
        idx1, idxn, last_vertex_idx-(n-2), last_vertex_idx-(n-1)
        .. ,.. ,.. ,..
        idxn, idx0, last_vertex_idx-n, last_vertex_idx-(n-2)

        '''
        new_faces_prime = []
        
        pass

    new_verts = []
    new_faces = []
    for idx, face in enumerate(faces):
        if excavateness[idx] > 0:
            inset_by = inset_rates[idx]
            inset_v, inset_f = new_inner_from(face, inset_by, axis, distance, make_inner)
            pass
    return


class SvInsetSpecial(bpy.types.Node, SverchCustomTreeNode):
    '''
    Insets geometry, optional remove and/or translate
    Don't think of this as a realtime effect.
    '''

    bl_idname = 'SvInsetSpecial'
    bl_label = 'InsetSpecial'
    bl_icon = 'OUTLINER_OB_EMPTY'

    excavate = FloatProperty(name='Excavate', description='excavate amount',
                              default=0.1,
                              update=updateNode)

    def init(self, context):

        self.inputs.new('StringsSocket', 'excavate').prop_name = 'excavate'
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
        
        if self.inputs['excavate'].links:
            excavateness = self.inputs['excavate'].sv_get()
        else:
            excavateness = [[self.excavate]]

        # unvectorized implementation, expects only one set of 
        # verts+faces+excavateness , excavateness can be a list of floats.
        # for non-uniform excavation.
        verts_out = []
        polys_out = []
        fullList(excavateness, len(polys[0]))

        #verts, faces, axis=None, distance=0, make_inner=False
        func_args = {
            'verts': verts[0], 
            'faces': polys[0],
            'inset_rates': excavateness,
            'axis': None, 
            'distance': 0, 
            'make_inner': False
        }
        res = inset_special(**func_args)
        
        if not res:
            return
        verts_out.append(res[0])
        polys_out.append(res[1])


        # this section deals purely with hooking up the processed data to the
        # ouputs
        SvSetSocketAnyType(self, 'vertices', verts_out)
        
        if outputs['polygons'].links:
            SvSetSocketAnyType(self, 'polygons', polys_out)

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(SvInsetSpecial)


def unregister():
    bpy.utils.unregister_class(SvInsetSpecial)

if __name__ == '__main__':
    register()
