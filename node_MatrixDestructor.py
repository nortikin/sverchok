import bpy
from node_s import *
from mathutils import *
from math import degrees
from util import *

class MatrixOutNode(Node, SverchCustomTreeNode):
    ''' Matrix Destructor '''
    bl_idname = 'MatrixOutNode'
    bl_label = 'Matrix out'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    def init(self, context):
        self.outputs.new('VerticesSocket', "Location", "Location")
        self.outputs.new('VerticesSocket', "Scale", "Scale")
        self.outputs.new('VerticesSocket', "Rotation", "Rotation")
        self.outputs.new('StringsSocket', "Angle", "Angle") 
        self.inputs.new('MatrixSocket', "Matrix", "Matrix")
        

    def update(self):
        if 'Matrix' in self.inputs and self.inputs['Matrix'].links:
            matrixes_ = SvGetSocketAnyType(self,self.inputs['Matrix'])
            matrixes = Matrix_generate(matrixes_)
            
            if 'Location' in self.outputs and self.outputs['Location'].links:
                locs = Matrix_location(matrixes, list=True)
                SvSetSocketAnyType(self, 'Location', locs)
                
            
            if 'Scale' in self.outputs and self.outputs['Scale'].links:
      
                locs = Matrix_scale(matrixes, list=True)
                SvSetSocketAnyType(self,'Scale', locs)
             
                
            if ('Rotation' in self.outputs and self.outputs['Rotation'].links ) \
                or ('Angle' in self.outputs and self.outputs['Angle'].links):
               
                locs = Matrix_rotation(matrixes, list=True)
                rots = []
                angles = []
                for lists in locs:
                    rots.append([pair[0] for pair in lists])
                    for pair in lists:
                        angles.append(degrees(pair[1]))
                SvSetSocketAnyType(self, 'Rotation',rots)
                SvSetSocketAnyType(self, 'Angle',[angles])
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
