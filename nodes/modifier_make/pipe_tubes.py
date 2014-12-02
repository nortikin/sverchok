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
from bpy.props import IntProperty, FloatProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode,
                            SvSetSocketAnyType, SvGetSocketAnyType)
from mathutils import Vector
from math import sin, cos, radians


class SvPipeNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Pipe from edges '''
    bl_idname = 'SvPipeNode'
    bl_label = 'Pipe tube Node'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    #nsides = IntProperty(name='nsides', description='number of sides',
    #              default=1, min=1, max=64,
    #              options={'ANIMATABLE'}, update=updateNode)
    radius = FloatProperty(name='redius', description='radius',
                  default=0.4,
                  options={'ANIMATABLE'}, update=updateNode)
    

    def draw_buttons(self, context, layout):
        pass

    def sv_init(self, context):
        self.inputs.new('VerticesSocket', 'Vers', 'Vers')
        self.inputs.new('StringsSocket', "Edgs", "Edgs")
        self.inputs.new('StringsSocket', "Radius", "Radius").prop_name = 'radius'
        self.outputs.new('VerticesSocket', 'Vers', 'Vers')
        self.outputs.new('StringsSocket', "Pols", "Pols")

    def process(self):
        
        if self.outputs['Vers'].links and self.inputs['Vers'].links:
            Vecs = SvGetSocketAnyType(self, self.inputs['Vers'])
            Edgs = SvGetSocketAnyType(self, self.inputs['Edgs'])
            
            Radius = self.inputs['Radius'].sv_get()[0][0]
            
            outv, outp = self.Do_vecs(Vecs,Edgs,Radius)
            
            if self.outputs['Vers'].links:
                SvSetSocketAnyType(self, 'Vers', outv)
            if self.outputs['Pols'].links:
                SvSetSocketAnyType(self, 'Pols', outp)
    

    def Do_vecs(self, Vecs,Edgs,Radius):
        circle = [ (Vector((sin(radians(i)),cos(radians(i)),0))*Radius) \
                    for i in range(0,360,30) ]
        outv = []
        outp = []
        for E,V in zip(Edgs,Vecs):
            outv_ = []
            outp_ = []
            k = 0
            for e in E:
                v2,v1 = Vector(V[e[1]]),Vector(V[e[0]])
                vecdi = v2-v1
                matrix_rot = vecdi.rotation_difference(Vector((0,0,1))).to_matrix().to_4x4()
                verts1 = [ (ve*matrix_rot+v1)[:] for ve in circle ]
                verts2 = [ (ve*matrix_rot+v2)[:] for ve in circle ]
                outv_.extend(verts1)
                outv_.extend(verts2)
                pols = [ [k+i+0,k+i-1,k+i+11,k+i+12] for i in range(1,12,1) ]
                pols.append([k+0,k+11,k+23,k+12])
                k += 24
                outp_.extend(pols)
            outv.append(outv_)
            outp.append(outp_)
        return outv, outp



def register():
    bpy.utils.register_class(SvPipeNode)


def unregister():
    bpy.utils.unregister_class(SvPipeNode)

if __name__ == '__main__':
    register()

