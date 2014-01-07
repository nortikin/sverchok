import bpy
from mathutils import Vector, Matrix
from node_s import *
from util import *

class ListFuncNode(Node, SverchCustomTreeNode):
    ''' List function '''
    bl_idname = 'ListFuncNode'
    bl_label = 'List function '
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    mode_items = [
        ("MIN",         "Minimum",        ""), 
        ("MAX",         "Maximum",        ""), 
        ("AVR",         "Average",        ""),   
        ]
        
        
    func_=bpy.props.EnumProperty( items = mode_items, name="Function", 
            description="Function choice", default="AVR", update=updateNode)
            
    
    level = bpy.props.IntProperty(name = 'level_to_count', default=2, min=0, update=updateNode)
    
    def draw_buttons(self, context, layout):
        layout.prop(self, "level", text="level")
        layout.prop(self,"func_","Functions:")
        
    def init(self, context):
        self.inputs.new('StringsSocket', "Data", "Data")
        self.outputs.new('StringsSocket',"Function","Function")

    def update(self):
        # достаём два слота - вершины и полики
        if 'Function' in self.outputs and self.outputs['Function'].links:
            if not self.outputs['Function'].node.socket_value_update:
                self.outputs['Function'].node.update()
            if 'Data' in self.inputs and self.inputs['Data'].links:
                if not self.inputs['Data'].node.socket_value_update:
                    self.inputs['Data'].node.update()
                if type(self.inputs['Data'].links[0].from_socket) == StringsSocket:
                    data = eval(self.inputs['Data'].links[0].from_socket.StringsProperty)
                elif type(self.inputs['Data'].links[0].from_socket) == VerticesSocket:
                    data = eval(self.inputs['Data'].links[0].from_socket.VerticesProperty)
                elif type(self.inputs['Data'].links[0].from_socket) == MatrixSocket:
                    data = eval(self.inputs['Data'].links[0].from_socket.MatrixProperty)
                
                if self.func_=='MIN':
                    func=min
                elif self.func_=='MAX':
                    func=max
                else:
                    func=self.avr
                
                if not self.level:
                    out = str([func(data)])
                else:
                    out = str(self.count(data, self.level, func))
                
                self.outputs['Function'].StringsProperty = out
                
            
    def count(self, data, level, func):
        out = []
        if level:
            for obj in data:
                out.append(self.count(obj, level-1, func))
        elif type(data) in [list, tuple] and len(data)>0:
            if len(data)==1:
                data.extend(data)
            out = func(data)
        else:
            pass
        return out
            
    
    def avr(self, data):
        sum_d = 0.0
        flag = True
        for d in data:
            if type(d) not in [float, int]:
                idx_avr = len(data)//2
                result = data[idx_avr]
                flag = False
                break
            
            sum_d += d
            
        if flag:
            result = sum_d / len(data)
        return result
    
    
    def update_socket(self, context):
        self.update()

def register():
    bpy.utils.register_class(ListFuncNode)   
    
def unregister():
    bpy.utils.unregister_class(ListFuncNode)

if __name__ == "__main__":
    register()