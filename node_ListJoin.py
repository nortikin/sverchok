import bpy
from node_s import *
from util import *


class ListJoinNode(Node, SverchCustomTreeNode):
    ''' ListJoin node '''
    bl_idname = 'ListJoinNode'
    bl_label = 'List Join'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    JoinLevel = bpy.props.IntProperty(name='JoinLevel', description='Choose join level of data (see help)', default=1, min=1, update=updateNode)
    Offset_check = bpy.props.BoolProperty(name='Offset', description='Grouping similar to zip()', default=False, update=updateNode)
    Inner_check = bpy.props.BoolProperty(name='Inner', description='Grouping similar to append(list)', default=False, update=updateNode)
    
    def init(self, context):
        self.inputs.new('StringsSocket', "data", "data")
        self.outputs.new('VerticesSocket', 'vertices', 'vertices')
        self.outputs.new('StringsSocket', 'data', 'data')
        self.outputs.new('MatrixSocket', 'matrix', 'matrix')
    
    def check_slots(self, num):
        l = []
        if len(self.inputs)<num+1:
            return False
        for i, sl in enumerate(self.inputs[num:]):   
            if len(sl.links)==0:
                l.append(i+num)
        if l:
            return l
        else:
            return False
    
    def draw_buttons(self, context, layout):
        layout.prop(self, "Offset_check", text="Offset")
        layout.prop(self, "Inner_check", text="Inner")
        layout.prop(self, "JoinLevel", text="JoinLevel lists")
    
    
    def update(self):
        # inputs
        ch = self.check_slots(0)
        if ch and len(self.inputs)>1:
            for c in ch:
                self.inputs.remove(self.inputs[ch[0]])
        slots = []
        typ = ''
        for idx, multi in enumerate(self.inputs[:]):   
             
            if multi.links:
                if not multi.node.socket_value_update:
                    multi.node.update()
                if type(multi.links[0].from_socket) == VerticesSocket:
                    slots.append(eval(multi.links[0].from_socket.VerticesProperty))
                    ch = self.check_slots(2)
                    typ = 'v'
                if type(multi.links[0].from_socket) == StringsSocket:
                    slots.append(eval(multi.links[0].from_socket.StringsProperty))
                    ch = self.check_slots(2)
                    typ = 's'
                if type(multi.links[0].from_socket) == MatrixSocket:
                    slots.append(eval(multi.links[0].from_socket.MatrixProperty))
                    ch = self.check_slots(2)
                    typ = 'm'
        if not ch:
            self.inputs.new('StringsSocket', "data", "data")
        
        
        if 'vertices' in self.outputs and self.outputs['vertices'].links or \
            'data' in self.outputs and self.outputs['data'].links or \
            'matrix' in self.outputs and  self.outputs['matrix'].links:
            list_b=slots.copy()
            if self.Offset_check:
                list_b = myZip(slots,self.JoinLevel)  
                
            if self.Inner_check:
                result = preobrazovatel(list_b,[self.JoinLevel+2])
            else:
                result = preobrazovatel(list_b,[self.JoinLevel+1])
            
            output = [result]

            if len(self.outputs['vertices'].links)>0 and typ == 'v':
                if not self.outputs['vertices'].node.socket_value_update:
                    self.outputs['vertices'].node.update()
                self.outputs['vertices'].links[0].from_socket.VerticesProperty =  str(output)
            if len(self.outputs['data'].links)>0 and typ == 's':
                if not self.outputs['data'].node.socket_value_update:
                    self.outputs['data'].node.update()
                self.outputs['data'].links[0].from_socket.StringsProperty =  str(output)
            if len(self.outputs['matrix'].links)>0 and typ == 'm':
                if not self.outputs['matrix'].node.socket_value_update:
                    self.outputs['matrix'].node.update()
                self.outputs['matrix'].links[0].from_socket.MatrixProperty = str(output)

def register():
    bpy.utils.register_class(ListJoinNode)
    
def unregister():
    bpy.utils.unregister_class(ListJoinNode)

if __name__ == "__main__":
    register()