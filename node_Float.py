import bpy
from node_s import *
from util import *

class FloatNode(Node, SverchCustomTreeNode):
    ''' Float '''
    bl_idname = 'FloatNode'
    bl_label = 'Float'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    float_ = bpy.props.FloatProperty(name = 'Float', description='float number', default=1.0, options={'ANIMATABLE'}, update=updateNode)
    
    def init(self, context):
        self.inputs.new('StringsSocket', "Float").prop_name='float_'
        self.outputs.new('StringsSocket', "Float")
    

    def update(self):
        # inputs
        if 'Float' in self.inputs and self.inputs['Float'].links:
            tmp = SvGetSocketAnyType(self,self.inputs['Float'])
            Float = tmp[0][0]
        else:
            Float = self.float_
        # outputs
        if 'Float' in self.outputs and self.outputs['Float'].links:
            SvSetSocketAnyType(self,'Float',[[Float]])
    
    def update_socket(self, context):
        self.update()

def register():
    bpy.utils.register_class(FloatNode)
    
def unregister():
    bpy.utils.unregister_class(FloatNode)

if __name__ == "__main__":
    register()
