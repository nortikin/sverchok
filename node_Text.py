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

import bpy
from bpy.props import StringProperty, EnumProperty, BoolProperty
from node_s import *
from util import *
import io
import csv
import collections
import ast
import locale
import json
import itertools

# TODO, 
# load and dump to/from external file
# update stability, do not disconnect unless something changed
# fix colors for TextOut
# 


# status colors

FAIL_COLOR = (0.8,0.1,0.1)
READY_COLOR = (0,0.5,0.2)

# utility function    
def new_output_socket(node,name,type):
    if type == 'v':
        node.outputs.new('VerticesSocket',name,name)
    if type == 's':
        node.outputs.new('StringsSocket',name,name)
    if type == 'm':
        node.outputs.new('MatrixSocket',name,name)
        
        
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
    list_data = {}
    json_data = {}

# general settings
           
    def avail_texts(self,context):
        texts = bpy.data.texts
        items = [(t.name,t.name,"") for t in texts]
        return items 
        
    text = EnumProperty(items = avail_texts, name="Texts", 
                        description="Choose text to load", update=updateNode)
    
    text_modes = [("CSV", "Csv", "Csv data","",1),
                  ("SV", "Sverchok","Python data","",2),
                  ("JSON", "JSON", "Sverchok JSON",3)]  
                
    textmode = EnumProperty(items = text_modes, default='CSV',update=updateNode,)

# name of loaded text, to support reloading    
    current_text = StringProperty(default = "")
# external file
    file = StringProperty(subtype='FILE_PATH')
                           
# csv standard dialect as defined in http://docs.python.org/3.3/library/csv.html
# below are csv settings, user defined are set to 10 to allow more settings be added before
# user defined. 
# to add ; as delimiter and , as decimal mark 
 
    csv_dialects = [( 'excel',      'Excel',        'Standard excel',   1),
                    ( 'excel-tab',  'Excel tabs',   'Excel tab format', 2),
                    ( 'unix',       'Unix',         'Unix standard',    3),
                    ( 'semicolon',  'Excel ;,',     'Excel ; ,',        4),
                    ( 'user',       'User defined', 'Define settings',10),]
                    
                    
    csv_dialect = EnumProperty(items = csv_dialects, name="Csv Dialect", 
                        description="Choose csv dialect", default='excel', update=updateNode)
                        
    csv_delimiters = [(',',  ",",    "Comma: ,",    1),
                     ('\t', 'tab',  "Tab",          2),
                     (';',  ';',    "Semi-colon ;", 3),
                     ('CUSTOM', 'custom',"Custom",  10),]
                     
    csv_delimiter = EnumProperty(items = csv_delimiters, default=',')
    csv_custom_delimiter =  StringProperty(default=':')
    
    csv_decimalmarks = [('.',       ".",        "Dot",          1),
                        (',',       ',',        "Comma",        2),
                        ('LOCALE',  'Locale',   "Follow locale",3),
                        ('CUSTOM', 'custom',    "Custom",       10),]
                        
    csv_decimalmark = EnumProperty(items = csv_decimalmarks, default='LOCALE')
    csv_custom_decimalmark = StringProperty(default=',')
    csv_header = BoolProperty(default=False)                                  

