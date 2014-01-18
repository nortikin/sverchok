import bpy
from node_s import *
from util import *


class VariableNode(Node, SverchCustomTreeNode):
    ''' Variable '''
    bl_idname = 'VariableNode'
    bl_label = 'Variable'
    bl_icon = 'OUTLINER_OB_EMPTY'
        
    def init(self, context):
        self.inputs.new('StringsSocket', "a[0]", "a[0]")
        
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
        global sv_Vars
        # inputs
        ch = self.check_slots(0)
        if ch:
            for c in ch[:-1]:
                self.inputs.remove(self.inputs[ch[-1]])
        
        list_mult=[]
        for idx, multi in enumerate(self.inputs):   
            if multi.links:
                ch = self.check_slots(1)
                if not ch:
                    a_name = 'a['+str(len(self.inputs))+']'
                    self.inputs.new('StringsSocket', a_name, a_name)
        
        list_vars = []
        for idx, multi in enumerate(self.inputs): 
            a_name = 'a['+str(idx)+']'
            if multi.links:
                if type(multi.links[0].from_socket) == StringsSocket:
                    mult = eval(multi.links[0].from_socket.StringsProperty)
                elif type(multi.links[0].from_socket) == VerticesSocket:
                    mult = eval(multi.links[0].from_socket.VerticesProperty)
                elif type(multi.links[0].from_socket) == MatrixSocket:
                    mult = eval(multi.links[0].from_socket.MatrixProperty)
            else:
                mult = [[0.0]]
            
            list_vars.append(mult)
        
        sv_Vars[self.name] = list_vars
        #print('list_vars',list_vars)
     
     
def register():
    bpy.utils.register_class(VariableNode)
    
def unregister():
    bpy.utils.unregister_class(VariableNode)

if __name__ == "__main__":
    register()