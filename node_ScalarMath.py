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
from node_s import *
from util import *
from mathutils import Vector, Matrix
from math import *



class ScalarMathNode(Node, SverchCustomTreeNode):
    ''' ScalarMathNode '''
    bl_idname = 'ScalarMathNode'
    bl_label = 'function'
    bl_icon = 'OUTLINER_OB_EMPTY'
 

# Math functions from http://docs.python.org/3.3/library/math.html
# maybe this should be distilled to most common with the others available via Formula2 Node
    
    mode_items = [
        ("SINE",            "Sine",         ""),
        ("COSINE",          "Cosine",       ""),
        ("TANGENT",         "Tangent",      ""),
        ("ARCSINE",         "Arcsine",      ""),
        ("ARCCOSINE",       "Arccosine",    ""),
        ("ARCTANGENT",      "Arctangent",   ""),
        ("SQRT",            "Squareroot",   ""),
        ("NEG",             "Negate",       ""),
        ("DEGREES",         "Degrees",      ""),
        ("RADIANS",         "Radians",      ""),
        ("ABS",             "Absolute",     ""),
        ("CEIL",            "Ceiling",      ""),
        ("ROUND",           "Round",        ""), 
        ("ROUND-N",         "Round N",      ""),
        ("FMOD",            "Fmod",         ""),
        ("MODULO",          "modulo",       ""),     
        ("FLOOR",           "floor",        ""),
        ("EXP",             "Exponent",     ""),
        ("LN",              "log",          ""),
        ("LOG1P",           "log1p",        ""),
        ("LOG10",           "log10",        ""),
        ("ACOSH",           "acosh",        ""),
        ("ASINH",           "asinh",        ""),
        ("ATANH",           "atanh",        ""),
        ("COSH",            "cosh",         ""),
        ("SINH",            "sinh",         ""),
        ("TANH",            "tanh",         ""),
        ("ADD",              "+",           ""),
        ("SUB",              "-",           ""),
        ("MUL",              "*",           ""),
        ("DIV",              "/",           ""),  
        ("INTDIV",           "//",          ""),        
        ("POW",              "**",          ""),  
        ("PI",               "pi",          ""),
        ("E",                "e",           ""), 
        ("PHI",              "phi",         ""),
        ("MIN",              "min",         ""),
        ("MAX",              "max",         ""),    
        ]
        
    fx = {
        'SINE':       sin,
        'COSINE':     cos,
        'TANGENT':    tan,
        'ARCSINE':    asin,
        'ARCCOSINE':  acos,
        'ARCTANGENT': atan,
        'SQRT':       lambda x: sqrt(fabs(x)),
        'NEG':        lambda x: -x,
        'DEGREES':    degrees,
        'RADIANS':    radians,
        'ABS':        fabs,
        'FLOOR':      floor,
        'CEIL':       ceil,
        'EXP':        exp,
        'LN':         log,
        'LOG1P':      log1p,
        'LOG10':      log10,
        'ACOSH':      acosh,
        'ASINH':      asinh,
        'COSH':       cosh,
        'SINH':       sinh,
        'TANH':       tanh,
        'ROUND':      round  
    }
    
    fxy = {
        'ADD':      lambda x,y : x+y,
        'SUB':      lambda x,y : x-y,
        'DIV':      lambda x,y : x/y,
        'INTDIV':   lambda x,y : x//y,
        'MUL':      lambda x,y : x*y,
        'POW':      lambda x,y : x**y,
        'ROUND-N':  lambda x,y : round(x,y),
        'FMOD':     lambda x,y : fmod(x,y),
        'MODULO':   lambda x,y : x%y,
        'MIN':      lambda x,y : min(x,y),
        'MAX':      lambda x,y : max(x,y)                     
    }
    
    constant = {
        'PI':       pi,
        'E':        e,
        'PHI':      1.61803398875, 
    }       
        
    items_=bpy.props.EnumProperty( items = mode_items, name="Function", 
            description="Function choice", default="SINE", update=updateNode)
    
    def draw_buttons(self, context, layout):
        layout.prop(self,"items_","Functions:");

    def init(self, context):
        self.inputs.new('StringsSocket', "X", "x")        
        self.outputs.new('StringsSocket', "float", "out")
        

    def update(self):
                   
        # inputs
        nrInputs = 1
        if self.items_ in self.constant:
            nrInputs = 0
        elif self.items_ in self.fx:
            nrInputs = 1
        elif self.items_ in self.fxy:
            nrInputs = 2
                
        self.set_inputs(nrInputs)
        
        self.label=self.items_
        
        
        if 'X' in self.inputs and len(self.inputs['X'].links)>0 and \
            type(self.inputs['X'].links[0].from_socket) == StringsSocket:
            if not self.inputs['X'].node.socket_value_update:
                self.inputs['X'].node.update()
            Number1 = self.inputs['X'].links[0].from_socket.StringsProperty
        else:
            Number1 = []
        
        if 'Y' in self.inputs and len(self.inputs['Y'].links)>0 and \
            type(self.inputs['Y'].links[0].from_socket) == StringsSocket:
            if not self.inputs['Y'].node.socket_value_update:
                self.inputs['Y'].node.update()
            Number2 = self.inputs['Y'].links[0].from_socket.StringsProperty
        else:   
            Number2 = []
                   
        # outputs
        if 'float' in self.outputs and len(self.outputs['float'].links)>0:
            if not self.outputs['float'].node.socket_value_update:
                self.outputs['float'].node.update()
            result = []
            if nrInputs == 0:
                result = [self.constant[self.items_]]
            if nrInputs == 1:
                if len(Number1):
                    x = eval(Number1)
                    result = self.recurse_fx(x,self.fx[self.items_])
            if nrInputs == 2:
                if len(Number1) and len(Number2):
                    x = eval(Number1)
                    y = eval(Number2)
                    result = self.recurse_fxy(x,y,self.fxy[self.items_])
                      
            self.outputs['float'].StringsProperty = str(result)
    
    def set_inputs(self,n):
        if n == len(self.inputs):
            return
        if n < len(self.inputs):
            while n < len(self.inputs):
                self.inputs.remove(self.inputs[-1])
        if n > len(self.inputs):
            if not 'X' in self.inputs:
                self.inputs.new('StringsSocket', "X", "x")        
            if not 'Y' in self.inputs:
                self.inputs.new('StringsSocket', "Y", "y")

