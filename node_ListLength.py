import bpy
from node_s import *
from util import *
import itertools

class ListLengthNode(Node, SverchCustomTreeNode):
    ''' List Length '''
    bl_idname = 'ListLengthNode'
    bl_label = 'List Length'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    level = bpy.props.IntProperty(name = 'level_to_count', default=1, min=0, update=updateNode)
    
    def draw_buttons(self, context, layout):
        layout.prop(self, "level", text="level")
        
    def init(self, context):
        self.inputs.new('StringsSocket', "Data", "Data")
        self.outputs.new('StringsSocket',"Length","Length")

    def update(self):
        # достаём два слота - вершины и полики
        if 'Length' in self.outputs and self.outputs['Length'].links:
            if 'Data' in self.inputs and self.inputs['Data'].links:
                data = SvGetSocketAnyType(self, self.inputs['Data'])
                
                if not self.level:
                    out = [[len(data)]]
                elif self.level == 1:
                    out = [self.count(data, self.level)]
                else:
                    out = self.count(data,self.level)
            
                SvSetSocketAnyType(self, 'Length', out)
         
    def count(self, data, level):
        if isinstance(data, (float, int)):
            return 1  
        if level == 1:
            return [self.count(obj,level-1) for obj in data] 
        elif level == 2:
            out = [self.count(obj,level-1) for obj in data]
            return out
        elif level > 2: # flatten all but last level, we should preserve more detail than this
            out = [self.count(obj,level-1) for obj in data] 
            return [list(itertools.chain.from_iterable(obj)) for obj in out]         
        return len(data)        

    def update_socket(self, context):
        self.update()

def register():
    bpy.utils.register_class(ListLengthNode)   
    
def unregister():
    bpy.utils.unregister_class(ListLengthNode)

if __name__ == "__main__":
    register()