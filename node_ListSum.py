import bpy, bmesh, mathutils
from mathutils import Vector, Matrix
from node_s import *
from util import *

class ListSumNode(Node, SverchCustomTreeNode):
    ''' List summa WIP, not ready yet '''
    bl_idname = 'ListSumNode'
    bl_label = 'List summa'
    bl_icon = 'OUTLINER_OB_EMPTY'
        
        
    def init(self, context):
        self.inputs.new('StringsSocket', "Data", "Data")
        self.outputs.new('StringsSocket',"Sum","Sum")

    def update(self):
        # достаём два слота - вершины и полики
        if 'Sum' in self.outputs and self.outputs['Sum'].links:
            if 'Data' in self.inputs and self.inputs['Data'].links:
                data = SvGetSocketAnyType(self,self.inputs['Data'])
                    
                out_ = self.summ(data)
                #    print(out_)
                out = [[sum(out_)]]

                SvSetSocketAnyType(self,'Sum', out)
            
    def summ(self, data):
        out = []
        
        if data[0] and (type(data[0]) in [type(1.2), type(1)]):
            for obj in data:
                out.append(obj)
            #print (data)
        elif data[0] and (type(data[0]) in [tuple, list]):
            for obj in data:
                out.extend(self.summ(obj))
        return out
            

    def update_socket(self, context):
        self.update()

def register():
    bpy.utils.register_class(ListSumNode)   
    
def unregister():
    bpy.utils.unregister_class(ListSumNode)

if __name__ == "__main__":
    register()