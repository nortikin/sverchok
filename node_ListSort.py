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
        # адаптивный сокет
        inputsocketname = 'data'
        outputsocketname = ['data']
        changable_sockets(self, inputsocketname, outputsocketname)

        # достаём два слота - вершины и полики
        if 'data' in self.outputs and self.outputs['data'].links /
                    and 'data' in self.inputs and self.inputs['data'].links:
            if not self.outputs['data'].node.socket_value_update:
                self.outputs['data'].node.update()
            #if 'data' in self.inputs and self.inputs['data'].links:
            if not self.inputs['data'].node.socket_value_update:
                self.inputs['data'].node.update()
            if type(self.inputs['data'].links[0].from_socket) == StringsSocket:
                data = eval(self.inputs['data'].links[0].from_socket.StringsProperty)
            elif type(self.inputs['data'].links[0].from_socket) == VerticesSocket:
                data = eval(self.inputs['data'].links[0].from_socket.VerticesProperty)
            elif type(self.inputs['data'].links[0].from_socket) == MatrixSocket:
                data = eval(self.inputs['data'].links[0].from_socket.MatrixProperty)
            
            # init_level = levelsOflist(data)
            data_ = dataCorrect(data, nominal_dept=self.level)
            svQsort(data_)
            out = str(self.count(data, self.level))
            
            self.outputs['data'].StringsProperty = out
            

    def update_socket(self, context):
        self.update()

def register():
    bpy.utils.register_class(ListSortNode)   
    
def unregister():
    bpy.utils.unregister_class(ListSortNode)

if __name__ == "__main__":
    register()