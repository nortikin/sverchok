import bpy
from node_s import *
from util import *


class LineConnectNode(Node, SverchCustomTreeNode):
    ''' LineConnect node '''
    bl_idname = 'LineConnectNode'
    bl_label = 'Line Connect'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    JoinLevel = bpy.props.IntProperty(name='JoinLevel', description='Choose connect level of data (see help)', default=1, min=1, max=2, update=updateNode)
    dir_check = bpy.props.BoolProperty(name='direction', description='direction to connect', default=True, update=updateNode)
    link_check = bpy.props.BoolProperty(name='link', description='link parts', default=False, update=updateNode)
    cicl_check = bpy.props.BoolProperty(name='cicle', description='cicle line', default=False, update=updateNode)
    
    def init(self, context):
        self.inputs.new('VerticesSocket', "vertices", "vertices")
        self.outputs.new('VerticesSocket', 'vertices', 'vertices')
        self.outputs.new('StringsSocket', 'data', 'data')
    
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
        layout.prop(self, "dir_check", text="direction")
        layout.prop(self, "link_check", text="to link")
        layout.prop(self, "cicl_check", text="cicle first-last")
        layout.prop(self, "JoinLevel", text="connect level")
    
    def fullList(self, l, count):
        d = count - len(l)
        if d > 0:
            l.extend([l[-1] for a in range(d)])
        return
    
    def connect(self, vers, dirn, link, cicl, clev):
        vers_ = []
        lens = []
        
        if clev == 1:
            for ob in vers:
                vers_.extend(ob)
                for o in ob:
                    lens.append(len(o))
        elif clev == 2:
            for ob in vers:
                for o in ob:
                    vers_.extend(o)
                    lens.append(len(o))
        lenvers = len(vers_)
        edges = []
        if dirn:
            for k, ob in enumerate(vers_):
                objecto = []
                for i, ve in enumerate(ob[0:-1]):
                    objecto.append([i,i+1])
                if link:
                    pass
                if cicl:
                    objecto.append([0,k-1])
                edges.append(objecto)
        else:
            ml = max(lens)
            print(lens)
            joinvers = []
            for ob in vers_:
                #print('ob',ob)
                self.fullList(ob, ml)
                joinvers.extend(ob)
            objecto = []
            for i, ve in enumerate(vers_[0][0:-1]):
                inds = [j*ml+i for j in range(lenvers)]
                objecto.append(inds)
            edges.append(objecto)
            vers_ = [joinvers]
        return vers_, edges
    
    def update(self):
        # inputs
        ch = self.check_slots(0)
        if ch and len(self.inputs)>1:
            for c in ch:
                self.inputs.remove(self.inputs[ch[0]])
        slots = []
        for idx, multi in enumerate(self.inputs[:]):   
             
            if multi.links:
                if not multi.node.socket_value_update:
                    multi.node.update()
                if type(multi.links[0].from_socket) == VerticesSocket:
                    slots.append(eval(multi.links[0].from_socket.VerticesProperty))
                    # print ('slots',levelsOflist(slots))
                    ch = self.check_slots(2)
        if not ch:
            self.inputs.new('VerticesSocket', "vertices", "vertices")
        
        
        if 'vertices' in self.outputs and self.outputs['vertices'].links or \
                'data' in self.outputs and self.outputs['data'].links:
            
            if levelsOflist(slots) <=4:
                lev = 1
            else:
                lev = self.JoinLevel
            result = self.connect(slots, self.dir_check, self.link_check, self.cicl_check, lev)
            print (levelsOflist(slots), '===>', levelsOflist(result))
            if len(self.outputs['vertices'].links)>0:
                if not self.outputs['vertices'].node.socket_value_update:
                    self.outputs['vertices'].node.update()
                self.outputs['vertices'].links[0].from_socket.VerticesProperty =  str(result[0])
            if len(self.outputs['data'].links)>0:
                if not self.outputs['data'].node.socket_value_update:
                    self.outputs['data'].node.update()
                self.outputs['data'].links[0].from_socket.StringsProperty = str(result[1])

def register():
    bpy.utils.register_class(LineConnectNode)
    
def unregister():
    bpy.utils.unregister_class(LineConnectNode)

if __name__ == "__main__":
    register()