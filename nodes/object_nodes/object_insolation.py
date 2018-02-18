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
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

from bpy.props import BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode, match_long_repeat, match_cross)
from sverchok.utils.logging import debug, info, error

class FakeObj(object):

    def __init__(self, OB):
        self.matrix_local = OB.matrix_local
        
        mesh_settings = (bpy.context.scene, True, 'RENDER')
        data = OB.to_mesh(*mesh_settings)

        vertices = [vert.co[:] for vert in data.vertices] 
        polygons = [poly.vertices[:] for poly in data.polygons]

        self.BVH = BVHTree.FromPolygons(vertices, polygons)
        bpy.data.meshes.remove(data)


    def ray_cast(self, a, b):
        # obj.ray_cast returns  Return (result, location, normal, index
        # bvh.ray_cast returns: Vector location, Vector normal, int index, float distance
        #         ^--- therefor needs adjusting
        
        tv = self.BVH.ray_cast(a, b)
        if tv[0] == None:
            return [False, (0, 0, 0), (1, 0, 0), -1]
        else:
            return [True, tv[0], tv[1], tv[2]]



class SvOBJInsolationNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Insolation by RayCast Object '''
    bl_idname = 'SvOBJInsolationNode'
    bl_label = 'Object ID Insolation'
    bl_icon = 'OUTLINER_OB_EMPTY'

    mode = BoolProperty(name='input mode', default=False, update=updateNode)
    mode2 = BoolProperty(name='output mode', default=False, update=updateNode)
    separate = BoolProperty(name='separate the', default=False, update=updateNode)

    def sv_init(self, context):
        si,so = self.inputs.new,self.outputs.new
        si('SvObjectSocket', 'Objects')
        si('VerticesSocket', 'origin').use_prop = True
        si('VerticesSocket', 'direction').use_prop = True
        so('StringsSocket',  "hours")
        so('VerticesSocket', "HitP")
        so('VerticesSocket', "HitNorm")
        # self.inputs[2].prop[2] = -1  # z down   # <--- mayybe?

    def draw_buttons_ext(self, context, layout):
        row = layout.row(align=True)
        row.prop(self,    "mode",   text="In Mode")
        row.prop(self,    "mode2",   text="Out Mode")
        row = layout.row(align=True)

    def process(self):
        o,s,e = self.inputs
        S,P,N = self.outputs
        outfin,OutLoc_,obj,sm1,sm2 = [],[],o.sv_get(),self.mode,self.mode2
        lenor = len(s.sv_get()[0])
        lendir = len(e.sv_get()[0])
        leno = len(obj)
        st, en = match_cross([s.sv_get()[0], e.sv_get()[0]]) # 1,1,1,2,2,2 + 4,5,6,4,5,6

        for OB in obj:
            if OB.type == 'FONT':
                NOB = FakeObj(OB)
            else:
                NOB = OB

            if sm1:
                obm = NOB.matrix_local.inverted()
                outfin.append([NOB.ray_cast(obm*Vector(i), obm*Vector(i2)) for i,i2 in zip(st,en)])
            else:
                outfin.append([NOB.ray_cast(i,i2) for i,i2 in zip(st,en)])

            if OB.type == 'FONT':
                del NOB
        print(outfin)

        if S.is_linked:
            OutS_ = np.array([[i[0] for i in i2] for i2 in outfin]).reshape([leno,lenor,lendir])
            OutS = 1-OutS_.sum(axis=2)/lendir
            #OutS = [round(1-sum([OutS_[0][k*u] for u in range(lendir)])/lendir, 1) for k in range(lenor)]
            S.sv_set(OutS.round(1).tolist())

        if sm2:
            if P.is_linked:
                for i,i2 in zip(obj,outfin):
                    omw = i.matrix_world
                    OutLoc_.append([(omw*i[1])[:] for i in i2])
                OutLoc_ = np.array(OutLoc_).reshape([leno,lenor,lendir,3])
                OutLoc = OutLoc_[0,:,0]
                #OutLoc = [[OutLoc_[0][k*u] for u in range(lendir)] for k in range(lenor)]
                P.sv_set([OutLoc.tolist()])
        else:
            if P.is_linked:
                OutLoc_ = np.array([[i[1][:] for i in i2] for i2 in outfin]).reshape([leno,lenor,lendir,3])
                #OutLoc_ = [[i[1][:] for i in i2] for i2 in outfin]
                OutLoc = OutLoc_[0,:,0]
                #OutLoc = [[OutLoc_[0][k*u] for u in range(lendir)] for k in range(lenor)]
                P.sv_set([OutLoc.tolist()])

        if N.is_linked:
            OutN_ = np.array([[i[2][:] for i in i2] for i2 in outfin]).reshape([leno,lenor,lendir,3])
            #OutN_ = [[i[2][:] for i in i2] for i2 in outfin]
            OutN = OutN_[0,:,0]
            #OutN = [[OutN_[0][k*u] for u in range(lendir)] for k in range(lenor)]
            N.sv_set([OutN.tolist()])


    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(SvOBJInsolationNode)


def unregister():
    bpy.utils.unregister_class(SvOBJInsolationNode)

if __name__ == '__main__':
    register()