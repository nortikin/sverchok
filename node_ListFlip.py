import bpy
from node_s import *
from util import *


class ListFlipNode(Node, SverchCustomTreeNode):
    ''' ListFlipNode '''
    bl_idname = 'ListFlipNode'
    bl_label = 'List Flip Node'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    level = bpy.props.IntProperty(name = 'level_to_count', default=2, min=0, max=3, update=updateNode)
    
    def init(self, context):
        self.inputs.new('StringsSocket', "data", "data")
        self.outputs.new('VerticesSocket', 'vertices', 'vertices')
        self.outputs.new('StringsSocket', 'data', 'data')
        self.outputs.new('MatrixSocket', 'matrix', 'matrix')
    
    def draw_buttons(self, context, layout):
        layout.prop(self, "level", text="level")
    
    def flip(self, list, level):
        level -= 1
        if level:
            out = []
            for l in list:
                out.extend(self.flip(l, level))
        else:
            out = []
            length = self.maxlen(list)
            for i in range(length):
                out_ = []
                for l in list:
                    try:
                        out_.append(l[i])
                    except:
                        out_.append(l[0])
                out.append(out_)
        return out
            
    def maxlen(self, list):
        le = []
        for l in list:
            le.append(len(l))
        return max(le)
    
    def update(self):
        if 'vertices' in self.outputs and self.outputs['vertices'].links or \
            'data' in self.outputs and self.outputs['data'].links or \
            'matrix' in self.outputs and  self.outputs['matrix'].links:
            
            if type(self.inputs['data'].links[0].from_socket) == VerticesSocket:
                out_ = self.inputs['data'].links[0].from_socket.VerticesProperty
            if type(self.inputs['data'].links[0].from_socket) == StringsSocket:
                out_ = self.inputs['data'].links[0].from_socket.StringsProperty
            if type(self.inputs['data'].links[0].from_socket) == MatrixSocket:
                out_ = self.inputs['data'].links[0].from_socket.MatrixProperty
            
            outEval = eval(out_)
            outCorr = dataCorrect(outEval) # this is bullshit, as max 3 in levels
            levels = self.level-1
            out = self.flip(outCorr, levels)

            if len(self.outputs['vertices'].links)>0:
                if not self.outputs['vertices'].node.socket_value_update:
                    self.outputs['vertices'].node.update()
                self.outputs['vertices'].links[0].from_socket.VerticesProperty = str(out)
            if len(self.outputs['data'].links)>0:
                if not self.outputs['data'].node.socket_value_update:
                    self.outputs['data'].node.update()
                self.outputs['data'].links[0].from_socket.StringsProperty = str(out)
            if len(self.outputs['matrix'].links)>0:
                if not self.outputs['matrix'].node.socket_value_update:
                    self.outputs['matrix'].node.update()
                self.outputs['matrix'].links[0].from_socket.MatrixProperty = str(out)

def register():
    bpy.utils.register_class(ListFlipNode)
    
def unregister():
    bpy.utils.unregister_class(ListFlipNode)

if __name__ == "__main__":
    register()