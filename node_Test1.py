import bpy
from node_s import *
from util import *

class Test1Node(Node, SverchCustomTreeNode):
    ''' Test 1 node to test new features and make ideal node as example of howto '''
    bl_idname = 'Test1Node'
    bl_label = 'Test 1'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    # two veriables for adaptive socket
    typ = bpy.props.StringProperty(name='typ', default='')
    newsock = bpy.props.BoolProperty(name='newsock', default=False)
    
    def draw_buttons(self, context, layout):
        # if to make button - use name of socket and name of tree
        # will be here soon
        pass
        
    def init(self, context):
        # initial socket, that defines type of adaptive socket
        self.inputs.new('StringsSocket', "x", "x")
        # multysocket
        self.inputs.new('StringsSocket', "n[.]", "n[.]")
        # adaptive socket
        self.outputs.new('VerticesSocket', "data", "data")
        
   def update(self):
        # multisocket - from util(formula node) + cache
        # make multisocket - TODO
        
        if 'x' in self.inputs and len(self.inputs['x'].links)>0:
            if not self.inputs['x'].node.socket_value_update:
                self.inputs['x'].node.update() 
            # adaptive socket - from util(mask list node) + cache
            inputsocketname = self.inputs[0].name
            outputsocketname = ['data',]
            changable_sockets(self, inputsocketname, outputsocketname)
        
        if 'data' in self.outputs and len(self.outputs['data'].links)>0:
            if 'x' in self.inputs and len(self.inputs['x'].links)>0:
                # get any type socket from input:
                X = SvGetSocketAnyType(self, self.inputs['x'])
            # get multysocket values to list - TODO
            
            # how to assign correct property to adaptive output:
            # in nearest future with socket's data' dictionary we will send
            # only node_name+layout_name+socket_name in str() format
            # and will make separate definition to easyly assign and
            # get and recognise data from dictionary
            SvSetSocketAnyType(self, 'data', result)
            
def register():
    bpy.utils.register_class(Test1Node)
    
def unregister():
    bpy.utils.unregister_class(Test1Node)

if __name__ == "__main__":
    register()
