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
            
            result = f(X)

            # how to assign correct property to adaptive output:
            # in nearest future with socket's data' dictionary we will send
            # only node_name+layout_name+socket_name in str() format
            # and will make separate definition to easyly assign and
            # get and recognise data from dictionary
            SvSetSocketAnyType(self, 'data', result)


# multi input example
class Test2Node(Node, SverchCustomTreeNode):
    ''' Test 2 node to test new features and make ideal node as example of howto '''
    bl_idname = 'Test2Node'
    bl_label = 'Test 1'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    # two veriables for adaptive socket
    typ = bpy.props.StringProperty(name='typ', default='')
    newsock = bpy.props.BoolProperty(name='newsock', default=False)
    # Base name for multi socket input
    
    base_name = 'Data '
    multi_socket_type = 'StringsSocket'

    def draw_buttons(self, context, layout):
        # if to make button - use name of socket and name of tree
        # will be here soon
        pass
        
    def init(self, context):
        # initial socket, that defines type of adaptive socket
        self.inputs.new('StringsSocket', "Data 0", "Data 0")
        # multisocket 
        # adaptive socket
        self.outputs.new('VerticesSocket', "Data", "Data")
        
   def update(self):
        # multisocket - from util(formula node) + cache
        # 
        mulit_socket(min=1)
        
        if 'Data 0' in self.inputs and self.inputs['Data 0'].is_linked:
            
            # adaptive socket output - from util(mask list node) + cache
            inputsocketname = self.inputs[0].name
            outputsocketname = ['Data',]
            changable_sockets(self, inputsocketname, outputsocketname)
            
        # if output is linked collect data and process
        if 'Data' in self.outputs and self.outputs['Data'].is_linked:
            
            slots = []
            for socket in self.inputs:
                if socket.is_linked:
                    slots.append(SvGetSocketAnyType(self,socket))

            # determine if you have enough inputs for make output
            # if not return
            # examples: all but last (last is never connected)
            # len(slots) == len(self.inputs)-1    
            # if more than 2 etc.

            if len(slots) < 2:
                return   
            
            # Process data
            result = f(X)
            # how to assign correct property to adaptive output:
            # in nearest future with socket's data' dictionary we will send
            # only node_name+layout_name+socket_name in str() format
            # and will make separate definition to easyly assign and
            # get and recognise data from dictionary
            SvSetSocketAnyType(self, 'Data', result)
            

def register():
    bpy.utils.register_class(Test1Node)
    bpy.utils.register_class(Test2Node)
    
def unregister():
    bpy.utils.unregister_class(Test1Node)
    bpy.utils.unregister_class(Test2Node)


if __name__ == "__main__":
    register()
