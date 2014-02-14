#
# List Match Node by Linus Yng
#

import bpy
from node_s import *
from util import *
import itertools

# could be moved to util



    
class ListMatchNode(Node, SverchCustomTreeNode):
    ''' Stream Matching node '''
    bl_idname = 'ListMatchNode'
    bl_label = 'List Match'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    level = bpy.props.IntProperty(name='level', description='Choose level of data (see help)' \
                                , default=1, min=1, update=updateNode)

    modes = [("SHORT", "Short", "Shortest List",    1),
             ("CYCLE",   "Cycle", "Longest List",   2),
             ("REPEAT",   "Repeat", "Longest List", 3),
             ("XREF",   "X-Ref", "Cross reference", 4)]
    
    mode = bpy.props.EnumProperty(items = modes, default='REPEAT',update=updateNode)
    mode_final = bpy.props.EnumProperty(items = modes, default='REPEAT',update=updateNode)
  
    def init(self, context):
        self.inputs.new('StringsSocket', 'Data 0', 'Data 0')
        self.inputs.new('StringsSocket', 'Data 1', 'Data 1')
        self.outputs.new('StringsSocket', 'Data 0', 'Data 0')
        self.outputs.new('StringsSocket', 'Data 1', 'Data 1')
      
    def draw_buttons(self, context, layout):
        layout.prop(self, "level", text="Level")
        layout.label("Recurse/Final")
        layout.prop(self, "mode", expand = True)
        layout.prop(self, "mode_final", expand = True)
   
# recursive update of match function, now performs match function until depth
# works for short&long and simple scenarios. respect sub lists
# matches until the chosen level
# f2 is applied to the final level of matching,
# f1 is applied to every level until the final, where f2 is used.

    def match(self,lsts,level,f1,f2):
        level -= 1  
        if level:
            tmp=[self.match(obj,level,f1,f2) for obj in zip(*f1(lsts))]
            return list(map(list,zip(*tmp)))
        elif type(lsts) == list:
            return f2(lsts)
        elif type(lsts) == tuple:
            return tuple(f2(list(lsts)))
        return None
         
    def update(self):
        # inputs
        # these functions are in util.py
        func_dict = { 
            'SHORT': match_short,
            'CYCLE': match_long_cycle,
            'REPEAT': match_long_repeat,
            'XREF': match_cross2
            }
        
        # socket handling
        if self.inputs[-1].links:
            name = 'Data '+str(len(self.inputs))
            self.inputs.new('StringsSocket', name, name)
            self.outputs.new('StringsSocket', name, name)
        else:
            while len(self.inputs)>2 and not self.inputs[-2].links:
                self.inputs.remove(self.inputs[-1])
                self.outputs.remove(self.outputs[-1])
        # check number of connections and type match input socket n with output socket n
        count_inputs = 0
        count_outputs = 0     
        for idx,socket in enumerate(self.inputs):
            if socket.name in self.outputs and self.outputs[socket.name].links:
                count_outputs += 1
            if socket.links:
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
                if socket.links:
                    lsts.append(SvGetSocketAnyType(self,socket))
            try:
                out = self.match(lsts,self.level,func_dict[self.mode],func_dict[self.mode_final])
            except:
                print(self.name," failed")
                
           # output into linked sockets s
            for i,socket in enumerate(self.outputs):
                if i==len(out): #never write to last socket
                    break
                if socket.links:
                    SvSetSocketAnyType(self,socket.name,out[i])
            

def register():
    bpy.utils.register_class(ListMatchNode)
    
def unregister():
    bpy.utils.unregister_class(ListMatchNode)

if __name__ == "__main__":
    register()