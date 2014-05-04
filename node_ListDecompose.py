import bpy
from node_s import *
from util import *

class ListDecomposeNode(Node, SverchCustomTreeNode):
    ''' List devided to multiple sockets in some level '''
    bl_idname = 'ListDecomposeNode'
    bl_label = 'List Decompose'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    # two veriables for multi socket input
    base_name = 'data'
    multi_socket_type = 'StringsSocket'
    
    # two veriables for adaptive socket
    typ = bpy.props.StringProperty(name='typ', default='')
    newsock = bpy.props.BoolProperty(name='newsock', default=False)
    
    level = bpy.props.IntProperty(name='level', default=1,min=0)
    
    def draw_buttons(self, context, layout):
        col = layout.column(align=True)
        col.prop(self,'level')
        
    def init(self, context):
        # initial socket, is defines type of output
        self.inputs.new('StringsSocket', "data", "data")
        # adaptive multy socket
        self.outputs.new('StringsSocket', "data", "data")
        
    def update(self):
        if 'data' in self.inputs and self.inputs['data'].links:
            # get any type socket from input:
            data = SvGetSocketAnyType(self, self.inputs['data'])
            
            # Process data
            leve = min((levelsOflist(data)-2), self.level)
            result = self.beat(data, leve, leve)
            
            # multisocket - from util(formula node)
            multi_socket(self, min=1, start=2,breck=True, output=len(result))
            
            # adaptive socket - from util(mask list node)
            # list to pack and change type of multysockets in output... maybe not so quick
            outputsocketname = [name.name for name in self.outputs]
            changable_sockets(self, 'data', outputsocketname)
            self.multi_socket_type = get_socket_type_full(self, 'data')
            
            # how to assign correct property to adaptive output:
            # in nearest future with socket's data' dictionary we will send
            # only node_name+layout_name+socket_name in str() format
            # and will make separate definition to easyly assign and
            # get and recognise data from dictionary
            for i, out in enumerate(result):
                SvSetSocket(self.outputs[i],out)
                
    def beat(self, data, level, left):
        out=[]
        if left:
            for objects in data:
                out.extend(self.beat(objects,level,left-1))
        elif level:
            if type(data) not in (int, float):
                for objects in data:
                    out.append([self.beat(objects,level-1,0)])
            else:
                return data
        else:
            out.extend([data])
        return out

def register():
    bpy.utils.register_class(ListDecomposeNode)
    
def unregister():
    bpy.utils.unregister_class(ListDecomposeNode)


if __name__ == "__main__":
    register()