# Sverchok list options
# choose which socket to interpretate data as
    socket_types = [('v', 'Vertices',  "Point, vector or vertices data",1),
                   ('s', 'Data',    "Generals numbers or edge polygon data",2),
                   ('m', 'Matrix',  "Matrix data",3),]
    socket_type = EnumProperty(items = socket_types, default='s')
    
    def draw_buttons(self, context, layout):
        
        layout.prop(self,"text","Select Text")
    #    layout.prop(self,"file","File") external file, TODO
        layout.prop(self,'textmode','textmode',expand=True)
        if self.textmode == 'CSV':
            layout.prop(self,'csv_header','Header fields')
            layout.prop(self,'csv_dialect','Dialect')
            if self.csv_dialect == 'user':
                layout.label(text="Delimiter")
                layout.prop(self, 'csv_delimiter',"Delimiter", expand = True)
                if self.csv_delimiter == 'CUSTOM':
                    layout.prop(self,'csv_custom_delimiter',"Custom")
                
                layout.label(text="Decimalmark")
                layout.prop(self, 'csv_decimalmark',"Decimalmark", expand = True)
                if self.csv_decimalmark == 'CUSTOM':
                    layout.prop(self,'csv_custom_decimalmark',"Custom")   

        if self.textmode == 'SV':
            layout.label(text="Select data type")
            layout.prop(self,'socket_type',expand = True)
            
        if self.textmode == 'JSON': # self documenting format
            pass        
                    
        op = layout.operator('node.sverchok_text_input', text='Load')
        op.name_tree = self.id_data.name
        op.name_obj = self.name 
      
    # dispatch functions
    
    def update(self): #dispatch based on mode
        if self.textmode == 'CSV':
            self.update_csv()
        elif self.textmode == 'SV':
            self.update_sv()
        elif self.textmode == 'JSON':
            self.update_json()


    def load(self, reload = False):
        if self.textmode == 'CSV':
            self.load_csv()
        elif self.textmode =='SV':
            self.load_sv()
        elif self.textmode =='JSON':
            self.load_json()

    def update_socket(self, context):
        self.update()  
#
# CSV methods. 
#            
    def update_csv(self):
        if not self.name in self.csv_data:
            self.use_custom_color = True
            self.color = FAIL_COLOR    
            return           
            
        self.use_custom_color = True
        self.color = READY_COLOR
        for item in self.csv_data[self.name]:
            if item in self.outputs and self.outputs[item].links:
                SvSetSocketAnyType(self,item,[self.csv_data[self.name][item]])

 
 
# reload options needs more work to be stable, name check of input and so on
            
    def load_csv(self, reload = False):
        
        csv_data = collections.OrderedDict() 
        
        if self.name in self.csv_data:
            del self.csv_data[self.name]
            
       #  if self.current_text == self.text:
#             reload = True
        self.current_text = self.text
            
        f = io.StringIO(bpy.data.texts[self.current_text].as_string())

        # setup CSV options

        if self.csv_dialect == 'user':
            if self.csv_delimiter == 'CUSTOM':
                d = self.csv_custom_delimiter
            else:
                d = self.csv_delimiter
                
            reader = csv.reader(f,delimiter=d)
        elif self.csv_dialect == 'semicolon':
            self.csv_decimalmark = ','
            reader = csv.reader(f,delimiter = ';')
        else:
            reader = csv.reader(f,dialect=self.csv_dialect)
            self.csv_decimalmark = '.'

        # setup parse decimalmark
            
        if self.csv_decimalmark == ',':
            get_number = lambda s: float(s.replace(',','.'))
        elif self.csv_decimalmark == 'LOCALE':
            get_number = lambda s: locale.atof(s)  
        elif self.csv_decimalmark == 'CUSTOM':
            if self.csv_custom_decimalmark :
                get_number = lambda s: float(s.replace(self.csv_custom_decimalmark,'.'))
        else: # . default
            get_number = float        
            
    # load data
        for i,row in enumerate(reader):         
            if i == 0: #setup names
                if self.csv_header:
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
                    csv_data[name].append(get_number(row[j]))   
                except (ValueError, IndexError):
                    pass #discard strings other than first row

# no row styled data in standard csv, let us follow that                        
#         else:         #rows            
#             for i,row in enumerate(reader):
#                 name = []
#                 out = []
#                 for j,obj in enumerate(row):
#                     nr = []
#                     try:
#                         out.append(float(obj))   
#                     except ValueError:
#                         if j == 0 and self.names:
#                             tmp = row[0]
#                             c = 1    
#                             while tmp in csv_data:
#                                 tmp = row[0]+str(c)
#                                 c += 1
#                             name = tmp
#                         else:
#                             pass #discard strings other than first column
# 
#                 if not name:
#                     name = "Row "+ str(i)
#                 csv_data[name] = out   
#         # store data

        print(csv_data)
        self.csv_data[self.name]=csv_data
        if not reload:
        # remove sockets
            self.outputs.clear()
            # create sockets with names, maybe implement reload() in future       
            for name in csv_data:
                self.outputs.new('StringsSocket', name, name)

