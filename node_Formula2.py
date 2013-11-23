import bpy
from node_s import *
from util import *
from mathutils import Vector, Matrix
import parser
from math import sin, cos, tan, pi

class Formula2Node(Node, SverchCustomTreeNode):
    ''' Formula2 '''
    bl_idname = 'Formula2Node'
    bl_label = 'Formula2'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    formula = bpy.props.StringProperty(name = 'formula', default='x*n[0]', update=updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, "formula", text="formula")
        
    def init(self, context):
        self.inputs.new('StringsSocket', "X", "X")
        self.inputs.new('StringsSocket', "n[.]", "n[.]")
        self.outputs.new('StringsSocket', "Result", "Result")
   
    def check_slots(self, num):
        l = []
        if len(self.inputs)<num+1:
            return False
        for i, sl in enumerate(self.inputs[num:]):   
            if len(sl.links)==0:
                 l.append(i+num)
        if l:
            return l
        else:
            return False


    def update(self):
        # inputs
        ch = self.check_slots(1)
        if ch:
            for c in ch[:-1]:
                self.inputs.remove(self.inputs[ch[0]])
        
        if 'X' in self.inputs and self.inputs['X'].links: 
            if not self.inputs['X'].node.socket_value_update:
                self.inputs['X'].node.update()
            if type(self.inputs['X'].links[0].from_socket) == StringsSocket:
                vecs = eval(self.inputs['X'].links[0].from_socket.StringsProperty)
            elif type(self.inputs['X'].links[0].from_socket) == VerticesSocket:
                vecs = eval(self.inputs['X'].links[0].from_socket.VerticesProperty)
            elif type(self.inputs['X'].links[0].from_socket) == MatrixSocket:
                vecs = eval(self.inputs['X'].links[0].from_socket.MatrixProperty)
        else:
            vecs = [[0.0]]
        
        list_mult=[]
        for idx, multi in enumerate(self.inputs[1:]):   
            if multi.links and \
                type(multi.links[0].from_socket) == StringsSocket:
                if not multi.node.socket_value_update:
                    multi.node.update()
                
                mult = eval(multi.links[0].from_socket.StringsProperty)
                ch = self.check_slots(2)
                if not ch:
                    self.inputs.new('StringsSocket', 'n[.]', "n[.]")

                list_mult.extend(mult)
        if len(list_mult)==0:
            list_mult= [[0.0]]
            
        # outputs
        if 'Result' in self.outputs and len(self.outputs['Result'].links)>0:
            if not self.outputs['Result'].node.socket_value_update:
               self.outputs['Result'].node.update()
            code_formula = parser.expr(self.formula).compile()
            
            # finding nasty levels, make equal nastyness (canonical 0,1,2,3)
            levels = [levelsOflist(vecs)]
            for n in list_mult:
                levels.append(levelsOflist(n)+1)
            maxlevel = max(max(levels), 3)
            diflevel = maxlevel - levels[0]
            if diflevel:
                vecs_ = dataSpoil(vecs, maxlevel)
                vecs = dataCorrect(vecs_, nominal_dept=2)
            for i, lev in enumerate(levels):
                if i==0: continue
                diflevel = maxlevel-lev
                if diflevel:
                    list_temp = dataSpoil(list_mult[i-1], maxlevel)
                    list_mult[i-1] = dataCorrect(list_temp, nominal_dept=1)
            
            r = self.inte(vecs, code_formula, list_mult, 3)
            
            result = dataCorrect(r, nominal_dept=min((levels[0]-1),2))
            
            self.outputs['Result'].StringsProperty = str(result)
    
    def inte(self, list_x, formula, list_n, levels, index=0):
        ''' calc lists in formula '''
        if not levels:
            
            X = x = list_x
            argumentslist = []
            for exli in list_n:
                argumentslist.append(exli[index])
            #print (x, argumentslist)
            N = n = argumentslist
            t = eval(formula)
        else:
            t = []
            Lennox = len(list_x)
            new_list_n = []
            for j, ne in enumerate(list_n):
                #operate with external lists untill come to float level
                
                if levels in [2,3]:
                    Lenin = len(ne)
                    equal = Lennox - Lenin
                    if equal > 0:
                        ne = self.enlarge(ne, equal)
                elif levels == 1:
                    Lenin = len(ne[0])
                    equal = Lennox - Lenin
                    #print (equal)
                    if equal > 0:
                        ne = self.enlarge(ne[0], equal)
                    else:
                        ne = ne[0]
                new_list_n.append(ne)
            print (new_list_n, list_x)
            for i, item_x in enumerate(list_x):
                pre_t = self.inte(item_x, formula, new_list_n, levels-1, index=i)
                t.append(pre_t)
        return t
    
    def enlarge(self, list, equal):
        ''' enlarge minor n[i] list to size of x list '''
        if equal > 0:
            list.append(list[-1])    
            list = self.enlarge(list, equal-1)
            #print (list, equal)
        return list
            
def register():
    bpy.utils.register_class(Formula2Node)
    
def unregister():
    bpy.utils.unregister_class(Formula2Node)

if __name__ == "__main__":
    register()