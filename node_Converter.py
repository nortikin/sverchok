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
            
            if type(self.inputs['data'].links[0].from_socket) == VerticesSocket:
                out = self.inputs['data'].links[0].from_socket.VerticesProperty
            if type(self.inputs['data'].links[0].from_socket) == StringsSocket:
                out = self.inputs['data'].links[0].from_socket.StringsProperty
            if type(self.inputs['data'].links[0].from_socket) == MatrixSocket:
                out = self.inputs['data'].links[0].from_socket.MatrixProperty

            if len(self.outputs['vertices'].links)>0:
                if not self.outputs['vertices'].node.socket_value_update:
                    self.outputs['vertices'].node.update()
                self.outputs['vertices'].links[0].from_socket.VerticesProperty = out
            if len(self.outputs['data'].links)>0:
                if not self.outputs['data'].node.socket_value_update:
                    self.outputs['data'].node.update()
                self.outputs['data'].links[0].from_socket.StringsProperty = out
            if len(self.outputs['matrix'].links)>0:
                if not self.outputs['matrix'].node.socket_value_update:
                    self.outputs['matrix'].node.update()
                self.outputs['matrix'].links[0].from_socket.MatrixProperty = out

def register():
    bpy.utils.register_class(ConverterNode)
    
def unregister():
    bpy.utils.unregister_class(ConverterNode)

if __name__ == "__main__":
    register()