#
# Sverchok list data
#
# loads a python list using eval
# any python list is considered valid input and you
# have know which socket to use it with. 
            
    def load_sv(self, reload = False):
        data = None
        name_dict = {'m':'Matrix','s':'Data','v':'Vertices'}
            
        if self.name in self.list_data:
            del self.list_data[self.name]
      
        #reset sockets
        for i in range(len(self.outputs)):
            self.outputs.remove(self.outputs[0])
             
        f = bpy.data.texts[self.text].as_string()
        # should be able to select external file
        try:
            data = ast.literal_eval(f)
        except:
            pass
        if type(data) is list:
            typ = self.socket_type
            new_output_socket(self,name_dict[typ],typ)
            self.list_data[self.name] = data
            self.use_custom_color=True
            self.color = READY_COLOR
            
        else:
            self.use_custom_color=True
            self.color = FAIL_COLOR    
            
    def update_sv(self):
        # nothing loaded, try to load and if it doesn't work fail             
        if not self.name in self.list_data:
            self.use_custom_color=True
            self.color = FAIL_COLOR
            return
            
        # load data into selected socket
        for item in ['Vertices','Data','Matrix']:
            if item in self.outputs and len(self.outputs[item].links)>0:
                SvSetSocketAnyType(self,item, str(self.list_data[self.name]))
#
# JSON
#
# Loads JSON data    
#
# format dict {socket_name : (socket type in ['v','m','s'], list data)
#              socket_name1 :etc. 
# socket_name must be unique

    def load_json(self, reload = False):
        json_data = {}
       
        #reset data        
        if self.name in self.json_data:
            del self.json_data[self.name]

        #reset sockets
        for i in range(len(self.outputs)):
            self.outputs.remove(self.outputs[-1])
                       
       #  if self.current_text == self.text:
#             reload = True
        self.current_text = self.text
            
        f = io.StringIO(bpy.data.texts[self.current_text].as_string())
        try:
            json_data = json.load(f)
        except:
            pass
        #create sockets   

        for item in json_data:
            data = json_data[item]
            if len(data) == 2 and data[0] in ['v','s','m']:                                 
                new_output_socket(self,item,data[0])
            else: # someting is wrong
                self.use_custom_color=True
                self.color = FAIL_COLOR       
                return
                
        self.json_data[self.name]=json_data         
        
    def update_json(self):
        if not self.name in self.json_data:
            self.use_custom_color=True
            self.color = FAIL_COLOR
            return
        
        self.use_custom_color=True
        self.color = READY_COLOR          
        
        for item in self.json_data[self.name]:
            if item in self.outputs and len(self.outputs[item].links)>0:
                out = self.json_data[self.name][item][1]
                SvSetSocketAnyType(self, item, out)
                

########################################################################################
#
# Text Output
#
########################################################################################
        
class SvTextOutOp(bpy.types.Operator):
    """ Dumps text data """
    bl_idname = "node.sverchok_text_output"
    bl_label = "Sverchok text output"
    bl_options = {'REGISTER', 'UNDO'}
    
    # from object in
    name_obj = StringProperty(name='object name')
    name_tree = StringProperty(name='tree name')
    
    def execute(self, context):
        node = bpy.data.node_groups[self.name_tree].nodes[self.name_obj]
        out = node.get_data()
        if len(out) == 0:
            return {'FINISHED'}
        bpy.data.texts[node.text].clear()
        bpy.data.texts[node.text].write(out)
        return {'FINISHED'}
            
            
