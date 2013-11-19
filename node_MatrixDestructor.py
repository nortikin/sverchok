import bpy
from node_s import *
from mathutils import *
from util import *

class MatrixOutNode(Node, SverchCustomTreeNode):
    ''' Matrix Destructor '''
    bl_idname = 'MatrixOutNode'
    bl_label = 'Matrix out'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    def init(self, context):
        self.outputs.new('VerticesSocket', "Location", "Location")
        self.outputs.new('VerticesSocket', "Scale", "Scale")
        self.inputs.new('MatrixSocket', "Matrix", "Matrix")
        

    def update(self):
        if self.inputs['Matrix'].links:
            if not self.inputs['Matrix'].node.socket_value_update:
                self.inputs['Matrix'].node.update()
            matrixes_ = eval(self.inputs['Matrix'].links[0].from_socket.MatrixProperty)
            matrixes = Matrix_generate(matrixes_)
            
            if 'Location' in self.outputs and self.outputs['Location'].links:
                if not self.outputs['Location'].node.socket_value_update:
                    self.outputs['Location'].node.update()
                locs = Matrix_location(matrixes, list=True)
                self.outputs['Location'].VerticesProperty = str(locs)
                
            
            if 'Scale' in self.outputs and self.outputs['Scale'].links:
                if not self.outputs['Scale'].node.socket_value_update:
                    self.outputs['Scale'].node.update()
                locs = Matrix_scale(matrixes, list=True)
                self.outputs['Scale'].VerticesProperty = str(locs)
        else:
            matrixes = [[]]
    def update_socket(self, context):
        self.update()


    

def register():
    bpy.utils.register_class(MatrixOutNode)
    
def unregister():
    bpy.utils.unregister_class(MatrixOutNode)

if __name__ == "__main__":
    register()