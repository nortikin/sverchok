import bpy
from node_s import *
from functools import reduce
from util import *



class ZipNode(Node, SverchCustomTreeNode):
    ''' Zip node '''
    bl_idname = 'ZipNode'
    bl_label = 'List Zip'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    level = bpy.props.IntProperty(name = 'level', default=1, min=1)
    typ = bpy.props.StringProperty(name='typ', default='')
    newsock = bpy.props.BoolProperty(name='newsock', default=False)
    
    base_name = 'data '
    multi_socket_type = 'StringsSocket'
    
    def draw_buttons(self, context, layout):
        layout.prop(self, "level", text="Level")
    
    def init(self, context):
        self.inputs.new('StringsSocket', "data", "data")
        self.outputs.new('StringsSocket', 'data', 'data')


    def update(self):
        # inputs
        multi_socket(self , min=1)
        
        if 'data' in self.inputs and self.inputs['data'].links:
            # адаптивный сокет
            inputsocketname = 'data'
            outputsocketname = ['data']
            changable_sockets(self, inputsocketname, outputsocketname)
        
        if 'data' in self.outputs and self.outputs['data'].links:
            slots = []
            for socket in self.inputs:
                if socket.links:
                    slots.append(SvGetSocketAnyType(self,socket))
            if len(slots) < 2:
                return    
            output = self.myZip(slots,self.level)  
            SvSetSocketAnyType(self, 'data', output)
    
    def myZip(self, list_all, level, level2=0):
        if level==level2:
            if type(list_all) in [list, tuple]:
                list_lens = []
                list_res = []
                for l in list_all:
                    if type(l) in [list, tuple]:
                        list_lens.append(len(l))
                    else:
                        list_lens.append(0)
                
                min_len=min(list_lens)
                for value in range(min_len):
                    lt=[]
                    for l in list_all:
                        lt.append(l[value])
                    t = list(lt)
                    list_res.append(t)
                return list_res
            else:
                return False
        elif level>level2:
            if type(list_all) in [list, tuple]:
                list_res = []
                list_tr = self.myZip(list_all, level, level2+1)
                if list_tr==False:
                    list_tr = list_all
                t = []
                for tr in list_tr:
                    if type(list_tr) in [list, tuple]:
                        list_tl = self.myZip(tr, level, level2+1)
                        if list_tl==False:
                            list_tl=list_tr
                        t.append(list_tl)
                list_res.extend(list(t))
                return list_res
            else:
                return False    
    
    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(ZipNode)
    
def unregister():
    bpy.utils.unregister_class(ZipNode)

if __name__ == "__main__":
    register()