import bpy
from node_s import *
from mathutils.noise import seed_set,random_unit_vector
from util import *


class RandomVectorNode(Node, SverchCustomTreeNode):
    ''' Random Vectors with len=1'''
    bl_idname = 'RandomVectorNode'
    bl_label = 'Random Vector'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    count_inner = bpy.props.IntProperty(name = 'count_inner', description='random', default=1,min=1, options={'ANIMATABLE'}, update=updateNode)
    seed = bpy.props.IntProperty(name = 'seed', description='random seed', default=1, options={'ANIMATABLE'}, update=updateNode)
    
    def init(self, context):
        self.inputs.new('StringsSocket', "Count", "Count")
        self.inputs.new('StringsSocket', "Seed", "Seed")

        self.outputs.new('VerticesSocket', "Random", "Random")
        
    def draw_buttons(self, context, layout):
        layout.prop(self, "count_inner", text="Count")
        layout.prop(self, "seed", text="Seed")


    def update(self):
        # inputs
        if 'Count' in self.inputs and len(self.inputs['Count'].links)>0 and \
            type(self.inputs['Count'].links[0].from_socket) == bpy.types.StringsSocket:
            if not self.inputs['Count'].node.socket_value_update:
                self.inputs['Count'].node.update()
            Coun = SvGetSocketAnyType(self,self.inputs['Count'])
        else:
            Coun = [[self.count_inner]]
            
        if 'Seed' in self.inputs and len(self.inputs['Seed'].links)>0 and \
             type(self.inputs['Seed'].links[0].from_socket) == bpy.types.StringsSocket:
            if not self.inputs['Seed'].node.socket_value_update:
                self.inputs['Seed'].node.update()
            tmp = SvGetSocketAnyType(self,self.inputs['Seed'])
            Seed = tmp[0][0]
        else:
            Seed = self.seed
      
        
        # outputs 
        if 'Random' in self.outputs and len(self.outputs['Random'].links)>0:
            Random = []          
            # set seed, protect against float input
            # seed = 0 is special value for blender which unsets the seed value
            # and starts to use system time making the random values unrepeatable.
            # So when seed = 0 we use a random value far from 0, generated used random.org
            int_seed = int(round(Seed))
            if int_seed:
                seed_set(int_seed)
            else:
                seed_set(140230)  
                
            # Coun[0], only takes first list
            for number in Coun[0]:
                if number > 0:
                    Random.append( [random_unit_vector().to_tuple() \
                                        for i in range(int(number))])
            SvSetSocketAnyType(self,'Random',Random)

    
    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(RandomVectorNode)
    
def unregister():
    bpy.utils.unregister_class(RandomVectorNode)

if __name__ == "__main__":
    register()