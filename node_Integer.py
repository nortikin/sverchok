import bpy
from node_s import *

class IntegerNode(Node, SverchCustomTreeNode):
    ''' Integer '''
    bl_idname = 'IntegerNode'
    bl_label = 'Integer'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    def init(self, context):
        self.inputs.new('NodeSocketInt', "Integer", "Integer").default_value = 10
        self.outputs.new('StringsSocket', "Integer", "Integer")
        

    def update(self):
        # inputs
        if len(self.inputs['Integer'].links)>0 and type(self.inputs['Integer'].links[0].from_socket) == bpy.types.NodeSocketInteger:
            if not self.inputs['Integer'].node.socket_value_update:
                self.inputs['Integer'].node.update()
            Integer = self.inputs['Integer'].links[0].from_socket.default_value
        else:
            Integer = self.inputs['Integer'].default_value
        
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