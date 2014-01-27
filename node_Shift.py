import bpy
from node_s import *
from util import *



class ShiftNode(Node, SverchCustomTreeNode):
    ''' Shift node '''
    bl_idname = 'ShiftNode'
    bl_label = 'List Shift'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    enclose = bpy.props.BoolProperty(name='check_tail', default=True, update=updateNode)
    level = bpy.props.IntProperty(name = 'level', default=0, min=0, update=updateNode)
    typ = bpy.props.StringProperty(name='typ', default='')
    newsock = bpy.props.BoolProperty(name='newsock', default=False)
    
    def draw_buttons(self, context, layout):
        layout.prop(self, "level", text="level")
        layout.prop(self, "enclose", text="enclose")
    
    def init(self, context):
        self.inputs.new('StringsSocket', "data", "data")
        self.inputs.new('StringsSocket', "shift", "shift")
        self.outputs.new('StringsSocket', 'data', 'data')

    def update(self):
        if 'data' in self.inputs and len(self.inputs['data'].links)>0:
            # адаптивный сокет
            inputsocketname = 'data'
            outputsocketname = ['data']
            changable_sockets(self, inputsocketname, outputsocketname)
        
        if 'data' in self.outputs and len(self.outputs['data'].links)>0:
            if 'shift' in self.inputs and self.inputs['shift'].links and \
                type(self.inputs['shift'].links[0].from_socket) == StringsSocket:
                if not self.inputs['shift'].node.socket_value_update:
                    self.inputs['shift'].node.update()
                number = eval(self.inputs['shift'].links[0].from_socket.StringsProperty)
                # не знаю насколько целесообразно
                #if type(number)!=list or type(number[0])!=list or type(number[0][0])!=int:
                    #number = [[0]]
            else:          
                number = [[0]]
            
            data = SvGetSocketAnyType(self, self.inputs['data'])
            output = self.shift(data, number, self.enclose, self.level)
            
            SvSetSocketAnyType(self, 'data', output)


    def shift(self, list_a, shift, check_enclose, level, cou=0):
        if level:
            list_all = []
            for idx, obj in enumerate(list_a):
                list_all.append(self.shift(obj, shift, check_enclose, level-1, idx))
                
        else:
            list_all = []
            if type(list_a)==list:
                indx = min(cou, len(shift)-1)
                for i,l in enumerate(list_a):
                    if type(l) == tuple:
                        l = list(l[:])
                    k=min(len(shift[indx])-1, i)
                    n = shift[indx][k]
                    n_=min(abs(n), len(l))
                    if n<0:
                        list_out = l[:-n_]
                        if check_enclose:
                            list_out = l[-n_:]+list_out
                    else:
                        list_out = l[n_:]
                        if check_enclose:
                            list_out.extend(l[:n_])
                    #print('\nn list_out', n,list_out)        
                    list_all.append(list_out)
            if list_all==[]:
                list_all=[[]]
        return list_all


def register():
    bpy.utils.register_class(ShiftNode)
    
def unregister():
    bpy.utils.unregister_class(ShiftNode)

if __name__ == "__main__":
    register()