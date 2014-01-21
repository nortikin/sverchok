import bpy
from node_s import *
from util import *

class Test1Node(Node, SverchCustomTreeNode):
    ''' Test 1 node to test new features '''
    bl_idname = 'Test1Node'
    bl_label = 'Test 1'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    def draw_buttons(self, context, layout):
        pass
        
    def init(self, context):
        # multysocket
        self.inputs.new('StringsSocket', "n[.]", "n[.]")
        # adaptive socket
        self.outputs.new('VerticesSocket', "Result", "Result")
        
   def update(self):
        # multisocket - from util(formula node) + cache
        '''
        ch = self.check_slots(0)
        if ch:
            for c in ch[:-1]:
                self.inputs.remove(self.inputs[ch[-1]])
        
        list_mult=[]
        for idx, multi in enumerate(self.inputs[1:]):   
            if multi.links:
                if not multi.node.socket_value_update:
                    multi.node.update()
                if type(multi.links[0].from_socket) == StringsSocket:
                    mult = eval(multi.links[0].from_socket.StringsProperty)
                elif type(multi.links[0].from_socket) == VerticesSocket:
                    mult = eval(multi.links[0].from_socket.VerticesProperty)
                elif type(multi.links[0].from_socket) == MatrixSocket:
                    mult = eval(multi.links[0].from_socket.MatrixProperty)
                ch = self.check_slots(2)
                if not ch:
                    self.inputs.new('StringsSocket', 'n[.]', "n[.]")

                list_mult.extend(mult)
        if len(list_mult)==0:
            list_mult= [[0.0]]
        '''
        # adaptive socket - from util(mask list node) + cache
        if 'Result' in self.outputs and len(self.outputs['Result'].links)>0:
            if not self.outputs['Result'].node.socket_value_update:
               self.outputs['Result'].node.update()
            
            # how to assign correct property 
            self.outputs['Result'].VerticesProperty = str(result)
    
            
def register():
    bpy.utils.register_class(Test1Node)
    
def unregister():
    bpy.utils.unregister_class(Test1Node)

if __name__ == "__main__":
    register()
