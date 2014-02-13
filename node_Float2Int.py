import bpy
from node_s import *
from util import *

class Float2IntNode(Node, SverchCustomTreeNode):
    ''' Float2Int '''
    bl_idname = 'Float2IntNode'
    bl_label = 'Float2int'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    def init(self, context):
        self.inputs.new('StringsSocket', "float", "float")
        self.outputs.new('StringsSocket', "int", "int")
        

    def update(self):
        # inputs
        if 'float' in self.inputs and self.inputs['float'].links and \
             type(self.inputs['float'].links[0].from_socket) == StringsSocket:

            Number = SvGetSocketAnyType(self,self.inputs['float'])
        else:
            Number = []
        
        # outputs
        if 'int' in self.outputs and self.outputs['int'].links:
            result = self.inte(Number)
            SvSetSocketAnyType(self,'int',result)
    
    def update_socket(self, context):
        self.update()
    
    def inte(self, l):
        if type(l) == int or type(l) == float:
            return round(l)
        else:
            return [self.inte(i) for i in l]
       
            
    
    def levels(self, list):
        level = 1
        for n in list:
            if type(n) == list:
                level += self.levels(n)
            return level


def register():
    bpy.utils.register_class(Float2IntNode)
    
def unregister():
    bpy.utils.unregister_class(Float2IntNode)

if __name__ == "__main__":
    register()
