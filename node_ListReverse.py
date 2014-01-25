import bpy
from node_s import *
from util import *

class ListReverseNode(Node, SverchCustomTreeNode):
    ''' List Reverse Node '''
    bl_idname = 'ListReverseNode'
    bl_label = 'List Reverse'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    level = bpy.props.IntProperty(name = 'level_to_Reverse', default=2, min=1, update=updateNode)
    typ = bpy.props.StringProperty(name='typ', default='')
    newsock = bpy.props.BoolProperty(name='newsock', default=False)
    
    def draw_buttons(self, context, layout):
        layout.prop(self, "level", text="level")
    
    def init(self, context):
        self.inputs.new('StringsSocket', "data", "data")
        self.outputs.new('StringsSocket', 'data', 'data')

    def update(self):
        if 'data' in self.inputs and len(self.inputs['data'].links)>0:
            # адаптивный сокет
            inputsocketname = 'data'
            outputsocketname = ['data']
            changable_sockets(self, inputsocketname, outputsocketname)
        
            data = SvGetSocketAnyType(self, self.inputs['data'])
            output = self.revers(data, self.level)
            SvSetSocketAnyType(self, 'data', output)

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