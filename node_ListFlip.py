import bpy
from node_s import *
from util import *


class ListFlipNode(Node, SverchCustomTreeNode):
    ''' ListFlipNode '''
    bl_idname = 'ListFlipNode'
    bl_label = 'List Flip Node'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    level = bpy.props.IntProperty(name = 'level_to_count', default=2, min=0, max=3, update=updateNode)
    typ = bpy.props.StringProperty(name='typ', default='')
    newsock = bpy.props.BoolProperty(name='newsock', default=False)
    
    def init(self, context):
        self.inputs.new('StringsSocket', "data", "data")
        self.outputs.new('StringsSocket', 'data', 'data')
    
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
        if 'data' in self.outputs and self.outputs['data'].links:
            # адаптивный сокет
            inputsocketname = 'data'
            outputsocketname = ['data']
            changable_sockets(self, inputsocketname, outputsocketname)
            
        if 'data' in self.inputs and self.inputs['data'].links:
            outEval = SvGetSocketAnyType(self, self.inputs['data'])
            outCorr = dataCorrect(outEval) # this is bullshit, as max 3 in levels
            levels = self.level-1
            out = self.flip(outCorr, levels)
            SvSetSocketAnyType(self, 'data', out)

def register():
    bpy.utils.register_class(ListFlipNode)
    
def unregister():
    bpy.utils.unregister_class(ListFlipNode)

if __name__ == "__main__":
    register()