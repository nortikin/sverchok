import bpy
from node_s import *
from mathutils import *
import math
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
             
                
            if ('Rotation' in self.outputs and self.outputs['Rotation'].links ) \
                or ('Angle' in self.outputs and self.outputs['Angle'].links):
                if not self.outputs['Angle'].node.socket_value_update:
                    self.outputs['Angle'].node.update()
                if not self.outputs['Angle'].node.socket_value_update:
                    self.outputs['Angle'].node.update()    
                locs = Matrix_rotation(matrixes, list=True)
                rots = []
                angles = []
                for lists in locs:
                    for pair in lists:
                        rots.append(pair[0])
                        angles.append(round(math.degrees(pair[1]),7))
                self.outputs['Rotation'].VerticesProperty = str([rots,])
# this should be updated to handle new numbernode formats. but so should the rest this file.
                self.outputs['Angle'].StringsProperty = str([angles ])

                   
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