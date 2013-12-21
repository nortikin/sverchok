import bpy
from node_s import *
from mathutils import *
from util import *

class MatrixApplyNode(Node, SverchCustomTreeNode):
    ''' Multiply vectors on matrixes with several objects in output '''
    bl_idname = 'MatrixApplyNode'
    bl_label = 'Apply matrix for vectors'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    def init(self, context):
        self.inputs.new('VerticesSocket', "Vectors", "Vectors")
        self.inputs.new('MatrixSocket', "Matrixes", "Matrixes")
        
        self.outputs.new('VerticesSocket', "Vectors", "Vectors")
        

    def update(self):
        # inputs
        if 'Vectors' in self.outputs and len(self.outputs['Vectors'].links)>0:
            if self.inputs['Vectors'].links and \
                    type(self.inputs['Vectors'].links[0].from_socket) == VerticesSocket \
                    and self.inputs['Matrixes'] and \
                    type(self.inputs['Matrixes'].links[0].from_socket) == MatrixSocket:
                if not self.inputs['Vectors'].node.socket_value_update:
                    self.inputs['Vectors'].node.update()
                vecs_ = eval(self.inputs['Vectors'].links[0].from_socket.VerticesProperty)
                vecs = Vector_generate(vecs_)
                #print (vecs)
                if not self.inputs['Matrixes'].node.socket_value_update:
                    self.inputs['Matrixes'].node.update()
                mats_ = eval(self.inputs['Matrixes'].links[0].from_socket.MatrixProperty)
                mats = Matrix_generate(mats_)
            else:
                vecs = [[]]
                mats = [Matrix()]
            
            # outputs
        
            if not self.outputs['Vectors'].node.socket_value_update:
                self.outputs['Vectors'].node.update()
            
            vectors_ = self.vecscorrect(vecs, mats)
            vectors = Vector_degenerate(vectors_)
            self.outputs['Vectors'].VerticesProperty = str(vectors)
            
    
    def vecscorrect(self, vecs, mats):
        out = []
        lengthve = len(vecs)-1
        for i, m in enumerate(mats):
            out_ = []
            k = i
            if k > lengthve:
                k = lengthve 
            for v in vecs[k]:
                out_.append(m*v)
            out.append(out_)
        return out
                
    def update_socket(self, context):
        updateNode(self,context)


    

def register():
    bpy.utils.register_class(MatrixApplyNode)
    
def unregister():
    bpy.utils.unregister_class(MatrixApplyNode)

if __name__ == "__main__":
    register()