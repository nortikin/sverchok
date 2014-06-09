import bpy
from node_s import *
import random
from util import *

class RandomNode(Node, SverchCustomTreeNode):
    ''' Random numbers 0-1'''
    bl_idname = 'RandomNode'
    bl_label = 'Random'
    bl_icon = 'OUTLINER_OB_EMPTY'

    count_inner = bpy.props.IntProperty(name = 'Count', default=1, min=1, options={'ANIMATABLE'}, update=updateNode)
    seed = bpy.props.FloatProperty(name = 'Seed', default=0, options={'ANIMATABLE'}, update=updateNode)
    
    def init(self, context):
        self.inputs.new('StringsSocket', "Count").prop_name = 'count_inner'
        self.inputs.new('StringsSocket', "Seed").prop_name = 'seed'

        self.outputs.new('StringsSocket', "Random", "Random")
        
    def draw_buttons(self, context, layout):
        pass
        #layout.prop(self, "count_inner", text="Count")
        #layout.prop(self, "seed", text="Seed")

    def update(self):
        if not 'Random' in self.outputs:
            return
        # inputs
        if 'Count' in self.inputs:
            Coun = self.inputs['Count'].sv_get()[0]
            
        if 'Seed' in self.inputs:
            Seed = self.inputs['Seed'].sv_get()[0]
        
        # outputs
        
        if 'Random' in self.outputs and self.outputs['Random'].links:
            Random = []
            if len(Seed) == 1:
                random.seed(Seed[0])
                for c in Coun:
                    Random.append([random.random() for i in range(int(c))])
            else:
                param = match_repeat_long([Seed,Count])
                for s,c in zip(*param):
                    random.seed(s)
                    Random.append([random.random() for i in range(int(c))])
                    
            SvSetSocketAnyType(self, 'Random',Random)

    
    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(RandomNode)
    
def unregister():
    bpy.utils.unregister_class(RandomNode)

if __name__ == "__main__":
    register()
