import bpy
from node_s import *
from util import *

class SvListInputNode(Node, SverchCustomTreeNode):
    ''' Creta a float or int List '''
    bl_idname = 'SvListInputNode'
    bl_label = 'List Input'
    bl_icon = 'OUTLINER_OB_EMPTY'
                
    defaults = [0 for i in range(32)]
    int_ = bpy.props.IntProperty(name = 'int_', description='integer number', default=1,min=1,max=32, update=updateNode)
    int_list = bpy.props.IntVectorProperty(name='int_list',description="Integer list",default=defaults,size=32,update=updateNode)
    float_list = bpy.props.FloatVectorProperty(name='float_list',description="Float list",default=defaults,size=32,update=updateNode)
    
    modes = [
        ("int_list","Int","Integer","",1),
        ("float_list","Float","Float","",2)]
             
    mode = bpy.props.EnumProperty(items=modes,
                default='int_list',
                update=updateNode)
    
    def init(self, context):
        self.outputs.new('StringsSocket', "List", "List")
        
    def draw_buttons(self, context, layout):
        layout.prop(self, "int_", text="List Length")
        layout.prop(self, "mode", expand=True)
        col = layout.column(align=True)
        for i in range(self.int_):
            col.prop(self,self.mode,text='',index=i)
        col= layout.column(align=True)
        
    def update(self):
        if 'List' in self.outputs and self.outputs['List'].links:
            if self.mode == 'int_list':
                SvSetSocketAnyType(self,"List",[list(self.int_list[:self.int_])])
            else:
                SvSetSocketAnyType(self,"List",[list(self.float_list[:self.int_])])
        else:
            SvSetSocketAnyType(self,"List",[])
            
    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(SvListInputNode)
    
def unregister():
    bpy.utils.unregister_class(SvListInputNode)

if __name__ == "__main__":
    register()
    
    
    
       

