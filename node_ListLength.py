import bpy, bmesh, mathutils
from mathutils import Vector, Matrix
from node_s import *
from util import *

class ListLengthNode(Node, SverchCustomTreeNode):
    ''' List Length '''
    bl_idname = 'ListLengthNode'
    bl_label = 'List Length'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    level = bpy.props.IntProperty(name = 'level_to_count', default=2, min=0, update=updateNode)
    
    def draw_buttons(self, context, layout):
        layout.prop(self, "level", text="level")
        
    def init(self, context):
        self.inputs.new('StringsSocket', "Data", "Data")
        self.outputs.new('StringsSocket',"Length","Length")

    def update(self):
        # достаём два слота - вершины и полики
        if 'Length' in self.outputs and self.outputs['Length'].links:
            data = SvGetSocketAnyType(self, self.inputs['Data'])
                
            if not self.level:
                out = str([len(data)])
            else:
                out = str(self.count(data, self.level))
            
            SvSetSocketAnyType(self, 'Length', out)
            
    def count(self, data, level):
        if level:
            out = []
            for obj in data:
                out.append(self.count(obj, level-1))
        elif type(data) not in [float, int]:
            out = [len(data)]
        elif type(data) in [float, int]:
            out = 1
        else:
            pass
        return out
            

    def update_socket(self, context):
        self.update()

def register():
    bpy.utils.register_class(ListLengthNode)   
    
def unregister():
    bpy.utils.unregister_class(ListLengthNode)

if __name__ == "__main__":
    register()