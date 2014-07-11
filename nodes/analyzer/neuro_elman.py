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

# by Alexander Nedovizin

import bpy
from bpy.props import BoolProperty, IntProperty, StringProperty, FloatProperty

from node_tree import SverchCustomTreeNode
from data_structure import (updateNode, changable_sockets,
                            dataCorrect, svQsort,
                            SvSetSocketAnyType, SvGetSocketAnyType)
import random, cmath






class SvNeuro_Elman:
    InA = 0
    InB = 0
    wA = []
    gister = 0.01
    k_learning = 0.1
    
    
    def __init__(self, num_a, num_b):
        self.InA = num_a
        self.InB = num_b
        self.wA = self.init_w(num_a, num_b)
        
    
    def init_w(self, number, ext):
        out = []
        for n in range(number):
            tmp = []
            for e in range(ext):
                tmp.append(random.uniform(-1 , 1))
            out.append(tmp)
        
        return out
    
    
    def sigmoida(self, x, a):    
        #a = 5.0 # 5== -1 - +1, 1== -5 - +5
        b = 5/a
        return 1/(1+cmath.exp(-b*x).real)
        #return (cmath.exp(a*x).real-cmath.exp(-a*x).real)/(cmath.exp(-a*x).real+cmath.exp(a*x).real)

    
    def neuro(self, list_in, etalon, maxim, learning=False): 
        flag = True
        if flag:
            outA = self.layerA(list_in, maxim)
            outB = self.layerB(outA)
            suma = sum(outB)
            if learning and abs(etalon-suma)>self.gister:
                self.learning(suma, etalon)
            else:
            #if not learning or not abs(etalon-suma)>1e-2:
                flag = False
        
        ##print('wA',self.wA)
        return suma
    
    
    def layerA(self, list_in, maxim):
        lin = len(list_in)
        if lin!=self.InA:
            self.wA = self.init_w(lin, self.InB)
            self.InA = lin
            
        outA = list(map(self.sigmoida, list_in, [maxim]*self.InA))
        return outA
    
    
    def layerB(self, outA):
        summ_B = [0]*self.InB
        for ida,la in enumerate(self.wA):
            for idb, lb in enumerate(la):
                t1 = lb*outA[ida]
                summ_B[idb] += t1
        
        return summ_B

    
    def learning(self, sumB, etalon):
        d = etalon - sumB
        epsilon = self.k_learning
        
        for ida,la in enumerate(self.wA):
            for idb, lb in enumerate(la):
                self.wA[ida][idb] += epsilon*d*abs(lb)
        
        return 


# *********************


class SvNeuroElman1LNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Neuro Elman 1 Layer '''
    bl_idname = 'SvNeuroElman1LNode'
    bl_label = 'Neuro Elman 1 Layer'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    Elman = SvNeuro_Elman(1,1)
    k_learning = FloatProperty(name='k_learning',
                            default=0.1,
                            update=updateNode)
    gisterezis = FloatProperty(name='gisterezis',
                            default=0.01,
                            min = 0.0,
                            max = 1.0,
                            update=updateNode)
    maximum = FloatProperty(name='maximum',
                            default=3.0,
                            update=updateNode)

    def init(self, context):
        self.inputs.new('StringsSocket', "data", "data")
        self.inputs.new('StringsSocket', "etalon", "etalon")
        self.outputs.new('StringsSocket', "result", "result")
        
        
    def draw_buttons(self, context, layout):
        layout.prop(self, "k_learning", text="koeff learning")
        layout.prop(self, "gisterezis", text="gisterezis")
        layout.prop(self, "maximum", text="maximum")
    
    
    def update(self):
        self.Elman.gister = abs(self.gisterezis)
        self.Elman.k_learning = self.k_learning
        
        result = []
        if 'result' in self.outputs and len(self.outputs['result'].links) > 0 \
                and 'data' in self.inputs and len(self.inputs['data'].links) > 0:
            
            if 'etalon' in self.inputs and len(self.inputs['etalon'].links) > 0:
                etalon = SvGetSocketAnyType(self, self.inputs['etalon'])[0][0]
                #print('etalon', etalon)
                flag = True
            else:
                flag = False
                etalon = 0
            
            data_ = SvGetSocketAnyType(self, self.inputs['data'])
            for data in data_:
                if type(data) not in [list, tuple]: data = [data]
                ##print('\ndata',data)
                result.append([self.Elman.neuro(data, etalon, self.maximum, flag)])
        
        else:
            result = [[]]
            
        ##print('result', result)
        SvSetSocketAnyType(self, 'result', result)

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(SvNeuroElman1LNode)


def unregister():
    bpy.utils.unregister_class(SvNeuroElman1LNode)


