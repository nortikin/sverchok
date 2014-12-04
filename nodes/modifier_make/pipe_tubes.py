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
from bpy.props import IntProperty, FloatProperty, BoolProperty
from mathutils import Vector

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
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
    offset = FloatProperty(name='offset', description='offset from ends',
                  default=0.0, min=-1, max=0.5,
                  options={'ANIMATABLE'}, update=updateNode)
    extrude = FloatProperty(name='extrude', description='extrude',
                  default=1.0, min=0.2, max=10.0,
                  options={'ANIMATABLE'}, update=updateNode)
    close = BoolProperty(name='close', description='close ends',
                  default=False,
                  options={'ANIMATABLE'}, update=updateNode)


    def draw_buttons(self, context, layout):
        layout.prop(self,'close',text='close')

    def sv_init(self, context):
        self.inputs.new('VerticesSocket', 'Vers', 'Vers')
        self.inputs.new('StringsSocket', "Edgs", "Edgs")
        self.inputs.new('StringsSocket', "Diameter", "Diameter").prop_name = 'diameter'
        self.inputs.new('StringsSocket', "Sides", "Sides").prop_name = 'nsides'
        self.inputs.new('StringsSocket', "Offset", "Offset").prop_name = 'offset'
        self.inputs.new('StringsSocket', "Extrude", "Extrude").prop_name = 'extrude'
        self.outputs.new('VerticesSocket', 'Vers', 'Vers')
        self.outputs.new('StringsSocket', "Pols", "Pols")

    def process(self):
        
        if self.outputs['Vers'].is_linked and self.inputs['Vers'].is_linked:
            Vecs = self.inputs['Vers'].sv_get()
            Edgs = self.inputs['Edgs'].sv_get()
            Nsides = max(self.inputs['Sides'].sv_get()[0][0], 4)
            Diameter = self.inputs['Diameter'].sv_get()[0][0]
            Offset = self.inputs['Offset'].sv_get()[0][0]
            Extrude = self.inputs['Extrude'].sv_get()[0][0]
            
            outv, outp = self.Do_vecs(Vecs,Edgs,Diameter,Nsides,Offset,Extrude)
            
            if self.outputs['Vers'].is_linked:
                self.outputs['Vers'].sv_set(outv)
            if self.outputs['Pols'].is_linked:
                self.outputs['Pols'].sv_set(outp)
    

    def Do_vecs(self, Vecs,Edgs,Diameter,Nsides,Offset,Extrude):
        Sides = int(360/Nsides)
        if Nsides == 4:
            Diameter = Diameter*sqrt(2)/2
        else:
            Diameter = Diameter/2
        circle = [ (Vector((sin(radians(i))*Extrude,cos(radians(i)),0))*Diameter) \
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
                verts1 = [ (ve*matrix_rot+v1+vecdi*Offset)[:] for ve in circle ]
                verts2 = [ (ve*matrix_rot+v2-vecdi*Offset)[:] for ve in circle ]
                outv_.extend(verts1)
                outv_.extend(verts2)
                pols = [ [k+i+0,k+i-1,k+i+Nsides-1,k+i+Nsides] for i in range(1,Nsides,1) ]
                pols.append([k+0,k+Nsides-1,k+Nsides*2-1,k+Nsides])
                if self.close and k!=0:
                    p = [ [k+i+0-Nsides,k+i-1-Nsides,k+i-1,k+i] for i in range(1,Nsides,1) ]
                    pols.extend(p)
                    pols.append([k+0-Nsides,k-1,k+Nsides-1,k])
                outp_.extend(pols)
                k += Nsides*2
            outv.append(outv_)
            outp.append(outp_)
        return outv, outp



def register():
    bpy.utils.register_class(SvPipeNode)


def unregister():
    bpy.utils.unregister_class(SvPipeNode)

if __name__ == '__main__':
    register()

