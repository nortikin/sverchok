import bpy
from node_s import *
from util import *

class Test1Node(Node, SverchCustomTreeNode):
    ''' Test 1 node to test new features and make ideal node as example of howto '''
    bl_idname = 'Test1Node'
    bl_label = 'Test 1'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    # two veriables for multi socket input
    base_name = 'x'
    multi_socket_type = 'StringsSocket'
    
    # two veriables for adaptive socket
    typ = bpy.props.StringProperty(name='typ', default='')
    newsock = bpy.props.BoolProperty(name='newsock', default=False)
    
    def draw_buttons(self, context, layout):
        # if to make button - use name of socket and name of tree
        # will be here soon
        pass
        
    def init(self, context):
        # initial socket, is defines type of output
        self.inputs.new('StringsSocket', "data", "data")
        # this is multysocket
        self.inputs.new('StringsSocket', "x0", "x0")
        # adaptive socket
        self.outputs.new('StringsSocket', "data", "data")
        
    def update(self):
        # multisocket - from util(formula node)
        multi_socket(self, min=2)
        
        if 'x0' in self.inputs and len(self.inputs['x0'].links)>0:
            # adaptive socket - from util(mask list node)
            inputsocketname = self.inputs[0].name   # is you need x0 to define socket type - set 0 to 1
            outputsocketname = ['data',]
            changable_sockets(self, inputsocketname, outputsocketname)
        
        if 'data' in self.outputs and len(self.outputs['data'].links)>0:
            if 'x0' in self.inputs and len(self.inputs['x0'].links)>0:
                # get any type socket from input:
                X = SvGetSocketAnyType(self, self.inputs['data'])
                slots = []
                for socket in self.inputs:
                    if socket.links:
                        slots.append(SvGetSocketAnyType(self,socket))

                # determine if you have enough inputs for make output
                # if not return
                # examples: all but last (last is never connected)
                # len(slots) == len(self.inputs)-1    
                # if more than 2 etc.

                if len(slots) < 2:
                    return   
                
                # Process data
                X_ = dataCorrect(X)
                result = []
                for socket in slots:
                    result.extend(self.f(X_,dataCorrect(socket)))
                
                
                # how to assign correct property to adaptive output:
                # in nearest future with socket's data' dictionary we will send
                # only node_name+layout_name+socket_name in str() format
                # and will make separate definition to easyly assign and
                # get and recognise data from dictionary
                SvSetSocketAnyType(self, 'data', result)
            
    def f(self, x, socket):
        ''' this makes sum of units for every socket and object '''
        out = []
        fullList(x, len(socket))
        for i, obj in enumerate(socket):
            if type(obj) not in [int, float]:
                out.append(self.f(x[i],obj))
            else:
                out.append(obj+x[i])
        return out


class Test2Node(Node, SverchCustomTreeNode):
    ''' Test2 without comments '''
    bl_idname = 'Test2Node'
    bl_label = 'Test 2'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    base_name = 'x'
    multi_socket_type = 'StringsSocket'
    typ = bpy.props.StringProperty(name='typ', default='')
    newsock = bpy.props.BoolProperty(name='newsock', default=False)
        
    def init(self, context):
        self.inputs.new('StringsSocket', "data", "data")
        self.inputs.new('StringsSocket', "x0", "x0")
        self.outputs.new('StringsSocket', "data", "data")
        
    def update(self):
        multi_socket(self, min=2)
        
        if 'x0' in self.inputs and len(self.inputs['x0'].links)>0:
            inputsocketname = self.inputs[0].name
            outputsocketname = ['data',]
            changable_sockets(self, inputsocketname, outputsocketname)
        
        if 'data' in self.outputs and len(self.outputs['data'].links)>0:
            if 'x0' in self.inputs and len(self.inputs['x0'].links)>0:
                X = SvGetSocketAnyType(self, self.inputs['data'])
                slots = []
                for socket in self.inputs:
                    if socket.links:
                        slots.append(SvGetSocketAnyType(self,socket))
                if len(slots) < 2:
                    return
                
                X_ = dataCorrect(X)
                result = []
                for socket in slots:
                    result.extend(self.f(X_,dataCorrect(socket)))
                
                SvSetSocketAnyType(self, 'data', result)
            
    def f(self, x, socket):
        out = []
        fullList(x, len(socket))
        for i, obj in enumerate(socket):
            if type(obj) not in [int, float]:
                out.append(self.f(x[i],obj))
            else:
                out.append(obj+x[i])
        return out

def register():
    bpy.utils.register_class(Test1Node)
    bpy.utils.register_class(Test2Node)
    
def unregister():
    bpy.utils.unregister_class(Test1Node)
    bpy.utils.unregister_class(Test2Node)


if __name__ == "__main__":
    register()
