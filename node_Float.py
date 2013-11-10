import bpy
from node_s import *
from util import *

class FloatNode(Node, SverchCustomTreeNode):
    ''' Float '''
    bl_idname = 'FloatNode'
    bl_label = 'Float'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    float_ = bpy.props.FloatProperty(name = 'float_', description='float number', default=1.0, options={'ANIMATABLE'}, update=updateNode)
    
    def init(self, context):
        self.inputs.new('StringsSocket', "Float", "Float")
        self.outputs.new('StringsSocket', "Float", "Float")
    
    def draw_buttons(self, context, layout):
        layout.prop(self, "float_", text="float")

    def update(self):
        # inputs
        if len(self.inputs['Float'].links)>0:
            if not self.inputs['Float'].node.socket_value_update:
                self.inputs['Float'].node.update()
            Float = eval(self.inputs['Float'].links[0].from_socket.StringsProperty)[0][0]
        else:
            Float = self.float_
        
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