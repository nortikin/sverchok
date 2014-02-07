import bpy
from node_s import *
from util import *

class VectorsOutNode(Node, SverchCustomTreeNode):
    ''' Vectors out '''
    bl_idname = 'VectorsOutNode'
    bl_label = 'Vectors out'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    def init(self, context):
        self.inputs.new('VerticesSocket', "Vectors", "Vectors")
        self.outputs.new('StringsSocket', "X", "X")
        self.outputs.new('StringsSocket', "Y", "Y")
        self.outputs.new('StringsSocket', "Z", "Z")
        
    def update(self):
        # inputs
        X, Y, Z = [], [], []
        if 'Vectors' in self.inputs and self.inputs['Vectors'].is_linked:
            xyz = SvGetSocketAnyType(self,self.inputs['Vectors'])
            
            data = dataCorrect(xyz) # 
            #print (data)
            X,Y,Z = [],[],[]
            for obj in data:
                for item in obj:
                    X.append(item[0]) 
                    Y.append(item[1]) 
                    Z.append(item[2]) 
                    
            for i,name in enumerate(['X','Y','Z']):
                if self.outputs[name].is_linked:
                    SvSetSocketAnyType(self,name,[[X,Y,Z][i]])
                            
    def update_socket(self, context):
        self.update()

def register():
    bpy.utils.register_class(VectorsOutNode)
    
def unregister():
    bpy.utils.unregister_class(VectorsOutNode)

if __name__ == "__main__":
    register()