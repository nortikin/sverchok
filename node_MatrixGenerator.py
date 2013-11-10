import bpy
from node_s import *
from mathutils import *
from util import *

class MatrixGenNode(Node, SverchCustomTreeNode):
    ''' MatrixGenerator '''
    bl_idname = 'MatrixGenNode'
    bl_label = 'Matrix in'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    def init(self, context):
        self.inputs.new('VerticesSocket', "Location", "Location")
        self.inputs.new('VerticesSocket', "Scale", "Scale")
        self.inputs.new('VerticesSocket', "Rotation", "Rotation")
        self.inputs.new('StringsSocket', "Angle", "Angle")
        self.outputs.new('MatrixSocket', "Matrix", "Matrix")
        

    def update(self):
        # inputs
            if 'Location' in self.inputs and self.inputs['Location'].links and \
                type(self.inputs['Location'].links[0].from_socket) == VerticesSocket:
                if not self.inputs['Location'].node.socket_value_update:
                    self.inputs['Location'].node.update()
                loc_ = eval(self.inputs['Location'].links[0].from_socket.VerticesProperty)
                loc = Vector_generate(loc_)
            else:
                loc = [[]]
            
            if 'Scale' in self.inputs and self.inputs['Scale'].links and \
                type(self.inputs['Scale'].links[0].from_socket) == VerticesSocket:
                if not self.inputs['Scale'].node.socket_value_update:
                    self.inputs['Scale'].node.update()
                scale_ = eval(self.inputs['Scale'].links[0].from_socket.VerticesProperty)
                scale = Vector_generate(scale_)
            else:
                scale = [[]]
                
            if 'Rotation' in self.inputs and self.inputs['Rotation'].links and \
                type(self.inputs['Rotation'].links[0].from_socket) == VerticesSocket:
                if not self.inputs['Rotation'].node.socket_value_update:
                    self.inputs['Rotation'].node.update()
                rot_ = eval(self.inputs['Rotation'].links[0].from_socket.VerticesProperty)
                rot = Vector_generate(rot_)
                #print ('matrix_def', str(rot_))
            else:
                rot = [[]]
            
            rotA=[[]]
            angle = [[0.0]]
            if 'Angle' in self.inputs and self.inputs['Angle'].links:
                if not self.inputs['Angle'].node.socket_value_update:
                        self.inputs['Angle'].node.update()
                if type(self.inputs['Angle'].links[0].from_socket) == StringsSocket:
                    angle = eval(self.inputs['Angle'].links[0].from_socket.StringsProperty)
                    
                elif type(self.inputs['Angle'].links[0].from_socket) == VerticesSocket:
                    rotA_ = eval(self.inputs['Angle'].links[0].from_socket.VerticesProperty)
                    rotA = Vector_generate(rotA_)
            
            # outputs
        
            if not self.outputs['Matrix'].node.socket_value_update:
                self.outputs['Matrix'].node.update()
            
            max_l = max(len(loc[0]), len(scale[0]), len(rot[0]), len(angle[0]), len(rotA[0]))
            orig = []
            for l in range(max_l):
                M = mathutils.Matrix()
                orig.append(M)
            if len(orig)==0:
                return
            
            matrixes_ = matrixdef(orig, loc, scale, rot, angle, rotA)
            matrixes = Matrix_listing(matrixes_)
            self.outputs['Matrix'].MatrixProperty = str(matrixes)
            #print ('matrix_def', str(matrixes))
    
                
    def update_socket(self, context):
        self.update()


    

def register():
    bpy.utils.register_class(MatrixGenNode)
    
def unregister():
    bpy.utils.unregister_class(MatrixGenNode)

if __name__ == "__main__":
    register()