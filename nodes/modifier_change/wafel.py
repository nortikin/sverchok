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

from mathutils import Vector, Euler
from mathutils.geometry import distance_point_to_plane as D2P
from mathutils.geometry import intersect_line_line as IL2L
from mathutils import kdtree as KDT
from data_structure import Vector_generate, Vector_degenerate, fullList, \
                           SvSetSocketAnyType, SvGetSocketAnyType, dataCorrect
from math import sin, atan, cos, degrees, radians
from bpy.props import FloatProperty, BoolProperty, EnumProperty
from node_tree import SverchCustomTreeNode


class SvWafelNode(bpy.types.Node, SverchCustomTreeNode):
    '''Making vertical wafel - much raw node'''
    bl_idname = 'SvWafelNode'
    bl_label = 'Wafel'
    bl_icon = 'OUTLINER_OB_EMPTY'

    thick = FloatProperty(name='thick', description='thickness of material',
                           default=0.01)
    rounded = BoolProperty(name='rounded', description='making rounded edges',
                           default = False)
    up_down = EnumProperty(name='up_down', items=[('UP','UP','UP'),('DOWN','DOWN','DOWN')],
                           description='up or down', default = 'UP')

    def init(self, context):
        self.inputs.new('VerticesSocket', 'vec', 'vec')
        self.inputs.new('StringsSocket', 'edg', 'edg')
        self.inputs.new('VerticesSocket', 'vecplan', 'vecplan')
        self.inputs.new('StringsSocket', 'edgplan', 'edgplan')
        self.inputs.new('VerticesSocket', 'loc', 'loc')
        self.inputs.new('VerticesSocket', 'norm', 'norm')
        self.inputs.new('VerticesSocket', 'vecont', 'vecont')
        self.inputs.new('VerticesSocket', 'loccont', 'loccont')
        self.inputs.new('VerticesSocket', 'normcont', 'normcont')
        self.inputs.new('StringsSocket', 'thick').prop_name = 'thick'
        
        self.outputs.new('VerticesSocket', 'vupper', 'vupper')
        self.outputs.new('StringsSocket', 'outeup', 'outeup')
        self.outputs.new('VerticesSocket', 'vlower', 'vlower')
        self.outputs.new('StringsSocket', 'outelo', 'outelo')

    def draw_buttons(self, context, layout):
        layout.prop(self, 'rounded')
        layout.prop(self, 'up_down', expand=True)

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
        left right - points
        l r - indexes of this nearest points
        lz rz - height difference to compensate
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

    def get_coplanar(self,vec, loc_cont, norm_cont,vec_cont):
        '''
        if coplanar - than make flip cutting up-bottom
        '''
        for locon, nocon, vecon in zip(loc_cont,norm_cont,vec_cont):
            x = [i[0] for i in vecon]
            y = [i[1] for i in vecon]
            con_domein = vec[0]<max(x) and vec[0]>min(x) and vec[1]<max(y) and vec[1]>min(y)
            if con_domein:
                a = abs(D2P(vec,locon[0],nocon[0]))
                if a < 0.001:
                    return True
        return False

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
                sinuso60 = 0.8660254037844386
                sinuso60_minus = 0.133974596
                sinuso30 = 0.5
                sinuso45 = 0.7071067811865475
                if 'loccont' in self.inputs and self.inputs['loccont'].links and \
                       'normcont' in self.inputs and self.inputs['normcont'].links:
                    vecont = self.inputs['vecont'].sv_get()
                    loccont = self.inputs['loccont'].sv_get()
                    normcont = self.inputs['normcont'].sv_get()
                    vec_cont = Vector_generate(vecont)
                    loc_cont = Vector_generate(loccont)
                    norm_cont = Vector_generate(normcont)
                else:
                    norm_cont = [[Vector((0,0,1)) for i in range(len(norm[0]))]]
                    loc_cont = [[Vector((0,0,10000)) for i in range(len(norm[0]))]]
                    vec_cont = [[Vector((1000,0,1))] for i in range(len(norm[0]))]
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
                for l,n,vecp, edgp in zip(loc_[0],norm_[0],vecplan_,edgplan):
                    newinds1 = edgp.copy()
                    newinds2 = edgp.copy()
                    vupperob = vecp.copy()
                    vlowerob = vecp.copy()
                    deledges1 = []
                    deledges2 = []
                    k = 0
                    lenvep = len(vecp)
                    # KDtree collections closest to join edges to sockets
                    tree = KDT.KDTree(lenvep)
                    for i,v in enumerate(vecp):
                        tree.insert(v,i)
                    tree.balance()
                    # to define bounds
                    x = [i[0] for i in vecp]
                    y = [i[1] for i in vecp]
                    m1x,m2x,m1y,m2y = max(x), min(x), max(y), min(y)
                    # vertical edges iterations
                    # every edge is object - two points, one edge
                    for v in vec_:
                        # sort vertices by Z value
                        # find two vertices - one lower, two upper
                        vlist = [v[0],v[1]]
                        vlist.sort(key=lambda x: x[2], reverse=False)
                        # flip if coplanar to enemy plane
                        # flip plane coplanar
                        fliped = self.get_coplanar(v[0], loc_cont,norm_cont, vec_cont)
                        if fliped:
                            two, one = vlist
                        else:
                            one, two = vlist
                        # coplanar to owner
                        cop = abs(D2P(one,l,n))
                        # defining bounds
                        inside = one[0]<m1x and one[0]>m2x and one[1]<m1y and one[1]>m2y
                        # if in bounds and coplanar do:
                        #print(self.name,l, cop, inside)
                        if cop < 0.001 and inside:
                            '''
                            huge calculations. if we can reduce...
                            '''
                            # find shift for thickness in sockets
                            angle = radians(degrees(atan(n.y/n.x))+90)
                            thick_2 = thick/2
                            direction = Vector((cos(angle),sin(angle),0))*thick_2
                            #matr = Euler((0,0,angle),'YZX').to_matrix().to_4x4()
                            #matr.translation = 
                            #direction = matr
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
                            # с учётом интерполяций по высоте
                            left1, right1, l1, r1, lz1, rz1 = \
                                    self.calc_leftright(vecp, one, direction, en_0, en_1, thick_2)
                            left2, right2, l2, r2, lz2, rz2 = \
                                    self.calc_leftright(vecp, two, direction, en_2, en_3, thick_2)

                            # средняя точка и её смещение по толщине материала
                            three = (one-two)/2 + two
                            if self.rounded:
                                '''рёбра'''
                                if fliped:
                                    doflip = -1
                                else:
                                    doflip = 1
                                # пазы формируем независимо от верх низ

                                outeob1 = [[lenvep+k+8,lenvep+k],[lenvep+k+1,lenvep+k+2],
                                          [lenvep+k+2,lenvep+k+3],[lenvep+k+3,lenvep+k+4],
                                          [lenvep+k+4,lenvep+k+5],[lenvep+k+5,lenvep+k+6],
                                          [lenvep+k+6,lenvep+k+7],[lenvep+k+7,lenvep+k+8],
                                          [lenvep+k+9,lenvep+k+1]]

                                outeob2 = [[lenvep+k,lenvep+k+1],[lenvep+k+1,lenvep+k+2],
                                          [lenvep+k+2,lenvep+k+3],[lenvep+k+3,lenvep+k+4],
                                          [lenvep+k+4,lenvep+k+5],[lenvep+k+5,lenvep+k+6],
                                          [lenvep+k+6,lenvep+k+7],[lenvep+k+7,lenvep+k+8],
                                          [lenvep+k+8,lenvep+k+9]]
                                # наполнение списков lenvep = length(vecp)
                                newinds1.extend([[l1, lenvep+k], [lenvep+k+9, r1]])
                                newinds2.extend([[l2, lenvep+k+9], [lenvep+k, r2]])
                                '''Вектора'''
                                thick_3 = thick/3
                                thick_6 = thick/6
                                round1 = Vector((0,0,doflip*thick_3))
                                round2 = Vector((0,0,doflip*thick_3*sinuso30))
                                round2_= direction/3 + direction*(2*sinuso60/3)
                                round3 = Vector((0,0,doflip*thick_3*sinuso60_minus))
                                round3_= direction/3 + direction*(2*sinuso30/3)
                                round4 = direction/3
                                vupperob.extend([two-direction-Vector((0,0,lz2)),
                                                 three+round1-direction, three+round2-round2_,
                                                 three+round3-round3_, three-round4,
                                                 three+round4, three+round3+round3_,
                                                 three+round2+round2_, three+round1+direction,
                                                 two+direction-Vector((0,0,rz2))])
                                vlowerob.extend([one+direction-Vector((0,0,rz1)),
                                                 three-round1-direction, three-round2-round2_,
                                                 three-round3-round3_, three-round4,
                                                 three+round4, three-round3+round3_,
                                                 three-round2+round2_, three-round1+direction,
                                                 one-direction-Vector((0,0,lz1))])
                                k += 10
                            else:
                                '''рёбра'''
                                # пазы формируем независимо от верх низ
                                outeob1 = [[lenvep+k,lenvep+k+1],[lenvep+k+1,lenvep+k+2],[lenvep+k+2,lenvep+k+3]]
                                outeob2 = [[lenvep+k,lenvep+k+1],[lenvep+k+1,lenvep+k+2],[lenvep+k+2,lenvep+k+3]]
                                # наполнение списков lenvep = length(vecp)
                                newinds1.extend([[l1, lenvep+k], [lenvep+k+3, r1]])
                                newinds2.extend([[l2, lenvep+k+3], [lenvep+k, r2]])
                                '''Вектора'''
                                vupperob.extend([two-direction-Vector((0,0,lz2)), three-direction, 
                                                 three+direction, two+direction-Vector((0,0,rz2))])
                                vlowerob.extend([one+direction-Vector((0,0,rz1)), three+direction,
                                                 three-direction, one-direction-Vector((0,0,lz1))])
                                k += 4
                            newinds1.extend(outeob1)
                            newinds2.extend(outeob2)
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

