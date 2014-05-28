from node_s import *
from util import *
from itertools import chain

# ListSplit
# by Linus Yng            
    
def split(data,size):
    size = max(1,int(size))
    return [data[i:i+size] for i in range(0, len(data), size)]
           
class SvListSplitNode(Node, SverchCustomTreeNode):
    ''' List Split '''
    bl_idname = 'SvListSplitNode'
    bl_label = 'List Split'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    def change_mode(self,context):
        if self.unwrap:
            self.level_unwrap=max(1,self.level)
        else:
            self.level=self.level_unwrap
        updateNode(self, context)
            
    level = bpy.props.IntProperty(name='Level', default=1, min=0, update=updateNode)
    level_unwrap = bpy.props.IntProperty(name='Level', default=1, min=1, update=updateNode)
    split = bpy.props.IntProperty(name='Split size', default=1, min=1, update=updateNode)
    unwrap = bpy.props.BoolProperty(name='Unwrap', default=True, update=change_mode)
    
    typ = bpy.props.StringProperty(name='typ', default='')
    newsock = bpy.props.BoolProperty(name='newsock', default=False)
    
    def draw_buttons(self, context, layout):
        if self.unwrap:
            layout.prop(self, "level_unwrap", text="level")
        else:
            layout.prop(self, "level", text="level")
        layout.prop(self, "unwrap")
        
    def init(self, context):
        self.inputs.new('StringsSocket', "Data")
        self.inputs.new('StringsSocket', "Split").prop_name='split'
        self.outputs.new('StringsSocket',"Split")

    def update(self):
        if 'Data' in self.inputs and self.inputs['Data'].links:
            inputsocketname = 'Data'
            outputsocketname = ['Split']
            changable_sockets(self, inputsocketname, outputsocketname)
        
        if 'Split' in self.outputs and self.outputs['Split'].links:
            if 'Data' in self.inputs and self.inputs['Data'].links:
                data = SvGetSocketAnyType(self, self.inputs['Data'])
                sizes = self.inputs['Split'].sv_get()[0]
                if self.unwrap:
                    out = self.get(data, self.level_unwrap, sizes)
                elif self.level:
                    out = self.get(data, self.level, sizes)
                else:
                    out = split(data,sizes[0])
                SvSetSocketAnyType(self, 'Split', out)

    def get(self, data, level, size):
        if not isinstance(data,(list,tuple)):
            return data
        if not isinstance(data[0],(list,tuple)):
            return data
        if level >1: # find level to work on
            return [self.get(d, level-1, size) for d in data]
        elif level == 1: #execute the chosen function
            sizes = repeat_last(size)
            if self.unwrap:
                return list(chain.from_iterable((split(d, next(sizes)) for d in data))) 
            else:    
                return [split(d,next(sizes)) for d in data]
        else: #Fail
            return None
        
    def update_socket(self, context):
        self.update()

def register():
    bpy.utils.register_class(SvListSplitNode)   
    
def unregister():
    bpy.utils.unregister_class(SvListSplitNode)

if __name__ == "__main__":
    register()
