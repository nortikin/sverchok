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
    level = bpy.props.IntProperty(name = 'level_to_count', default=1, min=0, update=updateNode)
    typ = bpy.props.StringProperty(name='typ', default='')
    newsock = bpy.props.BoolProperty(name='newsock', default=False)
    
    def draw_buttons(self, context, layout):
        layout.prop(self, "level", text="level")
        layout.prop(self,"func_","Functions:")
        
    def init(self, context):
        self.inputs.new('StringsSocket', "Data", "Data")
        self.outputs.new('StringsSocket',"Function","Function")

    def update(self):
        if 'Data' in self.inputs and len(self.inputs['Data'].links)>0:
            # адаптивный сокет
            inputsocketname = 'Data'
            outputsocketname = ['Function']
            changable_sockets(self, inputsocketname, outputsocketname)
            
        if 'Function' in self.outputs and self.outputs['Function'].links:
            if 'Data' in self.inputs and self.inputs['Data'].links:
                data = SvGetSocketAnyType(self, self.inputs['Data'])
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
                
                SvSetSocketAnyType(self, 'Function', out)
                
            
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