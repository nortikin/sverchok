import bpy
from node_s import *
from functools import reduce
from util import *



class ListLevelsNode(Node, SverchCustomTreeNode):
    ''' Lists Levels node '''
    bl_idname = 'ListLevelsNode'
    bl_label = 'List Levels'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    Sverch_LisLev = bpy.props.StringProperty(name='Sverch_LisLev', description='User defined nesty levels. (i.e. 1,2)', default='1,2,3', update=updateNode)
    typ = bpy.props.StringProperty(name='typ', default='')
    newsock = bpy.props.BoolProperty(name='newsock', default=False)
    
    def init(self, context):
        self.inputs.new('StringsSocket', 'data', 'data')
        self.outputs.new('StringsSocket', 'data', 'data')
    
    def draw_buttons(self, context, layout):
        layout.prop(self, "Sverch_LisLev", text="List levels")
    
    def update(self):
        if 'data' in self.inputs and len(self.inputs['data'].links)>0:
            inputsocketname = 'data'
            outputsocketname = ['data',]
            changable_sockets(self, inputsocketname, outputsocketname)
            
            if 'data' in self.outputs and len(self.outputs['data'].links)>0:
                data = SvGetSocketAnyType(self, self.inputs['data'])
                userlevelb = eval('['+self.Sverch_LisLev+']')
                SvSetSocketAnyType(self, 'data', preobrazovatel(data, userlevelb))

    def update_socket(self, context):
        self.update()

def register():
    bpy.utils.register_class(ListLevelsNode)
    
def unregister():
    bpy.utils.unregister_class(ListLevelsNode)

if __name__ == "__main__":
    register()