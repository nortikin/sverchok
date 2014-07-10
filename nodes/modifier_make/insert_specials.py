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
from bpy.props import FloatProperty
import bmesh

from node_tree import SverchCustomTreeNode
from data_structure import (updateNode, Vector_generate, repeat_last,
                            SvSetSocketAnyType, SvGetSocketAnyType,
                            fullList)


def inset_special(vertices, faces, excavateness):

    def new_inner_from(face):
        pass

    new_verts = []
    new_faces = []
    for idx, face in enumerate(faces):
        if excavateness[idx] > 0:
            inset_verts = new_inner_from(face)
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
        res = inset_special(verts[0], polys[0], excavateness):
        
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
