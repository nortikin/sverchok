from node_s import *
from util import *
import itertools
from itertools import cycle, islice
from bpy.props import IntProperty

class SvMaskJoinNode(Node, SverchCustomTreeNode):
    '''Mask Join'''
    bl_idname = 'SvMaskJoinNode'
    bl_label = 'Mask Join'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    level = IntProperty(min=1, name="Level", default=1)
    
    typ = bpy.props.StringProperty(name='typ', default='')
    newsock = bpy.props.BoolProperty(name='newsock', default=False)

    def init(self, context):
        self.inputs.new('StringsSocket', 'Mask')
        self.inputs.new('StringsSocket', 'Data True')
        self.inputs.new('StringsSocket', 'Data False')
        
        self.outputs.new('StringsSocket', 'Data')
    
    def draw_buttons(self, context, layout):
        layout.prop(self,'level')
    
    def update(self):
        if not 'Data' in self.outputs:
            return
        if not self.outputs['Data'].links:
            return       
        inputsocketname = 'Data True'
        outputsocketname = ['Data']
        changable_sockets(self, inputsocketname, outputsocketname)

        if all((s.links for s in self.inputs)):
            mask = SvGetSocketAnyType(self,self.inputs['Mask'])
            data_t = SvGetSocketAnyType(self,self.inputs['Data True'])
            data_f = SvGetSocketAnyType(self,self.inputs['Data False'])
            
            data_out = self.get_level(mask,data_t,data_f,self.level-1)
            
            SvSetSocketAnyType(self, 'Data',data_out)
            
    def apply_mask(self,mask,data_t,data_f):
        ind_t,ind_f=0,0
        out = []
        for m in mask:
            if m:
                if ind_t == len(data_t):
                    return out 
                out.append(data_t[ind_t])
                ind_t += 1
            else:
                if ind_f == len(data_f):
                    return out 
                out.append(data_f[ind_f])
                ind_f += 1
        return out
    
    def get_level(self,mask,data_t,data_f,level):
        if level==1:
            out = []
            param=(mask,data_t,data_f)
            if not all((isinstance(p,(list,tuple)) for p in param)):
                print("Fail")
                return
            max_index = min(map(len,param))
            for i in range(max_index):
                out.append(self.apply_mask(mask[i],data_t[i],data_f[i]))
            return out
        elif level > 2: 
            out = []
            for t,f in zip(data_t,data_f):
                out.append(self.get_level(mask,t,f, level - 1))
            return out
        else:
            return self.apply_mask(mask[0],data_t,data_f)
            
    def update_socket(self, context):
        self.update()

def register():
    bpy.utils.register_class(SvMaskJoinNode)   
    
def unregister():
    bpy.utils.unregister_class(SvMaskJoinNode)

if __name__ == "__main__":
    register()
