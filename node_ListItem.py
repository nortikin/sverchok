import bpy
from node_s import *
from util import *

# supports of older code, remove soon
# Linus Yng, Feb 4, 2014

class ListItemNode(Node, SverchCustomTreeNode):
    ''' List item '''
    bl_idname = 'ListItemNode'
    bl_label = 'List item old'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    level = bpy.props.IntProperty(name = 'level_to_count', default=2, min=0, update=updateNode)
    item = bpy.props.IntProperty(name = 'item', default=0, update=updateNode)
    typ = bpy.props.StringProperty(name='typ', default='')
    newsock = bpy.props.BoolProperty(name='newsock', default=False)
    
    def draw_buttons(self, context, layout):
        layout.prop(self, "level", text="level")
        layout.prop(self, "item", text="item")
        
    def init(self, context):
        self.inputs.new('StringsSocket', "Data", "Data")
        self.outputs.new('StringsSocket',"Item","Item")
        self.outputs.new('StringsSocket',"Other","Other")

    def update(self):
        if 'Data' in self.inputs and len(self.inputs['Data'].links)>0:
            # адаптивный сокет
            inputsocketname = 'Data'
            outputsocketname = ['Item','Other']
            changable_sockets(self, inputsocketname, outputsocketname)
            
        if 'Item' in self.outputs and self.outputs['Item'].links or \
                'Other' in self.outputs and self.outputs['Other'].links:
            
            if 'Data' in self.inputs and self.inputs['Data'].links:
                data = SvGetSocketAnyType(self, self.inputs['Data'])
                
                if 'Item' in self.outputs and self.outputs['Item'].links:
                    out = self.count(data, self.level-1, self.item, True)
                    SvSetSocketAnyType(self, 'Item', out)
                if 'Other' in self.outputs and self.outputs['Other'].links:
                    out = self.count(data, self.level-1, self.item, False)
                    SvSetSocketAnyType(self, 'Other', out)
            
    def count(self, data, level, item, itself):
        if level:
            out = []
            for obj in data:
                out.append(self.count(obj, level-1, item, itself))
                
        elif type(data) == tuple:
            if item > len(data)-1:
                item = len(data)-1
            if itself:
                out = [data[item]]
            else:
                out = [data[:item]+data[item+1:]]
        elif type(data) == list:
            if item > len(data)-1:
                item = len(data)-1
            if itself:
                out = [data[item]]
            else:
                data.pop(item)
                out = [data]
        else:
            out = None
        return out
            

    def update_socket(self, context):
        self.update()
        
# ListItem2
# Allows a list of items, with both negative and positive index and repeated values
# Other output is not wrapped.
# Based on ListItem
# For now only accepts one list of items
# by Linus Yng

             
class ListItem2Node(Node, SverchCustomTreeNode):
    ''' List item '''
    bl_idname = 'ListItem2Node'
    bl_label = 'List item'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    level = bpy.props.IntProperty(name = 'level_to_count', default=2, min=0, update=updateNode)
    item = bpy.props.IntProperty(name = 'item', default=0, update=updateNode)
    typ = bpy.props.StringProperty(name='typ', default='')
    newsock = bpy.props.BoolProperty(name='newsock', default=False)
    
    def draw_buttons(self, context, layout):
        layout.prop(self, "level", text="level")
        
    def init(self, context):
        self.inputs.new('StringsSocket', "Data", "Data")
        self.inputs.new('StringsSocket', "Item", "Item").prop_name = 'item'
        self.outputs.new('StringsSocket',"Item","Item")
        self.outputs.new('StringsSocket',"Other","Other")

    def update(self):
        if 'Data' in self.inputs and len(self.inputs['Data'].links)>0:
            inputsocketname = 'Data'
            outputsocketname = ['Item','Other']
            changable_sockets(self, inputsocketname, outputsocketname)
        
        if 'Item' in self.outputs and self.outputs['Item'].links or \
                'Other' in self.outputs and self.outputs['Other'].links:
            
            if 'Data' in self.inputs and self.inputs['Data'].links:
                data = SvGetSocketAnyType(self, self.inputs['Data'])
                
                if 'Item' in self.inputs and self.inputs['Item'].links:
                    items = SvGetSocketAnyType(self,self.inputs['Item'])
                else:
                    items = [[self.item]]
                    
                if 'Item' in self.outputs and self.outputs['Item'].links:
                    if self.level-1:
                        out = self.get(data, self.level-1, items,self.get_items)
                    else:
                        out = self.get_items(data, items[0])
                    SvSetSocketAnyType(self, 'Item', out)
                if 'Other' in self.outputs and self.outputs['Other'].links:
                    if self.level-1:
                        out = self.get(data, self.level-1,items,self.get_other)
                    else:
                        out = self.get_other(data, items[0])
                    SvSetSocketAnyType(self, 'Other', out)
            
    def get_items(self,data, items):
        if type(data) in [list, tuple]:
            return [data[item] for item in items if item < len(data) and item >= -len(data)]
        else:
            return None
    
    def get_other(self, data, items):
        is_tuple = False
        if type(data) == tuple:
            data = list(data)
            is_tuple = True
        if type(data) == list:   
            m_items = items.copy() 
            for idx,item in enumerate(items):
                if item < 0:
                    m_items[idx] = len(data)-abs(item)
            for i in sorted(set(m_items), reverse = True):
                if i < len(data) and i > -1:
                    del data[i]
            if is_tuple:
                return tuple(data)
            else:
                return data
        else:
            return None
            
    def get(self, data, level, items,f):
        if level == 1:
            item_iter = repeat_last(items)
            return [self.get(obj,level-1,next(item_iter),f) for obj in data]
        elif level:
            return [self.get(obj,level-1,items,f) for obj in data]
        else:   
            return f(data,items)
        
    def update_socket(self, context):
        self.update()

def register():
    bpy.utils.register_class(ListItemNode)   
    bpy.utils.register_class(ListItem2Node)   
    
def unregister():
    bpy.utils.unregister_class(ListItemNode)
    bpy.utils.unregister_class(ListItem2Node)


if __name__ == "__main__":
    register()
