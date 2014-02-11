import bpy, bmesh, mathutils
from mathutils import Vector, Matrix
from node_s import *
from util import *

class ListSortNode(Node, SverchCustomTreeNode):
    ''' List Sort '''
    bl_idname = 'ListSortNode'
    bl_label = 'List Sort'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    level = bpy.props.IntProperty(name = 'level_to_count', default=2, min=0, update=updateNode)
    typ = bpy.props.StringProperty(name='typ', default='')
    newsock = bpy.props.BoolProperty(name='newsock', default=False)
    
    def draw_buttons(self, context, layout):
        layout.prop(self, "level", text="level")
        
    def init(self, context):
        self.inputs.new('StringsSocket', "data", "data")
        self.outputs.new('StringsSocket',"data", "data")

    def update(self):
        if 'data' in self.inputs and len(self.inputs['data'].links)>0:
            # адаптивный сокет
            inputsocketname = 'data'
            outputsocketname = ['data']
            changable_sockets(self, inputsocketname, outputsocketname)

        # достаём два слота - вершины и полики
        if 'data' in self.outputs and len(self.outputs['data'].links)>0 \
                and 'data' in self.inputs and len(self.inputs['data'].links)>0:
            if not self.outputs['data'].node.socket_value_update:
                self.outputs['data'].node.update()
            data_ = SvGetSocketAnyType(self, self.inputs['data'])
            
            # init_level = levelsOflist(data)
            data = dataCorrect(data_, nominal_dept=self.level)
            out_ = []
            for obj in data:
                out_.append(svQsort(obj))
            out = dataCorrect(out_)
            SvSetSocketAnyType(self, 'data', out)
            

    def update_socket(self, context):
        self.update()

def register():
    bpy.utils.register_class(ListSortNode)   
    
def unregister():
    bpy.utils.unregister_class(ListSortNode)

if __name__ == "__main__":
    register()