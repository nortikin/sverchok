import bpy
from node_s import *

class FloatNode(Node, SverchCustomTreeNode):
    ''' Float '''
    bl_idname = 'FloatNode'
    bl_label = 'Float'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    def init(self, context):
        self.inputs.new('NodeSocketFloat', "Float", "Float").default_value = 10
        self.outputs.new('StringsSocket', "Float", "Float")
        

    def update(self):
        # inputs
        if len(self.inputs['Float'].links)>0 and type(self.inputs['Float'].links[0].from_socket) == bpy.types.NodeSocketFloat:
            if not self.inputs['Float'].node.socket_value_update:
                self.inputs['Float'].node.update()
            Float = self.inputs['Float'].links[0].from_socket.default_value
        else:
            Float = self.inputs['Float'].default_value
        
        # outputs
        if 'Float' in self.outputs and len(self.outputs['Float'].links)>0:
            if not self.outputs['Float'].node.socket_value_update:
                self.inputs['Float'].node.update()
            
            self.outputs['Float'].StringsProperty = str([[Float, ]])
    
    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(FloatNode)
    
def unregister():
    bpy.utils.unregister_class(FloatNode)

if __name__ == "__main__":
    register()