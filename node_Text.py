# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# made by: Linus Yng
#
#

import bpy, bmesh, mathutils
from bpy.props import StringProperty, EnumProperty, BoolProperty
from node_s import *
from util import *
import io
import csv
import collections
import ast


# status colors

FAIL_COLOR = (0.8,0.1,0.1)
READY_COLOR = (0,0.5,0.2)

class SvTextInOp(bpy.types.Operator):
    """ Load text data """
    bl_idname = "node.sverchok_text_input"
    bl_label = "Sverchok text input"
    bl_options = {'REGISTER', 'UNDO'}
    
    # from object in
    name_obj = StringProperty(name='object name')
    name_tree = StringProperty(name='tree name')
    
    def execute(self, context):
        node = bpy.data.node_groups[self.name_tree].nodes[self.name_obj]
        node.load()
        return {'FINISHED'}
      

class SvTextInNode(Node,SverchCustomTreeNode):
    ''' Text Input '''
    bl_idname = 'SvTextInNode'
    bl_label = 'Text Input'
    bl_icon = 'OUTLINER_OB_EMPTY'


    csv_data = {}
           
    def avail_texts(self,context):
        texts = bpy.data.texts
        items = [(t.name,t.name,"") for t in texts]
        return items 
        
    text = EnumProperty(items = avail_texts, name="Texts", 
                        description="Choose text to load", update=updateNode)
    current_text = StringProperty(default = "")
    
    columns = BoolProperty(default=True, options={'ANIMATABLE'})
    names = BoolProperty(default=True, options={'ANIMATABLE'})
                                       
#    formatting options for future implementation
#    decimal = StringProperty(name="Decimal separator", default=".")
#    delimiter = StringProperty(name="Delimiter", default=",")
    

    def init(self, context):
        self.use_custom_color = False
    
        
    def draw_buttons(self, context, layout):
        layout.prop(self,"text","Text Select:")
        layout.prop(self,'columns','Columns')
        layout.prop(self,'names','Named fields?')
        op = layout.operator('node.sverchok_text_input', text='Load')
        op.name_tree = self.id_data.name
        op.name_obj = self.name 
        # should be able to select external file, for now load in text editor

    def update(self):
        # no data, try to reload the data otherwise fail       
        if not self.name in self.csv_data:
            self.load(reload = True)
            if not self.name in self.csv_data:
                self.use_custom_color = True
                self.color = FAIL_COLOR    
                return #nothing loaded
        
        self.use_custom_color = True
        self.color = READY_COLOR
        for item in self.csv_data[self.name]:
            if item in self.outputs and len(self.outputs[item].links)>0:
                if not self.outputs[item].node.socket_value_update:
                    self.outputs[item].node.update()
                self.outputs[item].StringsProperty = str([self.csv_data[self.name][item]])
 
                        
    def update_socket(self, context):
        self.update()

# reload options needs more work to be stable, name check of input and so on

    def load(self, reload = False):
        
        csv_data = collections.OrderedDict() 
        
        if self.name in self.csv_data:
            del self.csv_data[self.name]
            
        if self.current_text == self.text:
            reload = True
        self.current_text = self.text
            
        f = bpy.data.texts[self.current_text].as_string()
        # should be able to select external file, and formatting options
        reader = csv.reader(io.StringIO(f),delimiter=',')
        
        if self.columns:
            for i,row in enumerate(reader):         
                if i == 0: #setup names
                    if self.names:
                        for name in row:
                            tmp = name
                            c = 1
                            while tmp in csv_data:
                                tmp = name+str(c)
                                c += 1
                            csv_data[str(tmp)] = []
                        continue #first row is names    
                    else:
                        for j in range(len(row)):
                            csv_data["Col "+str(j)] = []
                # load data 
                              
                for j,name in enumerate(csv_data):
                    try:
                        csv_data[name].append(float(row[j]))   
                    except (ValueError, IndexError):
                        pass #discard strings other than first row
                        
        else:         #rows            
            for i,row in enumerate(reader):
                name = []
                out = []
                for j,obj in enumerate(row):
                    nr = []
                    try:
                        out.append(float(obj))   
                    except ValueError:
                        if j == 0 and self.names:
                            tmp = row[0]
                            c = 1    
                            while tmp in csv_data:
                                tmp = row[0]+str(c)
                                c += 1
                            name = tmp
                        else:
                            pass #discard strings other than first column

                if not name:
                    name = "Row "+ str(i)
                csv_data[name] = out   
        # store data        
        self.csv_data[self.name]=csv_data
        if not reload:
        # remove sockets
            for out in self.outputs:
                self.outputs.remove(out)
            # create sockets with names, maybe implement reload() in future       
            for name in csv_data:
                self.outputs.new('StringsSocket', name, name)
            
            
