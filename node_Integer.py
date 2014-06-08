import bpy
from node_s import *
from util import *

class IntegerNode(Node, SverchCustomTreeNode):
    ''' Integer '''
    bl_idname = 'IntegerNode'
    bl_label = 'Integer'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    int_ = bpy.props.IntProperty(name = 'Int', description='integer number', default=1, options={'ANIMATABLE'}, update=updateNode)
    
    def init(self, context):
        self.inputs.new('StringsSocket', "Integer", "Integer").prop_name='int_'
        self.outputs.new('StringsSocket', "Integer", "Integer")
    
    def update(self):
        # inputs
        if 'Integer' in self.inputs and self.inputs['Integer'].links:
            tmp = SvGetSocketAnyType(self,self.inputs['Integer'])
            Integer = tmp[0][0]
        else:
            Integer = self.int_
        
        # outputs
        if 'Integer' in self.outputs and self.outputs['Integer'].links:
            SvSetSocketAnyType(self, 'Integer',[[Integer]])
            
    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(IntegerNode)
    
def unregister():
    bpy.utils.unregister_class(IntegerNode)

if __name__ == "__main__":
    register()
