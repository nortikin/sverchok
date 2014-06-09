import bpy
from node_s import *
from mathutils.noise import seed_set,random_unit_vector
from util import *


class RandomVectorNode(Node, SverchCustomTreeNode):
    ''' Random Vectors with len=1'''
    bl_idname = 'RandomVectorNode'
    bl_label = 'Random Vector'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    count_inner = bpy.props.IntProperty(name = 'Count', description='random', default=1,min=1, options={'ANIMATABLE'}, update=updateNode)
    seed = bpy.props.IntProperty(name = 'Seed', description='random seed', default=1, options={'ANIMATABLE'}, update=updateNode)
    
    def init(self, context):
        self.inputs.new('StringsSocket', "Count").prop_name = 'count_inner'
        self.inputs.new('StringsSocket', "Seed").prop_name = 'seed'

        self.outputs.new('VerticesSocket', "Random", "Random")
        
    def update(self):
        # inputs
        if 'Count' in self.inputs and self.inputs['Count'].links and \
            type(self.inputs['Count'].links[0].from_socket) == bpy.types.StringsSocket:
            Coun = SvGetSocketAnyType(self,self.inputs['Count'])[0]
        else:
            Coun = [self.count_inner]
            
        if 'Seed' in self.inputs and self.inputs['Seed'].links and \
             type(self.inputs['Seed'].links[0].from_socket) == bpy.types.StringsSocket:
            Seed = SvGetSocketAnyType(self,self.inputs['Seed'])[0]
        else:
            Seed = [self.seed]
      
        
        # outputs 
        if 'Random' in self.outputs and self.outputs['Random'].links:
            Random = []          
            param=match_long_repeat([Coun,Seed])
            # set seed, protect against float input
            # seed = 0 is special value for blender which unsets the seed value
            # and starts to use system time making the random values unrepeatable.
            # So when seed = 0 we use a random value far from 0, generated used random.org
            for c,s in zip(*param):
                int_seed = int(round(s))
                if int_seed:
                    seed_set(int_seed)
                else:
                    seed_set(140230)  
                                    
                Random.append([random_unit_vector().to_tuple() for i in range(int(max(1,c)))])
            
            SvSetSocketAnyType(self,'Random',Random)

    
    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(RandomVectorNode)
    
def unregister():
    bpy.utils.unregister_class(RandomVectorNode)

if __name__ == "__main__":
    register()
