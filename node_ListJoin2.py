import bpy
from node_s import *
from util import *

class ListJoinNode(Node, SverchCustomTreeNode):
    ''' ListJoin node '''
    bl_idname = 'ListJoinNode'
    bl_label = 'List Join'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    JoinLevel = bpy.props.IntProperty(name='JoinLevel', description='Choose join level of data (see help)', default=1, min=1, update=updateNode)
    mix_check = bpy.props.BoolProperty(name='mix', description='Grouping similar to zip()', default=False, update=updateNode)
    wrap_check = bpy.props.BoolProperty(name='wrap', description='Grouping similar to append(list)', default=False, update=updateNode)
    typ = bpy.props.StringProperty(name='typ', default='')
    newsock = bpy.props.BoolProperty(name='newsock', default=False)
    
    base_name = 'data '
    multi_socket_type = 'StringsSocket'
    
    def init(self, context):
        self.inputs.new('StringsSocket', "data", "data")
        self.outputs.new('StringsSocket', 'data', 'data')
       
    def draw_buttons(self, context, layout):
        layout.prop(self, "mix_check", text="mix")
        layout.prop(self, "wrap_check", text="wrap")
        layout.prop(self, "JoinLevel", text="JoinLevel lists")
    
    def update(self):
        # inputs
        multi_socket(self , min=1)
        
        if 'data' in self.inputs and len(self.inputs['data'].links)>0:
            inputsocketname = 'data'
            outputsocketname = ['data']
            changable_sockets(self, inputsocketname, outputsocketname)
        
        if 'data' in self.outputs and self.outputs['data'].links:
            slots = []
            for socket in self.inputs:
                if socket.links:
                    slots.append(SvGetSocketAnyType(self,socket))
            if len(slots)==0:
                return
                
            list_result = joiner(slots,self.JoinLevel)
            result = list_result.copy()
            if self.mix_check:
                list_mix = myZip_2(slots,self.JoinLevel)
                result = list_mix.copy()

            if self.wrap_check:
                list_wrap = wrapper_2(slots, list_result, self.JoinLevel)
                result = list_wrap.copy()

                if self.mix_check:
                    list_wrap_mix = wrapper_2(slots, list_mix, self.JoinLevel)
                    result = list_wrap_mix.copy()
                    
            SvSetSocketAnyType(self, 'data', result)
            
    def update_socket(self, context):
        self.update()

def register():
    bpy.utils.register_class(ListJoinNode)
    
def unregister():
    bpy.utils.unregister_class(ListJoinNode)

if __name__ == "__main__":
    register()