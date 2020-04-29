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

from bpy.props import BoolProperty, IntProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.nodes_mixins.sv_animatable_nodes import SvAnimatableNode
from sverchok.data_structure import (updateNode, match_long_repeat, match_cross)
from sverchok.utils.logging import debug, info, error

class FakeObj(object):

    def __init__(self, obj):
        self.matrix_local = obj.matrix_local

        # mesh_settings = (..., True, 'RENDER')
        # data = OB.to_mesh(*mesh_settings)
        data = obj.to_mesh() # bpy.context.depsgraph, apply_modifiers=True, calc_undeformed=False)

        vertices = [vert.co[:] for vert in data.vertices]
        polygons = [poly.vertices[:] for poly in data.polygons]

        self.BVH = BVHTree.FromPolygons(vertices, polygons)
        obj.to_mesh_clear()


    def ray_cast(self, a, b):
        # obj.ray_cast returns  Return (result, location, normal, index
        # bvh.ray_cast returns: Vector location, Vector normal, int index, float distance
        #         ^--- therefor needs adjusting

        tv = self.BVH.ray_cast(a, b)
        if tv[0] == None:
            return [False, (0, 0, 0), (1, 0, 0), -1]
        else:
            return [True, tv[0], tv[1], tv[2]]



class SvOBJInsolationNode(bpy.types.Node, SverchCustomTreeNode, SvAnimatableNode):
    ''' Insolation by RayCast Object '''
    bl_idname = 'SvOBJInsolationNode'
    bl_label = 'Object ID Insolation'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_INSOLATION'

    mode: BoolProperty(name='input mode', default=False, update=updateNode)
    #mode2 = BoolProperty(name='output mode', default=False, update=updateNode)
    sort_critical: IntProperty(name='sort_critical', default=12, min=1,max=24, update=updateNode)
    separate: BoolProperty(name='separate the', default=False, update=updateNode)

    def sv_init(self, context):
        si,so = self.inputs.new,self.outputs.new
        #si('SvStringsSocket', 'Date')
        si('SvObjectSocket', 'Predator')
        si('SvObjectSocket', 'Victim')
        si('SvVerticesSocket', 'SunRays').use_prop = True
        #so('SvColorSocket',  "Color")
        so('SvVerticesSocket', "Centers")
        #so('SvVerticesSocket', "HitP")
        so('SvStringsSocket',  "Hours")
        # self.inputs[2].prop[2] = -1  # z down   # <--- mayybe?

    def draw_buttons(self, context, layout):
        self.draw_animatable_buttons(layout, icon_only=True)

    def draw_buttons_ext(self, context, layout):
        self.draw_animatable_buttons(layout)
        row = layout.row(align=True)
        row.prop(self,    "mode",   text="In Mode")
        row.prop(self,    "sort_critical",text="Limit")
        #row.prop(self,    "mode2",   text="Out Mode")

    def process(self):
        o,r,e = self.inputs
        #dd,o,r,e = self.inputs
        N,H = self.outputs
        #S,H,P,N = self.outputs
        outfin,OutLoc_,obj,rec,sm1,sc = [],[],o.sv_get(),r.sv_get()[0],self.mode,self.sort_critical
        #lenor = len(s.sv_get()[0])
        lendir = len(e.sv_get()[0])
        leno = len(obj)
        #st, en = match_cross([s.sv_get()[0], e.sv_get()[0]]) # 1,1,1,2,2,2 + 4,5,6,4,5,6
        st = []
        for i in rec.data.polygons:
            st.append(i.center[:])
            #(np.array(st_).sum(axis=1)/len(i.vertices)).tolist())
            #(np.array([[rec.data.vertices[k].co[:] for k in i.vertices]/len(i.vertices) for i in rec.data.polygons]).sum(axis=1)).tolist()
        if N.is_linked:
            N.sv_set([st])
        lenor = len(st)
        st, en = match_cross([st, e.sv_get()[0]]) # 1,1,1,2,2,2 + 4,5,6,4,5,6

        for OB in obj:
            if OB.type == 'FONT':
                NOB = FakeObj(OB)
            else:
                NOB = OB

            if sm1:
                obm = NOB.matrix_local.inverted()
                outfin.append([NOB.ray_cast(obm @ Vector(i), obm @ Vector(i2)) for i,i2 in zip(st,en)])
            else:
                outfin.append([NOB.ray_cast(i,i2) for i,i2 in zip(st,en)])

            if OB.type == 'FONT':
                del NOB
        self.debug(outfin)

        OutS_ = np.array([[i[0] for i in i2] for i2 in outfin]).reshape([leno,lenor,lendir])
        def colset(rec,OutS_):
            OutS_ = 1-OutS_.sum(axis=2)/lendir
            OutS = np.array([[[i,i,i,1] for i in k] for k in OutS_.tolist()]).reshape([leno,lenor,4]).tolist()
            if not 'SvInsol' in rec.data.vertex_colors:
                rec.data.vertex_colors.new(name='SvInsol')
            colors = rec.data.vertex_colors['SvInsol'].data
            for i, pol in enumerate(rec.data.polygons):
                self.debug(pol.loop_indices,OutS[0][i])
                for co in pol.loop_indices:
                    colors[co].color = OutS[0][i]
        colset(rec,OutS_)
        def matset(rec):
            # add new material with nodes
            ms = rec.material_slots
            if not 'svmat' in bpy.data.materials:
                manew = bpy.data.materials.new('svmat')
                manew.use_nodes = True
            if not len(ms):
                # append if no slots
                rec.data.materials.append(manew)
            if not ms[-1].material:
                # assign if no material in slot
                ms[-1].material = manew
            trem = ms[-1].material.node_tree
            matnodes = trem.nodes
            if not 'Attribute' in matnodes:
                att = matnodes.new('ShaderNodeAttribute')
            else:
                att = matnodes['Attribute']
            if not 'Diffuse BSDF' in matnodes:
                dif = matnodes.new('ShaderNodeBsdfDiffuse')
            else:
                dif = matnodes['Diffuse BSDF']
            att.attribute_name = 'SvInsol'
            trem.links.new(dif.inputs[0],att.outputs[0])
        matset(rec)
        if H.is_linked:
            OutH = []
            for k in OutS_.sum(axis=2).tolist():
                OutH_ = []
                for i in k:
                    li = lendir-i
                    if li < sc+1:
                        OutH_.append([str(li)])
                    else:
                        OutH_.append([''])
                OutH.append(OutH_)
            #OutH = [[[str(lendir-i)] for i in k] for k in OutS_.sum(axis=2).tolist()]
            H.sv_set(OutH)
        '''if S.is_linked:
            OutS = np.array([[[i,i,0,1.0] for i in k] for k in OutS_.tolist()]).reshape([leno,lenor,4]).tolist()
            #OutS = 1-OutS_.sum(axis=2)/lendir
            #OutS = np.array([[[[i,i,0,1.0] for t in range(4)] for i in k] for k in OutS_.tolist()]).reshape([leno,lenor*4,4]).tolist() #.reshape([leno,lenor*4,4]).tolist()
            #OutS = [round(1-sum([OutS_[0][k*u] for u in range(lendir)])/lendir, 1) for k in range(lenor)]
            S.sv_set(OutS)'''
        ''' # colors works wrong
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
        '''

        ''' # N solved upper easily
        if N.is_linked:
            OutN_ = np.array([[i[2][:] for i in i2] for i2 in outfin]).reshape([leno,lenor,lendir,3])
            #OutN_ = [[i[2][:] for i in i2] for i2 in outfin]
            OutN = OutN_[0,:,0]
            #OutN = [[OutN_[0][k*u] for u in range(lendir)] for k in range(lenor)]
            N.sv_set([OutN.tolist()])
        '''



def register():
    bpy.utils.register_class(SvOBJInsolationNode)


def unregister():
    bpy.utils.unregister_class(SvOBJInsolationNode)
