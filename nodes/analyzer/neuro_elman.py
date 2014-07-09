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
from bpy.props import BoolProperty, IntProperty, StringProperty

from node_tree import SverchCustomTreeNode
from data_structure import (updateNode, changable_sockets,
                            dataCorrect, svQsort,
                            SvSetSocketAnyType, SvGetSocketAnyType)
import random, cmath




def sigmoida(x, a):    
    #a = 5.0 # 5== -1 - +1, 1== -5 - +5
    b = 5/a
    return 1/(1+cmath.exp(-b*x).real)
    #return (cmath.exp(a*x).real-cmath.exp(-a*x).real)/(cmath.exp(-a*x).real+cmath.exp(a*x).real)


class Neuro_Elman:
    InA = 0
    InB = 0
    wA = []
    
    
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
    
    
    def neuro(self, list_in, etalon, learning=False): 
        flag = True
        while flag:
            outA = self.layerA(list_in)
            outB = self.layerB(outA)
            suma = sum(outB)
            if learning:
                self.learning(suma, etalon)
            
            if not learning or not abs(etalon-suma)>1e-2:
                flag = False
            
        return suma
    
    
    def layerA(self, list_in):
        lin = len(list_in)
        if lin!=self.InA:
            self.wA = self.init_w(lin, self.InB)
            self.InA = lin
            
        outA = list(map(sigmoida, list_in, [1]*self.InA))
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
        epsilon = 0.3
        
        for ida,la in enumerate(self.wA):
            for idb, lb in enumerate(la):
                self.wA[ida][idb] += epsilon*d*abs(lb)
        
        return 


# *********************


class NeuroElman1LNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Neuro Elman 1 Layer '''
    bl_idname = 'NeuroElman1LNode'
    bl_label = 'Neuro Elman 1 Layer'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    Elman = Neuro_Elman(1,5)
    

    def init(self, context):
        self.inputs.new('StringsSocket', "data", "data")
        self.inputs.new('StringsSocket', "etalon", "etalon")
        self.outputs.new('StringsSocket', "result", "result")
        

    def update(self):
        if 'result' in self.outputs and len(self.outputs['result'].links) > 0 \
                and 'data' in self.inputs and len(self.inputs['data'].links) > 0:
            
            if 'etalon' in self.inputs and len(self.inputs['etalon'].links) > 0:
                etalon = SvGetSocketAnyType(self, self.inputs['etalon'])[0][0]
                #print('etalon', etalon)
                flag = True
            else:
                flag = False
                etalon = 0
            
            data = SvGetSocketAnyType(self, self.inputs['data'])
            result = [[self.Elman.neuro(data, etalon, flag)]]
        
        else:
            result = [[]]
            
        #print('result', result)
        SvSetSocketAnyType(self, 'result', result)

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(NeuroElman1LNode)


def unregister():
    bpy.utils.unregister_class(NeuroElman1LNode)

