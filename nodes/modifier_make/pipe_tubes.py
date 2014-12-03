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
from math import sin, cos, radians, sqrt


class SvPipeNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Pipe from edges '''
    bl_idname = 'SvPipeNode'
    bl_label = 'Pipe tube Node'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    nsides = IntProperty(name='nsides', description='number of sides',
                  default=4, min=4, max=24,
                  options={'ANIMATABLE'}, update=updateNode)
    diameter = FloatProperty(name='diameter', description='diameter',
                  default=0.4,
                  options={'ANIMATABLE'}, update=updateNode)
    

    def draw_buttons(self, context, layout):
        pass

    def sv_init(self, context):
        self.inputs.new('VerticesSocket', 'Vers', 'Vers')
        self.inputs.new('StringsSocket', "Edgs", "Edgs")
        self.inputs.new('StringsSocket', "Diameter", "Diameter").prop_name = 'diameter'
        self.inputs.new('StringsSocket', "Sides", "Sides").prop_name = 'nsides'
        self.outputs.new('VerticesSocket', 'Vers', 'Vers')
        self.outputs.new('StringsSocket', "Pols", "Pols")

    def process(self):
        
        if self.outputs['Vers'].links and self.inputs['Vers'].links:
            Vecs = SvGetSocketAnyType(self, self.inputs['Vers'])
            Edgs = SvGetSocketAnyType(self, self.inputs['Edgs'])
            Nsides = max(self.inputs['Sides'].sv_get()[0][0], 4)
            Diameter = self.inputs['Diameter'].sv_get()[0][0]
            
            outv, outp = self.Do_vecs(Vecs,Edgs,Diameter,Nsides)
            
            if self.outputs['Vers'].links:
                SvSetSocketAnyType(self, 'Vers', outv)
            if self.outputs['Pols'].links:
                SvSetSocketAnyType(self, 'Pols', outp)
    

    def Do_vecs(self, Vecs,Edgs,Diameter,Nsides):
        Sides = int(360/Nsides)
        if Nsides == 4:
            Diameter = Diameter*sqrt(2)/2
        else:
            Diameter = Diameter/2
        circle = [ (Vector((sin(radians(i)),cos(radians(i)),0))*Diameter) \
                    for i in range(45,405,Sides) ]
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
                pols = [ [k+i+0,k+i-1,k+i+Nsides-1,k+i+Nsides] for i in range(1,Nsides,1) ]
                pols.append([k+0,k+Nsides-1,k+Nsides*2-1,k+Nsides])
                k += Nsides*2
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

