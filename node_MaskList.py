import bpy
from node_s import *
from util import *
from copy import copy


class MaskListNode(Node, SverchCustomTreeNode):
    ''' MaskList node '''
    bl_idname = 'MaskListNode'
    bl_label = 'MaskList'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    Level = bpy.props.IntProperty(name='Level', description='Choose list level of data (see help)', default=1, min=1, max=10, update=updateNode)
    
    typ = [False, 'None']
    
    def init(self, context):
        self.inputs.new('StringsSocket', "data", "data")
        self.inputs.new('StringsSocket', "mask", "mask")
        self.outputs.new('StringsSocket', 'dataTrue', 'dataTrue')
        self.outputs.new('StringsSocket', 'dataFalse', 'dataFalse')
    
    def draw_buttons(self, context, layout):
        layout.prop(self, "Level", text="Level lists")
    
    # а не поменялся ли тип входных данных сокета?
    def check_slots(self):
        if type(self.inputs['data'].links[0].from_socket) == VerticesSocket:
            if self.typ[1] != 'v':
                self.typ = [False, 'v']
            else:
                self.typ = [True, 'v']
        if type(self.inputs['data'].links[0].from_socket) == StringsSocket:
            if self.typ[1] != 's':
                self.typ = [False, 's']
            else:
                self.typ = [True, 's']
        if type(self.inputs['data'].links[0].from_socket) == MatrixSocket:
            if self.typ[1] != 'm':
                
                self.typ = [False, 'm']
                print (self.typ[1])
            else:
                self.typ = [True, 'm']
        return
    
    def clean_sockets(self):
        self.typ[0] = False
        if self.outputs['dataFalse']:
            self.outputs.remove(self.outputs['dataFalse'])
        if self.outputs['dataTrue']:
            self.outputs.remove(self.outputs['dataTrue'])
        return
    
    def update(self):
        # changable types sockets in output
        if len(self.inputs['data'].links) > 0:
            self.check_slots()
        #print (self.typ)
        if self.typ[0] == True:
            self.clean_sockets()
            if self.typ[1] == 'v':
                self.outputs.new('VerticesSocket', 'dataFalse', "dataFalse")
                self.outputs.new('VerticesSocket', 'dataTrue', "dataTrue")
            if self.typ[1] == 's':
                self.outputs.new('StringsSocket', 'dataFalse', "dataFalse")
                self.outputs.new('StringsSocket', 'dataTrue', "dataTrue")
            if self.typ[1] == 'm':
                self.outputs.new('MatrixSocket', 'dataFalse', "dataFalse")
                self.outputs.new('MatrixSocket', 'dataTrue', "dataTrue")
        
        # input sockets
        if 'data' not in self.inputs:
            return False
        data = [[]]
        mask=[[1,0]]
        
        if not self.inputs['data'].node.socket_value_update:
            self.inputs['data'].node.update()
        if self.inputs['data'].links and \
                type(self.inputs['data'].links[0].from_socket) == VerticesSocket:
            data = eval(self.inputs['data'].links[0].from_socket.VerticesProperty)
        if self.inputs['data'].links and \
                type(self.inputs['data'].links[0].from_socket) == StringsSocket:
            data = eval(self.inputs['data'].links[0].from_socket.StringsProperty)
        if self.inputs['data'].links and \
                type(self.inputs['data'].links[0].from_socket) == MatrixSocket:
            data = eval(self.inputs['data'].links[0].from_socket.MatrixProperty)
            
        
        if not self.inputs['mask'].node.socket_value_update:
            multi.node.update()
        if self.inputs['mask'].links and \
                type(self.inputs['mask'].links[0].from_socket) == StringsSocket:
            mask = eval(self.inputs['mask'].links[0].from_socket.StringsProperty)
        
        result =  self.getMask(data, mask, self.Level)
        
        # outupy sockets data
        if 'dataTrue' in self.outputs and len(self.outputs['dataTrue'].links)>0:
            if self.typ[1] == 'v':
                self.outputs['dataTrue'].node.VerticesProperty =  str(result[0])
            if self.typ[1] == 's':
                self.outputs['dataTrue'].StringsProperty =  str(result[0])
            if self.typ[1] == 'm':
                self.outputs['dataTrue'].MatrixProperty = str(result[0])
            if not self.outputs['dataTrue'].node.socket_value_update:
                self.outputs['dataTrue'].node.update()
        else:
            self.outputs['dataTrue'].StringsProperty='[[]]'
        
        if 'dataFalse' in self.outputs and len(self.outputs['dataFalse'].links)>0:
            if self.typ[1] == 'v':
                self.outputs['dataFalse'].VerticesProperty =  str(result[1])
            if self.typ[1] == 's':
                self.outputs['dataFalse'].StringsProperty =  str(result[1])
            if self.typ[1] == 'm':
                self.outputs['dataFalse'].MatrixProperty = str(result[1])
            if not self.outputs['dataFalse'].node.socket_value_update:
                self.outputs['dataFalse'].node.update()
        else:
            self.outputs['dataFalse'].StringsProperty='[[]]'      
    
    
    # working horse
    def getMask(self, list_a, mask_l, level):
        list_b = self.getCurrentLevelList(list_a, level)
        res = list_b
        if list_b:
            res = self.putCurrentLevelList(list_a, list_b, mask_l, level)
        return res
    

    def putCurrentLevelList(self, list_a, list_b, mask_l, level):   
        result_t = []
        result_f = []
        if level>1:
            if type(list_a) in [list, tuple]:
                for idx,l in enumerate(list_a):
                    l2 = self.putCurrentLevelList(l, list_b, mask_l, level-1)
                    result_t.append(l2[0])
                    result_f.append(l2[1])
            else:
                print('AHTUNG!!!')
                return list_a
        else:
            mask = mask_l[0]
            mask_0 = copy(mask)
            while len(mask)<len(list_a):
                if len(mask_0)==0:
                    mask_0 = [1,0]
                mask = mask+mask_0
    
            for idx,l in enumerate(list_a):
                tmp = list_b.pop(0)
                if mask[idx]:
                    result_t.append(tmp)
                else:
                    result_f.append(tmp)
                
        return (result_t,result_f)
            
            
    def getCurrentLevelList(self, list_a, level):
        list_b=[]
        if level>1:
            if type(list_a) in [list, tuple]:
                for l in list_a:
                    l2 = self.getCurrentLevelList(l, level-1)
                    if type(l2) in [list, tuple]:
                        list_b.extend(l2)
                    else:
                        return False
            else:
                return False
        else:
            if type(list_a) in [list, tuple]:
                return copy(list_a)
            else:
                return list_a
        return list_b


def register():
    bpy.utils.register_class(MaskListNode)
    
def unregister():
    bpy.utils.unregister_class(MaskListNode)

if __name__ == "__main__":
    register()