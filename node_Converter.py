import bpy
from node_s import *
from util import *


class ConverterNode(Node, SverchCustomTreeNode):
    ''' Converter node temporery solution '''
    bl_idname = 'ConverterNode'
    bl_label = 'Converter'
    bl_icon = 'OUTLINER_OB_EMPTY'
        
    def init(self, context):
        self.inputs.new('StringsSocket', "data", "data")
        self.outputs.new('VerticesSocket', 'vertices', 'vertices')
        self.outputs.new('StringsSocket', 'data', 'data')
        self.outputs.new('MatrixSocket', 'matrix', 'matrix')
    
    def draw_buttons(self, context, layout):
        pass
    
    
    def update(self):
        if 'vertices' in self.outputs and self.outputs['vertices'].links or \
            'data' in self.outputs and self.outputs['data'].links or \
            'matrix' in self.outputs and  self.outputs['matrix'].links:
            
            out = SvGetSocketAnyType(self,self.inputs['data'])

            if self.outputs['vertices'].links:
                SvSetSocketAnyType(self, 'vertices', out)
            if self.outputs['data'].links:
                SvSetSocketAnyType(self, 'data', out)
            if self.outputs['matrix'].links:
                SvSetSocketAnyType(self, 'matrix', out)

def register():
    bpy.utils.register_class(ConverterNode)
    
def unregister():
    bpy.utils.unregister_class(ConverterNode)

if __name__ == "__main__":
    register()