# loads a python list using eval
# any python list is considered valid input and you
# have know which socket to use it with, 

# to be merged with above class, do not use
            
class SvRawInNode(Node,SverchCustomTreeNode):
    ''' Raw Text Input - expects a python list '''
    bl_idname = 'SvRawInNode'
    bl_label = 'Sv List Input'
    bl_icon = 'OUTLINER_OB_EMPTY'

    list_data = {}
    
    def avail_texts(self,context):
        texts = bpy.data.texts
        items = [(t.name,t.name,"") for t in texts]
        return items 
    
    text = EnumProperty(items = avail_texts, name="Texts", 
                        description="Choose text file to load", update=updateNode)    

        
    def init(self, context):
        self.use_custom_color = False
        self.outputs.new('VerticesSocket', 'Vertices', 'Vertices')
        self.outputs.new('StringsSocket', 'Data', 'Data')
        self.outputs.new('MatrixSocket', 'Matrix', 'Matrix')
                
    def draw_buttons(self, context, layout):
        layout.prop(self,"text","Text Select:")
        op = layout.operator('node.sverchok_text_input', text='Load')
        op.name_tree = self.id_data.name
        op.name_obj = self.name 
        # should be able to select external file, for now load in text editor

    def update(self):
        # nothing loaded, try to load and if it doesn't work fail             
        if not self.name in self.list_data:
            self.load()
            if not self.name in self.list_data:
                self.use_custom_color=True
                self.color = FAIL_COLOR
                self.reset_sockets()
                return
            
        # load data into connected socket
        for item in ['Vertices','Data','Matrix']:
            if item in self.outputs and len(self.outputs[item].links)>0:
                if not self.outputs[item].node.socket_value_update:
                    self.outputs[item].node.update()
                if item == 'Vertices':
                    self.outputs[item].VerticesProperty = str(self.list_data[self.name])
                if item == 'Data':
                    self.outputs[item].StringsProperty = str(self.list_data[self.name])
                if item == 'Matrix':
                    self.outputs[item].MatrixProperty = str(self.list_data[self.name])        
 
                        
    def update_socket(self, context):
        self.update()
        
    def reset_sockets(self):
        for item in ['Vertices','Data','Matrix']:
            if item in self.outputs:
                if item == 'Vertices':
                    self.outputs[item].VerticesProperty = ""
                if item == 'Data':
                    self.outputs[item].StringsProperty = ""
                if item == 'Matrix':
                    self.outputs[item].MatrixProperty = ""
                    
    def load(self, reload = False):
        
        data = None
                
        if self.name in self.list_data:
            del self.list_data[self.name]
      
        #reset sockets
        self.reset_sockets()
           
        f = bpy.data.texts[self.text].as_string()
        # should be able to select external file
        try:
            data = ast.literal_eval(f)
        except:
            pass
        if type(data) is list:
            self.list_data[self.name] = data
            self.use_custom_color=True
            self.color = READY_COLOR
        else:
            self.use_custom_color=True
            self.color = FAIL_COLOR
        

            
        

def register():
    bpy.utils.register_class(SvTextInOp)
    bpy.utils.register_class(SvTextInNode)

    
def unregister():
    bpy.utils.unregister_class(SvTextInOp)
    bpy.utils.unregister_class(SvTextInNode)

if __name__ == "__main__":
    register()



