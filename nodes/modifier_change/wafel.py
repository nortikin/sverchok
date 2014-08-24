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

# nikitron made

import bpy

from mathutils import Vector
from mathutils.geometry import distance_point_to_plane as D2P
from mathutils import kdtree as KDT
from data_structure import Vector_generate, Vector_degenerate, fullList, \
                           SvSetSocketAnyType, SvGetSocketAnyType, dataCorrect
from math import sin, atan, cos, degrees, radians
from bpy.props import FloatProperty
from node_tree import SverchCustomTreeNode


class SvWafelNode(bpy.types.Node, SverchCustomTreeNode):
    '''Making vertical wafel - much raw node'''
    bl_idname = 'SvWafelNode'
    bl_label = 'Wafel'
    bl_icon = 'OUTLINER_OB_EMPTY'

    thick = FloatProperty(name='thick', description='thickness of material', \
                          default=0.01)

    def init(self, context):
        self.inputs.new('VerticesSocket', 'vec', 'vec')
        self.inputs.new('StringsSocket', 'edg', 'edg')
        self.inputs.new('VerticesSocket', 'vecplan', 'vecplan')
        self.inputs.new('StringsSocket', 'edgplan', 'edgplan')
        self.inputs.new('VerticesSocket', 'loc', 'loc')
        self.inputs.new('VerticesSocket', 'norm', 'norm')
        self.inputs.new('VerticesSocket', 'loccont', 'loccont')
        self.inputs.new('VerticesSocket', 'normcont', 'normcont')
        self.inputs.new('StringsSocket', 'thick').prop_name = 'thick'
        
        self.outputs.new('VerticesSocket', 'vupper', 'vupper')
        self.outputs.new('StringsSocket', 'outeup', 'outeup')
        self.outputs.new('VerticesSocket', 'vlower', 'vlower')
        self.outputs.new('StringsSocket', 'outelo', 'outelo')

    def calc_indexes(self, edgp, near):
        '''
        find binded edges and vertices, prepare to delete edges
        '''
        q = []
        deledges = []
        for i in edgp:
            if near in i:
                for t in i:
                    if t != near:
                        q.append(t)
                deledges.append(list(i))
        q.append(deledges)
        return q

    def interpolation(self, vecp, vec, en0, en1, thick):
        # shifting on height
        interp1_ = Vector((vecp[en0][0],vecp[en0][1],0)) - Vector((vec[0], vec[1], 0))
        interp1 = thick/interp1_.length
        interp2_ = Vector((vecp[en1][0],vecp[en1][1],0)) - Vector((vec[0], vec[1], 0))
        interp2 = thick/interp2_.length
        a = (vecp[en0][2]-vec[2])*interp1
        b = (vecp[en1][2]-vec[2])*interp2
        return a, b

    def calc_leftright(self, vecp, vec, dir, en0, en1, thick):
        '''
        calc left right from defined point and direction to join vertices
        oriented on given indexes
        '''
        a,b = vecp[en0]-vec+dir, vecp[en0]-vec-dir
        if a.length > b.length:
            left, l = vecp[en0], en0
            right,r = vecp[en1], en1
            lz, rz = self.interpolation(vecp, vec, en0, en1, thick)
        else:
            left, l = vecp[en1], en1
            right,r = vecp[en0], en0
            rz, lz = self.interpolation(vecp, vec, en0, en1, thick)
        return left, right, l, r, lz, rz

    def update(self):
        if 'vec' in self.inputs and 'edg' in self.inputs:
            print(self.name, 'is starting')
            if self.inputs['vec'].links and self.inputs['edg'].links:

                vec = self.inputs['vec'].sv_get()
                edg = self.inputs['edg'].sv_get()
                vecplan = self.inputs['vecplan'].sv_get()
                edgplan = self.inputs['edgplan'].sv_get()
                loc = self.inputs['loc'].sv_get()
                norm = self.inputs['norm'].sv_get()
                thick = self.inputs['thick'].sv_get()[0][0]
                if 'loccont' in self.inputs and self.inputs['loccont'].links and \
                       'normcont' in self.inputs and self.inputs['normcont'].links:
                    loccont = self.inputs['loccont'].sv_get()
                    normcont = self.inputs['normcont'].sv_get()
                    loc_cont = Vector_generate(loccont)
                    norm_cont = Vector_generate(normcont)
                else:
                    norm_cont = [[Vector((0,0,1)) for i in range(len(norm[0]))]]
                    loc_cont = [[Vector((0,0,10000)) for i in range(len(norm[0]))]]
                outeup = []
                outelo = []
                vupper = []
                vlower = []
                vec_ = Vector_generate(vec)
                loc_ = Vector_generate(loc)
                norm_ = Vector_generate(norm)
                vecplan_ = Vector_generate(vecplan)
                #print(self.name, 'veriables: \n', \
                #      vec_,'\n',
                #      vecplan_,'\n',
                #      loc_,'\n',
                #      loc_cont)
                for locon,nocon,l,n,vecp,edgp in zip(loc_cont[0],norm_cont[0],loc_[0],norm_[0],vecplan_,edgplan):
                    newinds1 = edgp.copy()
                    newinds2 = edgp.copy()
                    vupperob = vecp.copy()
                    vlowerob = vecp.copy()
                    deledges1 = []
                    deledges2 = []
                    k = 0
                    lenvep = len(vecp)
                    # find shift for thickness in sockets
                    angle = radians(degrees(atan(n.y/n.x))+90)
                    thick_2 = thick/2
                    direction = Vector((cos(angle),sin(angle),0))*thick_2
                    # KDtree collections closest to join edges to sockets
                    tree = KDT.KDTree(lenvep)
                    for i,v in enumerate(vecp):
                        tree.insert(v,i)
                    tree.balance()
                    # to define bounds
                    x = [i[0] for i in vecp]
                    y = [i[1] for i in vecp]
                    # vertical edges iterations
                    # every edge is object - two points, one edge
                    for v in vec_:
                        # sort vertices by Z value
                        vlist = [v[0],v[1]]
                        vlist.sort(key=lambda x: x[2], reverse=False)
                        # find two vertices - one lower, two upper
                        fliped = abs(D2P(v[0],locon,nocon))
                        if fliped < 0.001:
                            two, one = vlist
                        else:
                            one, two = vlist
                        # coplanar to 
                        cop = abs(D2P(one,l,n))
                        # flip plane coplanar
                        # defining bounds
                        inside = one[0]<max(x) and one[0]>min(x) and one[1]<max(y) and one[1]>min(y)
                        # if in bounds and coplanar do:
                        #print(self.name,l, cop, inside)
                        if cop < 0.001 and inside:
                            # вектор, индекс, расстояние
                            # запоминаем порядок
                            # находим какие удалить рёбра
                            # делаем выборку левая-правая точка
                            nearv_1, near_1 = tree.find(one)[:2]
                            nearv_2, near_2 = tree.find(two)[:2]
                            # indexes of two nearest points
                            # удалить рёбра что мешают спать заодно
                            en_0, en_1, de1 = self.calc_indexes(edgp, near_1)
                            deledges1.extend(de1)
                            en_2, en_3, de2 = self.calc_indexes(edgp, near_2)
                            deledges2.extend(de2)
                            # old delete
                            # en_0,en_1 = [[t for t in i if t != near_1] for i in edgp if near_1 in i]
                            # en_2,en_3 = [[t for t in i if t != near_2] for i in edgp if near_2 in i]
                            # print(vecp, one, direction, en_0, en_1)
                            # left-right indexes and vectors
                            left1, right1, l1, r1, lz1, rz1 = self.calc_leftright(vecp, one, direction, en_0, en_1, thick_2)
                            left2, right2, l2, r2, lz2, rz2 = self.calc_leftright(vecp, two, direction, en_2, en_3, thick_2)

                            # наполнение списков lenvep = length(vecp)
                            newinds1.extend([[l1, lenvep+k], [lenvep+k+3, r1]])
                            newinds2.extend([[l2, lenvep+k+3], [lenvep+k, r2]])
                            # пазы формируем независимо от верх низ
                            outeob = [[lenvep+k,lenvep+k+1],[lenvep+k+1,lenvep+k+2],[lenvep+k+2,lenvep+k+3]]
                            newinds1.extend(outeob)
                            newinds2.extend(outeob)
                            # средняя точка и её смещение по толщине материала
                            three = (one-two)/2 + two
                            vupperob.extend([two-direction-Vector((0,0,lz2)), three-direction, 
                                             three+direction, two+direction-Vector((0,0,rz2))])
                            vlowerob.extend([one+direction-Vector((0,0,rz1)), three+direction,
                                             three-direction, one-direction-Vector((0,0,lz1))])
                            k += 4
                    del tree
                    for e in deledges1:
                        if e in newinds1:
                            newinds1.remove(e)
                    for e in deledges2:
                        if e in newinds2:
                            newinds2.remove(e)
                    if vupperob or vlowerob:
                        outeup.append(newinds2)
                        outelo.append(newinds1)
                        vupper.append(vupperob)
                        vlower.append(vlowerob)
                vupper = Vector_degenerate(vupper)
                vlower = Vector_degenerate(vlower)
                
                if 'vupper' in self.outputs and self.outputs['vupper'].links:
                    out = dataCorrect(vupper)
                    SvSetSocketAnyType(self, 'vupper', out)
                if 'outeup' in self.outputs and self.outputs['outeup'].links:
                    SvSetSocketAnyType(self, 'outeup', outeup)
                if 'vlower' in self.outputs and self.outputs['vlower'].links:
                    SvSetSocketAnyType(self, 'vlower', vlower)
                if 'outelo' in self.outputs and self.outputs['outelo'].links:
                    SvSetSocketAnyType(self, 'outelo', outelo)
                print(self.name, 'is finishing')
        

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(SvWafelNode)


def unregister():
    bpy.utils.unregister_class(SvWafelNode)


if __name__ == '__main__':
    register()
