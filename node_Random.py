import bpy
from node_s import *
import random

class RandomNode(Node, SverchCustomTreeNode):
    ''' Random numbers 0-1'''
    bl_idname = 'RandomNode'
    bl_label = 'Random'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    Count_ = bpy.props.IntProperty(name='Count_', description='Random', default=1, min=1)
    
    def init(self, context):
        self.inputs.new('StringsSocket', "Count", "Count")
        self.outputs.new('StringsSocket', "Random", "Random")
        
    def draw(self, context, layout):
        layout.prop(self, "Count_", text="Random count")

    def update(self):
        # inputs
        if 'Count' in self.inputs and len(self.inputs['Count'].links)>0 and type(self.inputs['Count'].links[0].from_socket) == bpy.types.StringsSocket:
            if not self.inputs['Count'].node.socket_value_update:
                self.inputs['Count'].node.update()
                
            Count = eval(self.inputs['Count'].links[0].from_socket.StringsProperty)[0][0]
        else:
            Count = self.Count_
    
        
        # outputs
        if 'Random' in self.outputs and len(self.outputs['Random'].links)>0:
            if not self.outputs['Random'].node.socket_value_update:
                self.inputs['Random'].node.update()
            Random = [c for c in self.RandM(Count)]
            
            self.outputs['Random'].StringsProperty = str([Random, ])

    def RandM(self, Count):
        while Count:
            yield random.random()
            Count -= 1
    
    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(RandomNode)
    
def unregister():
    bpy.utils.unregister_class(RandomNode)

if __name__ == "__main__":
    register()