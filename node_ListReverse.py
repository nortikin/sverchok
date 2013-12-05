import bpy
from node_s import *
from util import *



class ListReverseNode(Node, SverchCustomTreeNode):
    ''' List Reverse Node '''
    bl_idname = 'ListReverseNode'
    bl_label = 'List Reverse'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    level = bpy.props.IntProperty(name = 'level_to_Reverse', default=2, min=1, update=updateNode)
    
    def draw_buttons(self, context, layout):
        layout.prop(self, "level", text="level")
    
    def init(self, context):
        self.inputs.new('StringsSocket', "data", "data")
        self.outputs.new('VerticesSocket', 'vertices', 'vertices')
        self.outputs.new('StringsSocket', 'data', 'data')
        self.outputs.new('MatrixSocket', 'matrix', 'matrix')
    

    def update(self):
        # inputs
        typ = 's'
        data = [[]]
        
        if not self.inputs['data'].node.socket_value_update:
            self.inputs['data'].node.update()
        if self.inputs['data'].links and \
            type(self.inputs['data'].links[0].from_socket) == VerticesSocket:
            data = eval(self.inputs['data'].links[0].from_socket.VerticesProperty)
            typ = 'v'
        if self.inputs['data'].links and \
            type(self.inputs['data'].links[0].from_socket) == StringsSocket:
            data = eval(self.inputs['data'].links[0].from_socket.StringsProperty)
            typ = 's'
        if self.inputs['data'].links and \
            type(self.inputs['data'].links[0].from_socket) == MatrixSocket:
            data = eval(self.inputs['data'].links[0].from_socket.MatrixProperty)
            typ = 'm'
           
        
        output = self.revers(data, self.level)  
        #print('\nshift output',output, '\n --- ', typ, data, number, self.enclose)
        
        if 'vertices' in self.outputs and len(self.outputs['vertices'].links)>0 and typ == 'v':
            if not self.outputs['vertices'].node.socket_value_update:
                self.outputs['vertices'].node.update()
            self.outputs['vertices'].VerticesProperty =  str(output)
            
        if 'data' in self.outputs and len(self.outputs['data'].links)>0 and typ == 's':
            if not self.outputs['data'].node.socket_value_update:
                self.outputs['data'].node.update()
            self.outputs['data'].StringsProperty =  str(output)
            
        if 'matrix' in self.outputs and len(self.outputs['matrix'].links)>0 and typ == 'm':
            if not self.outputs['matrix'].node.socket_value_update:
                self.outputs['matrix'].node.update()
            self.outputs['matrix'].MatrixProperty = str(output)


    def revers(self, list, level):
        level -= 1
        if level:
            out = []
            for l in list:
                out.append(self.revers(l, level))
            return out
        elif type(list) in [type([])]:
            #print (type(list))
            list.reverse()
            return list
        elif type(list) in [type(tuple())]:
            out = list[::-1]
            return out
            
        


def register():
    bpy.utils.register_class(ListReverseNode)
    
def unregister():
    bpy.utils.unregister_class(ListReverseNode)

if __name__ == "__main__":
    register()