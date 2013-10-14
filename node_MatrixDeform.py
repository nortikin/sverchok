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
        self.inputs.new('MatrixSocket', "Rotation", "Rotation")
        self.outputs.new('MatrixSocket', "Matrix", "Matrix")
        

    def update(self):
        # inputs
        if self.inputs['Original'].links and \
            type(self.inputs['Original'].links[0].from_socket) == MatrixSocket:
            if not self.inputs['Original'].node.socket_value_update:
                self.inputs['Original'].node.update()
            orig_ = eval(self.inputs['Original'].links[0].from_socket.MatrixProperty)
            orig = Matrix_generate(orig_)
        else:
            return
            
        if self.inputs['Location'].links and \
            type(self.inputs['Location'].links[0].from_socket) == VerticesSocket:
            if not self.inputs['Location'].node.socket_value_update:
                self.inputs['Location'].node.update()
            loc_ = eval(self.inputs['Location'].links[0].from_socket.VerticesProperty)
            loc = Vector_generate(loc_)
        else:
            loc = []
        
        if self.inputs['Scale'].links and \
            type(self.inputs['Scale'].links[0].from_socket) == VerticesSocket:
            if not self.inputs['Scale'].node.socket_value_update:
                self.inputs['Scale'].node.update()
            scale_ = eval(self.inputs['Scale'].links[0].from_socket.VerticesProperty)
            scale = Vector_generate(scale_)
        else:
            scale = []
            
        if self.inputs['Rotation'].links and \
            type(self.inputs['Rotation'].links[0].from_socket) == MatrixSocket:
            if not self.inputs['Rotation'].node.socket_value_update:
                self.inputs['Rotation'].node.update()
            rot_ = eval(self.inputs['Rotation'].links[0].from_socket.MatrixProperty)
            rot = Matrix_generate(rot_)
            #print ('matrix_def', str(rot_))
        else:
            rot = []
        
        # outputs
        if 'Matrix' in self.outputs and len(self.outputs['Matrix'].links)>0:
            if not self.outputs['Matrix'].node.socket_value_update:
                self.outputs['Matrix'].node.update()
            
            matrixes_ = self.matrixdef(orig, loc, scale, rot)
            matrixes = Matrix_listing(matrixes_)
            self.outputs['Matrix'].MatrixProperty = str(matrixes)
            #print ('matrix_def', str(matrixes))
    
    def matrixdef(self, orig, loc, scale, rot):
        modif = []
        for i, de in enumerate(orig):
            ma = de
            if scale:
                k = min(len(scale)-1,i)
                scale2=scale[0][k]
                for j in range(4):
                    kk=min(j,2)
                    ma[j][j] = ma[j][j] * scale2[kk]
            if rot:
                k = i
                #print (de, rot[k])
                if k >= len(rot):
                    k = len(rot) - 1
                ma = ma * rot[k]
                #ma = de.lerp(rot[k],10.0)    # * orig[i]
                #ma.to_3x3().rotate(rot[k])
                print ('scal' + str(scale) + 'oldmat'  +  str(de) + 'rot' + str(rot[k]))
                
            if loc:
                k = i
                if k >= len(loc[0]):
                    k = len(loc[0]) -1
                ma.translation = loc[0][k]
            modif.append(ma)
        return modif
                
    def update_socket(self, context):
        self.update()


    

def register():
    bpy.utils.register_class(MatrixDeformNode)
    
def unregister():
    bpy.utils.unregister_class(MatrixDeformNode)

if __name__ == "__main__":
    register()