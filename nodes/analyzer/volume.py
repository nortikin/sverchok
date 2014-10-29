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
import bmesh
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata
from sverchok.data_structure import (dataCorrect, updateNode,
                            SvSetSocketAnyType, SvGetSocketAnyType,
                            Vector_generate)


class SvVolumeNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Volume '''
    bl_idname = 'SvVolumeNode'
    bl_label = 'Volume Node'
    bl_icon = 'OUTLINER_OB_EMPTY'

    def draw_buttons(self, context, layout):
        pass

    def sv_init(self, context):
        self.inputs.new('VerticesSocket', 'Vers', 'Vers')
        self.inputs.new('StringsSocket', "Pols", "Pols")
        self.outputs.new('StringsSocket', "Volume", "Volume")

    def process(self):

        if self.outputs['Volume'].links and self.inputs['Vers'].links:
            vertices = Vector_generate(dataCorrect(SvGetSocketAnyType(self, self.inputs['Vers'])))
            faces = dataCorrect(SvGetSocketAnyType(self, self.inputs['Pols']))
            out = []
            for verts_obj, faces_obj in zip(vertices, faces):
                # this is for one object
                bme = bmesh_from_pydata(verts_obj, [], faces_obj)
                geom_in = bme.verts[:]+bme.edges[:]+bme.faces[:]
                bmesh.ops.recalc_face_normals(bme, faces=bme.faces[:])
                # calculation itself
                out.append(bme.calc_volume())
                bme.clear()
                bme.free()
                
            if self.outputs['Volume'].links:
                SvSetSocketAnyType(self, 'Volume', out)

    '''
    solution, that blow my mind, not delete.
    i have to investigate it here
    
    def Volume(self, bme):
        verts = obj_data.vertices     # array of vertices
        obj_data.calc_tessface()
        faces = obj_data.tessfaces        # array of faces
        VOLUME = 0;     # VOLUME OF THE OBJECT
        
        for f in faces:
            fverts = f.vertices      # getting face's vertices
            ab = verts[fverts[0]].co 
            ac = verts[fverts[1]].co
            ad = verts[fverts[2]].co
            
            # calculating determinator
            det = (ab[0]*ac[1]*ad[2]) - (ab[0]*ac[2]*ad[1]) - \
                (ab[1]*ac[0]*ad[2]) + (ab[1]*ac[2]*ad[0]) + \
                (ab[2]*ac[0]*ad[1]) - (ab[2]*ac[1]*ad[0])
            
            VOLUME += det/6
        '''

def register():
    bpy.utils.register_class(SvVolumeNode)


def unregister():
    bpy.utils.unregister_class(SvVolumeNode)

if __name__ == '__main__':
    register()

