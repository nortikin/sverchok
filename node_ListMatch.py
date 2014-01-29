#
# List Match Node by Linus Yng
#

import bpy
from node_s import *
from util import *
import itertools

# could be moved to util

# longest list matching [[1,2,3,4,5], [10,11]] -> [[1,2,3,4,5], [10,11,11,11,11]]
def match_long_repeat(lsts):
    max_l = 0
    for l in lsts:
        max_l = max(max_l,len(l))
    for l in lsts:
        l.extend(itertools.repeat(l[-1],max_l-len(l)))
    return lsts 

# longest list matching, cycle [[1,2,3,4,5] ,[10,11]] -> [[1,2,3,4,5] ,[10,11,10,11,10]]
def match_long_cycle(lsts):
    max_l = 0
    tmp = []
    for l in lsts:
        max_l = max(max_l,len(l))
    for l in lsts:
        if len(l)==max_l:
            tmp.append(l)
        else:
            tmp.append(itertools.cycle(l))
    return list(map( list, zip(*zip(*tmp))))

# cross matching [[1,2], [5,6,7]] -> [[1,1,1,2,2,2], [5,6,7,5,6,7]]
def match_cross(lsts):
    return list(map(list,zip(*itertools.product(*lsts))))

# Shortest list decides output length [[1,2,3,4,5], [10,11]] -> [[1,2], [10, 11]]   
def match_short(lsts):
    return list(map(list,zip(*zip(*lsts))))

    
class ListMatchNode(Node, SverchCustomTreeNode):
    ''' Stream Matching node '''
    bl_idname = 'ListMatchNode'
    bl_label = 'List Match'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    level = bpy.props.IntProperty(name='level', description='Choose level of data (see help)' \
                                , default=1, min=1, update=updateNode)

    modes = [("SHORT", "Short", "Shortest List",    1),
             ("LONG",   "Long", "Longest List",     2),
             ("XREF",   "X-Ref", "Cross reference", 3)]
    
    long_modes = [("CYCLE", "Cycle", "Cycle through list",  1),
                  ("REPEAT", "Repeat","Repeat Last",        2)]

    mode = bpy.props.EnumProperty(items = modes, default='SHORT', update=updateNode)
    long_mode = bpy.props.EnumProperty(items = long_modes, default='REPEAT',update=updateNode)

    
    def init(self, context):
        self.inputs.new('StringsSocket', 'Data 0', 'Data 0')
        self.inputs.new('StringsSocket', 'Data 1', 'Data 1')
        self.outputs.new('StringsSocket', 'Data 0', 'Data 0')
        self.outputs.new('StringsSocket', 'Data 1', 'Data 1')
    
    
    def draw_buttons(self, context, layout):
        layout.prop(self, "level", text="Level")
        layout.prop(self, "mode", expand = True)
        if self.mode == "LONG":
            layout.prop(self,'long_mode',expand = True)
            
    def match(self,lsts,level,f):
        level -= 1
        if level:
            tmp = self.match([l[0] for l in lsts],level,f)
            return [[l] for l in tmp]  
        elif type(lsts) == list:
            return f(lsts)
        elif type(lsts) == tuple:
            return tuple(f(list(lsts)))
        return None
         
    def update(self):
        # socket handling
        if self.inputs[-1].is_linked:
            name = 'Data '+str(len(self.inputs))
            self.inputs.new('StringsSocket', name, name)
            self.outputs.new('StringsSocket', name, name)
        else:
            while len(self.inputs)>2 and not self.inputs[-2].is_linked:
                self.inputs.remove(self.inputs[-1])
                self.outputs.remove(self.outputs[-1])
        # check number of connections and type match input socket n with output socket n
        count_inputs = 0
        count_outputs = 0     
        for idx,socket in enumerate(self.inputs):
            if self.outputs[socket.name].is_linked:
                count_outputs += 1
            if socket.is_linked:
                count_inputs += 1
                if type(socket.links[0].from_socket) != type(self.outputs[socket.name]):
                    self.outputs.remove(self.outputs[socket.name])
                    self.outputs.new(socket.links[0].from_socket.bl_idname,socket.name,socket.name)
                    self.outputs.move(len(self.outputs)-1,idx)
    
        # check inputs and that there is at least one output
        if count_inputs == len(self.inputs)-1 and count_outputs:                                  
            out = []
            lsts = [] 
            # get data
            for socket in self.inputs:
                if socket.is_linked:
                    lsts.append(SvGetSocketAnyType(self,socket))
        
            if self.mode == 'XREF':
                out = self.match(lsts,self.level,match_cross)
            elif self.mode == 'LONG':
                if self.long_mode == 'CYCLE':
                    out = self.match(lsts,self.level,match_long_cycle)
                else: # REPEAT
                    out = self.match(lsts,self.level,match_long_repeat)
            elif self.mode == 'SHORT':
                out = self.match(lsts,self.level,match_short)
           # output into linked sockets 
            for i,socket in enumerate(self.outputs):
                if i>len(out):
                    break
                if socket.is_linked:
                    SvSetSocketAnyType(self,socket.name,out[i])
            

def register():
    bpy.utils.register_class(ListMatchNode)
    
def unregister():
    bpy.utils.unregister_class(ListMatchNode)

if __name__ == "__main__":
    register()