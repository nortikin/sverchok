import bpy, bmesh, mathutils
from mathutils import Vector, Matrix
from node_s import *
from util import *

class ListFLNode(Node, SverchCustomTreeNode):
    ''' List First and last item of list '''
    bl_idname = 'ListFLNode'
    bl_label = 'List First Last'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    level = bpy.props.IntProperty(name = 'level_to_count', default=2, min=0, update=updateNode)
    
    def draw_buttons(self, context, layout):
        layout.prop(self, "level", text="level")
        
    def init(self, context):
        self.inputs.new('StringsSocket', "Data", "Data")
        self.outputs.new('StringsSocket',"First","First")
        self.outputs.new('StringsSocket',"Last","Last")

    def update(self):
        # достаём два слота - вершины и полики
        if 'First' in self.outputs and self.outputs['First'].links or \
                'Last' in self.outputs and self.outputs['Last'].links:
            if not self.outputs['First'].node.socket_value_update:
                self.outputs['First'].node.update()
            if not self.outputs['Last'].node.socket_value_update:
                self.outputs['Last'].node.update()
            if 'Data' in self.inputs and self.inputs['Data'].links:
                if not self.inputs['Data'].node.socket_value_update:
                    self.inputs['Data'].node.update()
                if type(self.inputs['Data'].links[0].from_socket) == StringsSocket:
                    data = eval(self.inputs['Data'].links[0].from_socket.StringsProperty)
                elif type(self.inputs['Data'].links[0].from_socket) == VerticesSocket:
                    data = eval(self.inputs['Data'].links[0].from_socket.VerticesProperty)
                elif type(self.inputs['Data'].links[0].from_socket) == MatrixSocket:
                    data = eval(self.inputs['Data'].links[0].from_socket.MatrixProperty)
                
                
                if 'First' in self.outputs and self.outputs['First'].links:
                    out = self.count(data, self.level, True)
                    self.outputs['First'].StringsProperty = str(out)  
                if 'Last' in self.outputs and self.outputs['Last'].links:
                    out = self.count(data, self.level, False)
                    self.outputs['Last'].StringsProperty = str(out)
            
    def count(self, data, level, First):
        if level:
            out = []
            for obj in data:
                out.append(self.count(obj, level-1, First))
        elif type(data) not in [int, float]:
            if First:
                out = [data[0]]
            else:
                out = [data[-1]]
        return out
            

    def update_socket(self, context):
        self.update()

def register():
    bpy.utils.register_class(ListFLNode)   
    
def unregister():
    bpy.utils.unregister_class(ListFLNode)

if __name__ == "__main__":
    register()