# apply f to all values recursively  
        
    def recurse_fx(self, l,f):
        if type(l) == int or type(l) == float:
            t = f(l)
        else:
            t = []
            for i in l:
                i = self.recurse_fx(i,f)
                t.append(i)
        return t
        
# match length of lists, 
# cases
# [1,2,3] + [1,2,3] -> [2,4,6]
# [1,2,3] + 1 -> [2,3,4]
# [1,2,3] + [1,2] -> [2,4,5] , list is expanded to match length, [-1] is repeated
# odd cases too.
# [1,2,[1,1,1]] + [[1,2,3],1,2] -> [[2,3,4],3,[3,3,3]]
 
    def recurse_fxy(self,l1, l2, f):
        if (type(l1) is int or type(l1) is float) and \
           (type(l2) is int or type(l2) is float):
                return f(l1,l2)
        if type(l1) is list and type (l2) is list:
            max_obj = max(len(l1),len(l2)) 
            fullList(l1,max_obj)
            fullList(l2,max_obj)    
            res = []
        
            for i in range(len(l1)):
                res.append( self.recurse_fxy(l1[i], l2[i],f))
            return res    
        if type(l1) is list and (type(l2) is float or type(l2) is int):
            return self.recurse_fxy(l1,[l2],f)
        if type(l2) is list and (type(l1) is float or type(l1) is int):
            return self.recurse_fxy([l1],l2,f)
            
    def update_socket(self, context):
        self.update()        
    


def register():
    bpy.utils.register_class(ScalarMathNode)
    
def unregister():
    bpy.utils.unregister_class(ScalarMathNode)

if __name__ == "__main__":
    register()