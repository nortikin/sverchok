import bpy
from node_s import *
from util import *

class SvDebugPrintNode(Node, SverchCustomTreeNode):
    ''' SvDebugPrintNode '''
    bl_idname = 'SvDebugPrintNode'
    bl_label = 'Debug print'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    # I wanted to show the bool so you could turn off and on individual sockets
    # but needs changes in node_s, want to think a bit more before adding an index option to
    # stringsockets, for now draw_button_ext
    defaults = [True for i in range(32)]
    print_socket = bpy.props.BoolVectorProperty(name='Print',default=defaults,size=32,update=updateNode)
    base_name = 'Data '
    multi_socket_type = 'StringsSocket'
    print_data = bpy.props.BoolProperty(name='Active',description='Turn on/off printing to stdout',default=True,update=updateNode)
    
    def init(self, context):
        socket=self.inputs.new('StringsSocket', "Data 0")
    
    def draw_buttons(self, context, layout):
        layout.prop(self,'print_data')
     
    def draw_buttons_ext(self,context,layout):
        layout.label(text='Print?')
        for i,socket in enumerate(self.inputs):
            layout.prop(self, "print_socket",index=i,text=socket.name)
   
    def update(self):
        multi_socket(self, min=1)
        
        if not self.print_data:
            return
            
        for i,socket in enumerate(self.inputs):
            if socket.links and self.print_socket[i]:
                print(SvGetSocketAnyType(self,socket))
            
    def update_socket(self, context):
        self.update()

def register():
    bpy.utils.register_class(SvDebugPrintNode)
    
def unregister():
    bpy.utils.unregister_class(SvDebugPrintNode)

if __name__ == "__main__":
    register()
