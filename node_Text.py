import bpy, bmesh, mathutils
from bpy.props import StringProperty, EnumProperty, BoolProperty
from node_s import *
from util import *
import io
import csv
import collections

class SvTextInOp(bpy.types.Operator):
    """ Load CSV data """
    bl_idname = "node.sverchok_text_input"
    bl_label = "Sverchok text input"
    bl_options = {'REGISTER', 'UNDO'}
    
    name_objectin = StringProperty(name='text file name', description='Name of text buffer')
    
# how to find which node this operator belongs to?
# create operator for each and remove as needed?
 
    def execute(self, context):
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

    csv_data = collections.OrderedDict()
    
    def avail_texts(self,context):
        texts = bpy.data.texts
# should be sorted       items = [(t.name,t.name,"") for t in sorted(texts, key = lambda t : t.name )]
        items = [(t.name,t.name,"") for t in texts]
        return items

    text = EnumProperty(items = avail_texts, name="Texts", 
                        description="Choose text file to load", update=updateNode)
    
    columns = BoolProperty(default=True, options={'ANIMATABLE'})
    names = BoolProperty(default=True, options={'ANIMATABLE'})
                                       
#    formatting options for future 
#    decimal = StringProperty(name="Decimal separator", default=".")
#    delimiter = StringProperty(name="Delimiter", default=",")
    

    def init(self, context):
        pass
                
    def draw_buttons(self, context, layout):
        layout.operator('node.sverchok_text_input', text='Load')
        layout.prop(self,"text","Text Select:")
        row = layout.row()
        row.prop(self,'columns','Columns?')
        row.prop(self,'names','Named fields?')
        # should be able to select external file

    def update(self): 
                 
        for name in self.csv_data:
            if name in self.outputs and len(self.outputs[name].links)>0:
                if not self.outputs[name].node.socket_value_update:
                    self.outputs[name].node.update()
                self.outputs[name].StringsProperty = str([self.csv_data[name]])
 
                        
    def update_socket(self, context):
        self.update()

    def load(self):
        #reset 
        for name in self.csv_data: 
            del self.csv_data[name]
            
        f = bpy.data.texts[self.text].as_string()
        # should be able to select external file
        reader = csv.reader(io.StringIO(f),delimiter=',')
        
        if self.columns:
            for i,row in enumerate(reader):
             
                if i == 0: #setup names
                    if self.names:
                        for name in row:
                            tmp = name
                            while not tmp in self.csv_data:
                                j = 1
                                tmp = name+str(j)
                                j += 1
                            self.csv_data[str(tmp)] = []
                        continue #first row is names    
                    else:
                        for j in range(len(row)):
                            self.csv_data["Col "+str(j)] = []
                # load data               
                for j,name in enumerate(self.csv_data):
                    try:
                        self.csv_data[name].append(float(row[j]))   
                    except (ValueError, IndexError):
                        pass #discard strings other than first
        #rows            
        else: 
            for i,row in enumerate(reader):
                name = []
                out = []
    
                for j,obj in enumerate(row):
                    nr = []
                    try:
                        out.append(float(obj))   
                    except ValueError:
                        if j == 0 and not self.names:
                            name = row[0]
                        else:
                            pass #discard strings other than first

                if not name:
                    name = "Row "+ str(i)
                self.csv_data[name] = out   
        
        #remove sockets
        for out in self.outputs:
            self.outputs.remove(out)
        # create sockets with names, maybe implement update in future       
        for name in self.csv_data:
            self.outputs.new('StringsSocket', name, name)                 
                  
 


def register():
    bpy.utils.register_class(SvTextInOp)
    bpy.utils.register_class(TextInNode)
    
def unregister():
    bpy.utils.unregister_class(SvTextInOp)
    bpy.utils.unregister_class(TextInNode)

if __name__ == "__main__":
    register()



