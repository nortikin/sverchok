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
        if 'Count' in self.inputs and self.inputs['Count'].is_linked and \
            type(self.inputs['Count'].links[0].from_socket) == bpy.types.StringsSocket:
      
            tmp = SvGetSocketAnyType(self,self.inputs['Count'])
            Coun = tmp[0][0]
        else:
            Coun = self.count_inner
            
        if 'Seed' in self.inputs and self.inputs['Seed'].is_linked and \
            type(self.inputs['Seed'].links[0].from_socket) == bpy.types.StringsSocket:
            
            tmp = SvGetSocketAnyType(self,self.inputs['Seed'])
            Seed = tmp[0][0]
        else:
            Seed = self.seed
        
        
        # outputs
        random.seed(Seed)
        
        if 'Random' in self.outputs and self.outputs['Random'].is_linked:
            Random = [round(random.random(),16) for c in range(Coun)]
            SvSetSocketAnyType(self, 'Random',[Random])

    
    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(RandomNode)
    
def unregister():
    bpy.utils.unregister_class(RandomNode)

if __name__ == "__main__":
    register()