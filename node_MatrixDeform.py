import bpy
from node_s import *
from mathutils import *
from util import *

class MatrixDeformNode(Node, SverchCustomTreeNode):
    ''' MatrixDeform '''
    bl_idname = 'MatrixDeformNode'
    bl_label = 'Matrix Deform'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    def init(self, context):
        self.inputs.new('MatrixSocket', "Original", "Original")
        self.inputs.new('VerticesSocket', "Location", "Location")
        self.inputs.new('VerticesSocket', "Scale", "Scale")
        self.inputs.new('VerticesSocket', "Rotation", "Rotation")
        self.inputs.new('StringsSocket', "Angle", "Angle")
        self.outputs.new('MatrixSocket', "Matrix", "Matrix")
        

    def update(self):
        # inputs
        if 'Matrix' in self.outputs and self.outputs['Matrix'].links:
            if self.inputs['Original'].links and \
                type(self.inputs['Original'].links[0].from_socket) == MatrixSocket:

                orig_ = SvGetSocketAnyType(self, self.inputs['Original'])
                orig = Matrix_generate(orig_)
            else:
                return
                
            if 'Location' in self.inputs and self.inputs['Location'].links and \
                type(self.inputs['Location'].links[0].from_socket) == VerticesSocket:

                loc_ = SvGetSocketAnyType(self,self.inputs['Location'])
                loc = Vector_generate(loc_)
            else:
                loc = [[]]
            
            if 'Scale' in self.inputs and self.inputs['Scale'].links and \
                type(self.inputs['Scale'].links[0].from_socket) == VerticesSocket:
   
                scale_ = SvGetSocketAnyType(self,self.inputs['Scale'])
                scale = Vector_generate(scale_)
            else:
                scale = [[]]
                
            if 'Rotation' in self.inputs and self.inputs['Rotation'].links and \
                type(self.inputs['Rotation'].links[0].from_socket) == VerticesSocket:

                rot_ = SvGetSocketAnyType(self,self.inputs['Rotation'])
                rot = Vector_generate(rot_)
                #print ('matrix_def', str(rot_))
            else:
                rot = [[]]
            
            rotA=[[]]
            angle = [[0.0]]
            if 'Angle' in self.inputs and self.inputs['Angle'].links:
     
                if type(self.inputs['Angle'].links[0].from_socket) == StringsSocket:
                    angle = SvGetSocketAnyType(self,self.inputs['Angle'])
                    
                elif type(self.inputs['Angle'].links[0].from_socket) == VerticesSocket:
                    rotA_ = SvGetSocketAnyType(self,self.inputs['Angle'])
                    rotA = Vector_generate(rotA_)
            
            # outputs
            #print(loc)
            matrixes_ = matrixdef(orig, loc, scale, rot, angle, rotA)
            matrixes = Matrix_listing(matrixes_)
            SvSetSocketAnyType(self, 'Matrix', matrixes)
            #print ('matrix_def', str(matrixes))
    
                
    def update_socket(self, context):
        updateNode(self,context)


    

def register():
    bpy.utils.register_class(MatrixDeformNode)
    
def unregister():
    bpy.utils.unregister_class(MatrixDeformNode)

if __name__ == "__main__":
    register()
