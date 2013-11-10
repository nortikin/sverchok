import bpy
from node_s import *
from util import *

class IntegerNode(Node, SverchCustomTreeNode):
    ''' Integer '''
    bl_idname = 'IntegerNode'
    bl_label = 'Integer'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    int_ = bpy.props.IntProperty(name = 'int_', description='integer number', default=1, options={'ANIMATABLE'}, update=updateNode)
    
    def init(self, context):
        self.inputs.new('StringsSocket', "Integer", "Integer")
        self.outputs.new('StringsSocket', "Integer", "Integer")
    
    def draw_buttons(self, context, layout):
        layout.prop(self, "int_", text="integer")

    def update(self):
        # inputs
        if len(self.inputs['Integer'].links)>0:
            if not self.inputs['Integer'].node.socket_value_update:
                self.inputs['Integer'].node.update()
            Integer = eval(self.inputs['Integer'].links[0].from_socket.StringsProperty)[0][0]
        else:
            Integer = self.int_
        
        # outputs
        if 'Integer' in self.outputs and len(self.outputs['Integer'].links)>0:
            if not self.outputs['Integer'].node.socket_value_update:
                self.inputs['Integer'].node.update()
            
            self.outputs['Integer'].StringsProperty = str([[Integer, ]])
    
    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(IntegerNode)
    
def unregister():
    bpy.utils.unregister_class(IntegerNode)

if __name__ == "__main__":
    register()