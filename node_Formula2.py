import bpy
from node_s import *
from util import *
from mathutils import Vector, Matrix
import parser
from math import *

class Formula2Node(Node, SverchCustomTreeNode):
    ''' Formula2 '''
    bl_idname = 'Formula2Node'
    bl_label = 'Formula2'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    formula = bpy.props.StringProperty(name = 'formula', default='x+n[0]', update=updateNode)
    typ = bpy.props.StringProperty(name='typ', default='')
    newsock = bpy.props.BoolProperty(name='newsock', default=False)

    def draw_buttons(self, context, layout):
        layout.prop(self, "formula", text="formula")
        
    def init(self, context):
        self.inputs.new('StringsSocket', "X", "X")
        self.inputs.new('StringsSocket', "n[.]", "n[.]")
        self.outputs.new('StringsSocket', "Result", "Result")
        
    def check_slots(self, num):
        l = []
        if len(self.inputs) <= num:
            return False
        for i, sl in enumerate(self.inputs[num:]):   
            if len(sl.links) == 0:
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
                self.inputs.remove(self.inputs[ch[-1]])
        
        list_mult=[]
        for idx, multi in enumerate(self.inputs[1:]):   
            if multi.links:
                list_mult.extend(SvGetSocketAnyType(self, multi))
                ch = self.check_slots(2)
        if not ch:
            self.inputs.new('StringsSocket', 'n[.]', "n[.]")
        
        if len(list_mult)==0:
            list_mult= [[0.0]]
            
        if 'X' in self.inputs and len(self.inputs['X'].links)>0:
            # адаптивный сокет
            inputsocketname = 'X'
            outputsocketname = ['Result']
            changable_sockets(self, inputsocketname, outputsocketname)
            vecs = SvGetSocketAnyType(self, self.inputs['X'])
        else:
            vecs = [[0.0]]
            
        # outputs
        if 'Result' in self.outputs and len(self.outputs['Result'].links)>0:
            code_formula = parser.expr(self.formula).compile()
            
            # finding nasty levels, make equal nastyness (canonical 0,1,2,3)
            levels = [levelsOflist(vecs)]
            for n in list_mult:
                levels.append(levelsOflist(n))
            maxlevel = max(max(levels), 3)
            diflevel = maxlevel - levels[0]
            
            if diflevel:
                vecs_ = dataSpoil([vecs], diflevel-1)
                vecs = dataCorrect(vecs_, nominal_dept=2)
            for i, lev in enumerate(levels):
                if i==0: continue
                diflevel = maxlevel-lev
                if diflevel:
                    list_temp = dataSpoil([list_mult[i-1]], diflevel-1)
                    list_mult[i-1] = dataCorrect(list_temp, nominal_dept=2)
            r = self.inte(vecs, code_formula, list_mult, 3)
            result = dataCorrect(r, nominal_dept=min((levels[0]-1),2))
            
            SvSetSocketAnyType(self, 'Result', result)
    
    def inte(self, list_x, formula, list_n, levels, index=0):
        ''' calc lists in formula '''
        out = []
        new_list_n = self.normalize(list_n, list_x)
        for j, x_obj in enumerate(list_x):
            out1 = []
            for k, x_lis in enumerate(x_obj):
                out2 = []
                for q, x in enumerate(x_lis):
                    out2.append(self.calc_item(x, formula, new_list_n, j, k, q))
                out1.append(out2)
            out.append(out1)
        return out
    
    def calc_item(self, x, formula, nlist, j, k, q):
        X = x
        n = []
        a = []
        list_vars = [w for w in sv_Vars.keys()]
        for v in list_vars:
            if v[:6]=='sv_typ': continue
            abra = sv_Vars[v]
            exec(str(v)+'=[]')
            for i, aa_abra in enumerate(abra):
                eva = str(v)+'.append('+str(aa_abra)+')'
                eval(eva)
        
        for nitem in nlist:
            n.append(nitem[j][k][q])
        N = n
        return eval(formula)
    
    def normalize(self, listN, listX):
        Lennox = len(listX)
        new_list_n = []
        for ne in listN:
            Lenin = len(ne)
            equal = Lennox - Lenin
            if equal > 0:
                ne = self.enlarge(ne, equal)
            for i, obj in enumerate(listX):
                Lennox = len(obj)
                Lenin = len(ne[i])
                equal = Lennox - Lenin
                if equal > 0:
                    ne[i] = self.enlarge(ne[i], equal)
                for j, list in enumerate(obj):
                    Lennox = len(list)
                    Lenin = len(ne[i][j])
                    equal = Lennox - Lenin 
                    if equal > 0:
                        ne[i][j] = self.enlarge(ne[i][j], equal)
                
            new_list_n.append(ne)
        return new_list_n
    
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