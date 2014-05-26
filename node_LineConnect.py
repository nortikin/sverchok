import bpy
from node_s import *
from util import *

class LineConnectNode(Node, SverchCustomTreeNode):
    ''' LineConnect node '''
    bl_idname = 'LineConnectNode'
    bl_label = 'Line Connect'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    JoinLevel = bpy.props.IntProperty(name='JoinLevel', description='Choose connect level of data (see help)', default=1, min=1, max=2, update=updateNode)
    polygons = bpy.props.BoolProperty(name='polygons', description='Do polygons or not?', default=True, update=updateNode)
    dir_check = bpy.props.BoolProperty(name='direction', description='direction to connect', default=True, update=updateNode)
    quad_check = bpy.props.BoolProperty(name='quad', description='quad', default=False, update=updateNode)
    cicl_check = bpy.props.BoolProperty(name='cicle', description='cicle line', default=False, update=updateNode)
    
    base_name = 'vertices '
    multi_socket_type = 'VerticesSocket'
    
    def init(self, context):
        self.inputs.new('VerticesSocket', 'vertices', 'vertices')
        self.outputs.new('VerticesSocket', 'vertices', 'vertices')
        self.outputs.new('StringsSocket', 'data', 'data')
    
    def draw_buttons(self, context, layout):
        layout.prop(self, "dir_check", text="direction")
        layout.prop(self, "quad_check", text="quad pols")
        layout.prop(self, "cicl_check", text="cicle first-last")
        layout.prop(self, "polygons", text="do polygons")
        layout.prop(self, "JoinLevel", text="connect level")

    
    def connect(self, vers, dirn, quad, cicl, clev, polygons):
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
            if not polygons:
                for k, ob in enumerate(vers_):
                    objecto = []
                    for i, ve in enumerate(ob[0:-1]):
                        objecto.append([i,i+1])
                    edges.append(objecto)
            else:
                length_ob = []
                newobject = []
                for k, ob in enumerate(vers_):
                    length_ob.append(len(ob))
                    newobject.extend(ob)
                curr = 0
                objecto = []
                indexes__ = []
                for i, ob in enumerate(length_ob):
                    indexes_ = []
                    for w in range(ob):
                        indexes_.append(curr)
                        curr += 1
                    if i==0 and cicl:
                        cicle_firstrow = indexes_
                    if i > 0:
                        indexes = indexes_ + indexes__[::-1]
                        if quad and len(indexes)>=4:
                            quaded = [(indexes[k], indexes[k+1], indexes[-(k+2)], indexes[-(k+1)]) for k in range((len(indexes)-1)//2)]
                            objecto.extend(quaded)
                        else:
                            objecto.append(indexes)
                        if i==len(length_ob)-1 and cicl:
                            indexes = cicle_firstrow + indexes_[::-1]
                            if quad and len(indexes)>=4:
                                quaded = [(indexes[k], indexes[k+1], indexes[-(k+2)], indexes[-(k+1)]) for k in range((len(indexes)-1)//2)]
                                objecto.extend(quaded)
                            else:
                                objecto.append(indexes)
                    indexes__ = indexes_
                vers_ = [newobject]
                edges = [objecto]
                    
        else:
            ml = max(lens)
            joinvers = []
            for ob in vers_:
                fullList(ob, ml)
                joinvers.extend(ob)
            objecto = []
            if polygons:
                for i, ve in enumerate(vers_[0][:]):
                    inds = [j*ml+i for j in range(lenvers)]
                    objecto.append(inds)
            else:
                for i, ve in enumerate(vers_[0][:]):
                    inds = [j*ml+i for j in range(lenvers)]
                    for i, item in enumerate(inds):
                        if i==0 and cicl:
                            objecto.append([inds[0],inds[-1]])
                        elif i==0:
                            continue
                        else:
                            objecto.append([item,inds[i-1]])
            edges.append(objecto)
            vers_ = [joinvers]
        return vers_, edges
    
    def update(self):
        # inputs
        multi_socket(self , min=1)

        if 'vertices' in self.outputs and self.outputs['vertices'].links or \
                'data' in self.outputs and self.outputs['data'].links:
            slots = []
            for socket in self.inputs:
                if socket.links and type(socket.links[0].from_socket) == VerticesSocket:
                    slots.append(SvGetSocketAnyType(self,socket))
            if len(slots) == 0:
                return
            if levelsOflist(slots) <=4:
                lev = 1
            else:
                lev = self.JoinLevel
            result = self.connect(slots, self.dir_check, self.quad_check, self.cicl_check, lev, self.polygons)
            
            if self.outputs['vertices'].links:
                 SvSetSocketAnyType(self,'vertices',result[0])
            if self.outputs['data'].links:
                SvSetSocketAnyType(self,'data',result[1])

def register():
    bpy.utils.register_class(LineConnectNode)
    
def unregister():
    bpy.utils.unregister_class(LineConnectNode)

if __name__ == "__main__":
    register()