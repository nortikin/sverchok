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
    v_int = bpy.props.IntProperty(name = 'int_', description='integer number', default=1,min=1,max=10, update=updateNode)

    int_list = bpy.props.IntVectorProperty(name='int_list',description="Integer list",default=defaults,size=32,update=updateNode)
    float_list = bpy.props.FloatVectorProperty(name='float_list',description="Float list",default=defaults,size=32,update=updateNode)
    vector_list = bpy.props.FloatVectorProperty(name='vector_list',description="Vector list",default=defaults,size=32,update=updateNode)
    
    
    def changeMode(self,context):
        if self.mode == 'vector':
            if not 'Vector List' in self.outputs:
                self.outputs.remove(self.outputs[0])
                self.outputs.new('VerticesSocket','Vector List','Vector List')
                return
        else:
            if not 'List' in self.outputs:
                self.outputs.remove(self.outputs[0])
                self.outputs.new('StringsSocket', 'List', 'List')
                return
        
    
    modes = [
        ("int_list","Int","Integer","",1),
        ("float_list","Float","Float","",2),
        ("vector","Vector","Vector","",3)]
             
    mode = bpy.props.EnumProperty(items=modes,
                default='int_list',
                update=changeMode)
    
    def init(self, context):
        self.outputs.new('StringsSocket', "List", "List")
        
    def draw_buttons(self, context, layout):
        if self.mode=='vector':
            layout.prop(self, "v_int", text="List Length")
        else:
            layout.prop(self, "int_", text="List Length")
        
        layout.prop(self, "mode", expand=True)
        
        if self.mode=='vector':
            for i in range(self.v_int):
                col = layout.column(align=True)
                for j in range(3):
                    col.prop(self,'vector_list',index=i*3+j,text='XYZ'[j])
        else:        
            col = layout.column(align=True)
            for i in range(self.int_):
                col.prop(self,self.mode,index=i,text=str(i))
        
    def update(self):
        if any((n in self.outputs for n in ['List','Vector List'])) and self.outputs[0].links:
            if self.mode == 'int_list':
                SvSetSocketAnyType(self,"List",[list(self.int_list[:self.int_])])
            elif self.mode == 'float_list':
                SvSetSocketAnyType(self,"List",[list(self.float_list[:self.int_])])
            elif self.mode == 'vector':
                c=self.v_int*3
                v_l=list(self.vector_list)
                out=list(zip(v_l[0:c:3],v_l[1:c:3],v_l[2:c:3]))
                SvSetSocketAnyType(self,"Vector List",[out])
            
    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(SvListInputNode)
    
def unregister():
    bpy.utils.unregister_class(SvListInputNode)

if __name__ == "__main__":
    register()
    
    
    
       

