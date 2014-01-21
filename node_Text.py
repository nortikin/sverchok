import bpy, bmesh, mathutils
from bpy.props import StringProperty, EnumProperty
from node_s import *
from util import *
import io
import csv

class SvTextInOp(bpy.types.Operator):
    """ Load CSV data """
    bl_idname = "node.sverchok_text_input"
    bl_label = "Sverchok text input"
    bl_options = {'REGISTER', 'UNDO'}
    
    name_objectin = StringProperty(name='text file name', description='Name of text buffer')
    

    def execute(self, context):
        print(context.active_node.name)
        node = context.active_node
        if not type(node) is TextInNode:
            print("wrong type")
            return {'CANCELLED'}
        node.load()
        return {'FINISHED'}
    
class TextInNode(Node, SverchCustomTreeNode):
    ''' Text Input '''
    bl_idname = 'TextInNode'
    bl_label = 'Text Input'
    bl_icon = 'OUTLINER_OB_EMPTY'

    csv_data = {}
    changed = False
    
    def avail_texts(self,context):
        texts = bpy.data.texts
        items = [(t.name,t.name,"") for i,t in enumerate(texts)]
        return items

    text = EnumProperty(items = avail_texts, name="Texts", 
                        description="Choose text file to load", update=updateNode)
                                      
    decimal = StringProperty(name="Decimal separator", default=".")
    delimiter = StringProperty(name="Delimiter", default=",")
    

    def init(self, context):
        self.update_texts()
        
        
    def draw_buttons(self, context, layout):
        layout.operator('node.sverchok_text_input', text='Load')
        layout.prop(self,"text","Text Select:");

    def update(self): 
  
        #remove sockets
        for out in self.outputs:
            if not out.name in self.csv_data:
                self.outputs.remove[out.name]
                
        for name in self.csv_data:
            print(name)
            if not name in self.outputs:
 #               print("new socket",name)
                self.outputs.new('StringsSocket', name, name) 
                
    #    print("hello update()",self.csv_data)
        for name in self.csv_data:
            if name in self.outputs and len(self.outputs[name].links)>0:
                if not self.outputs[name].node.socket_value_update:
                    self.outputs[name].node.update()
                self.outputs[name].StringsProperty = str([self.csv_data[name]])
 
                        
    def update_socket(self, context):
        self.update()

    def load(self):
        #reset 
        self.changed = True
             
        f = bpy.data.texts[self.text].as_string()
        reader = csv.reader(io.StringIO(f),delimiter=',')
        
        for i,row in enumerate(reader):
            name = []
            out = []
    
            for j,obj in enumerate(row):
                nr = []
                try:
                    out.append(float(obj))   
                except ValueError:
                    if j == 0:
                        name = row[0]
                    else:
                        pass #discard strings other than first

            if not name:
                name = "Row "+ str(i)
            self.csv_data[name] = out   
        
        print(self.csv_data) 
                
                  
 


def register():
    bpy.utils.register_class(SvTextInOp)
    bpy.utils.register_class(TextInNode)
    
def unregister():
    bpy.utils.unregister_class(SvTextInOp)
    bpy.utils.unregister_class(TextInNode)

if __name__ == "__main__":
    register()