class SvTextOutNode(Node,SverchCustomTreeNode):
    ''' Text Output Node '''
    bl_idname = 'SvTextOutNode'
    bl_label = 'Text Output'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    def avail_texts(self, context):
        texts = bpy.data.texts
        items = [(t.name,t.name,"") for t in texts]
        return items 

    def change_mode(self, context):
        self.inputs.clear()
        
        if self.text_mode == 'CSV':
            self.inputs.new('StringsSocket','Col 0','Col 0')
            self.base_name = 'Col '
        if self.text_mode == 'JSON':
            self.inputs.new('StringsSocket','Data 0','Data 0')
            self.base_name = 'Data '
        if self.text_mode == 'SV':
            self.inputs.new('StringsSocket','Data','Data')
                        
            
    text = EnumProperty(items = avail_texts, name="Texts", 
                        description="Choose text to load", update=updateNode)
  
    text_modes = [("CSV",   "Csv",      "Csv data","",  1),
                  ("SV",    "Sverchok", "Python data",  2),
                  ("JSON",  "JSON",     "Sverchok JSON",3)]  
    
    text_mode = EnumProperty(items = text_modes, default='CSV',update=change_mode)
    
     
    csv_dialects = [( 'excel',      'Excel',        'Standard excel',   1),
                    ( 'excel-tab',  'Excel tabs',   'Excel tab format', 2),
                    ( 'unix',       'Unix',         'Unix standard',    3),]
                    
    csv_dialect = EnumProperty(items = csv_dialects, default='excel')                    

    base_name = StringProperty(name='base_name',default='Col ')
    multi_socket_type = StringProperty(name='multi_socket_type',default='StringsSocket')

    def init(self,context):
        self.inputs.new('StringsSocket','Col 0','Col 0')

    def draw_buttons(self, context, layout):
    
        layout.prop(self,'text',"Select text")
    
        layout.label("Select output format")
        layout.prop(self,'text_mode',"Text format",expand = True)
        
        if self.text_mode == 'CSV':
            layout.prop(self,'csv_dialect',"Dialect")                
    
        op = layout.operator('node.sverchok_text_output', text='Dump')
        op.name_tree = self.id_data.name
        op.name_obj = self.name      
    
    
    def update_socket(self, context):
        self.update()
        

    #manage sockets
    # does not do anything with data until dump is executed
    
    def update(self):
        if self.text_mode == 'CSV' or self.text_mode == 'JSON':
            multi_socket(self,min=1)
        elif self.text_mode == 'SV':
            pass #only one input, do nothing
  
    # build a string with data from sockets        

    def get_data(self):
        out = ""
        if self.text_mode == 'CSV':
            data_out = []
            for socket in self.inputs:
                if socket.links and \
                    type(socket.links[0].from_socket) == StringsSocket:
                    
                    tmp = SvGetSocketAnyType(self,socket)
                    if len(tmp):
                        # flatten list
                        data_out.append(list(itertools.chain.from_iterable(tmp)))
                        
            csv_str = io.StringIO()
            writer = csv.writer(csv_str,dialect=self.csv_dialect)
            for row in zip(*data_out):
                writer.writerow(row)   
                             
            out = csv_str.getvalue()    
                
        elif self.text_mode == 'JSON':
            data_out = {}
            name_dict = {'m':'Matrix','s':'Data','v':'Vertices'}

            for item in self.inputs:
                if item.links:
                    tmp = SvGetSocketAnyType(self, item)
                    if len(tmp):
                        tmp_name = name_dict[get_socket_type(self,item.name)]
                        name = tmp_name
                        j = 1
                        while name in data_out: #unique names for json
                            name = tmp_name+str(j)
                            j += 1
                            
                        data_out[name] = (get_socket_type(self,item.name),tmp)
            out = json.dumps(data_out,indent=4)    
            
        elif self.text_mode == 'SV':
            if self.inputs['Data'].links:
                out = str(SvGetSocketAnyType(self,self.inputs['Data']))
        
        return out
    
def register():
    bpy.utils.register_class(SvTextInOp)
    bpy.utils.register_class(SvTextInNode)
    bpy.utils.register_class(SvTextOutOp)
    bpy.utils.register_class(SvTextOutNode)

    
def unregister():
    bpy.utils.unregister_class(SvTextInOp)
    bpy.utils.unregister_class(SvTextInNode)
    bpy.utils.unregister_class(SvTextOutOp)
    bpy.utils.unregister_class(SvTextOutNode)

if __name__ == "__main__":
    register()

