import bpy
from node_s import *
import random
from util import *

class RandomNode(Node, SverchCustomTreeNode):
    ''' Random numbers 0-1'''
    bl_idname = 'RandomNode'
    bl_label = 'Random'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    count_inner = bpy.props.IntProperty(name = 'count_inner', description='random', default=1, min=1, options={'ANIMATABLE'}, update=updateNode)
    seed = bpy.props.FloatProperty(name = 'seed', description='random seed', default=0, options={'ANIMATABLE'}, update=updateNode)
    
    def init(self, context):
        self.inputs.new('StringsSocket', "Count", "Count")
        self.inputs.new('StringsSocket', "Seed", "Seed")

        self.outputs.new('StringsSocket', "Random", "Random")
        
    def draw_buttons(self, context, layout):
        layout.prop(self, "count_inner", text="Count")
        layout.prop(self, "seed", text="Seed")


    def update(self):
        # inputs
        if 'Count' in self.inputs and len(self.inputs['Count'].links)>0 and type(self.inputs['Count'].links[0].from_socket) == bpy.types.StringsSocket:
            if not self.inputs['Count'].node.socket_value_update:
                self.inputs['Count'].node.update()
                
            Coun = eval(self.inputs['Count'].links[0].from_socket.StringsProperty)[0][0]
        else:
            Coun = self.count_inner
            
        if 'Seed' in self.inputs and len(self.inputs['Seed'].links)>0 and type(self.inputs['Seed'].links[0].from_socket) == bpy.types.StringsSocket:
            if not self.inputs['Seed'].node.socket_value_update:
                self.inputs['Seed'].node.update()
            
            Seed = eval(self.inputs['Seed'].links[0].from_socket.StringsProperty)[0][0]
        else:
            Seed = self.seed
        
        
        # outputs
        random.seed(Seed)
        
        if 'Random' in self.outputs and len(self.outputs['Random'].links)>0:
            if not self.outputs['Random'].node.socket_value_update:
                self.inputs['Random'].node.update()
            Random = [c for c in self.RandM(Coun)]
            
            self.outputs['Random'].StringsProperty = str([Random, ])

    def RandM(self, Count):
        while Count:
            yield round(random.random(), 16) # it cannot take nonrounded float
            Count -= 1
    
    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(RandomNode)
    
def unregister():
    bpy.utils.unregister_class(RandomNode)

if __name__ == "__main__":
    register()