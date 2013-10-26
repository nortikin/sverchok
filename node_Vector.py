import bpy
from node_s import *

class GenVectorsNode(Node, SverchCustomTreeNode):
    ''' Generator vectors '''
    bl_idname = 'GenVectorsNode'
    bl_label = 'Gen Vectors'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    def init(self, context):
        self.inputs.new('StringsSocket', "X", "X")
        self.inputs.new('StringsSocket', "Y", "Y")
        self.inputs.new('StringsSocket', "Z", "Z")
        self.outputs.new('VerticesSocket', "Vectors", "Vectors")
        

    def update(self):
        # inputs
        if self.inputs['X'].links and \
            type(self.inputs['X'].links[0].from_socket) == StringsSocket:
            if not self.inputs['X'].node.socket_value_update:
                self.inputs['X'].node.update()
            X = eval(self.inputs['X'].links[0].from_socket.StringsProperty)[0]
        else:
            X = [0.0]
        
        if self.inputs['Y'].links and \
            type(self.inputs['Y'].links[0].from_socket) == StringsSocket:
            if not self.inputs['Y'].node.socket_value_update:
                self.inputs['Y'].node.update()
            Y = eval(self.inputs['Y'].links[0].from_socket.StringsProperty)[0]
        else:
            Y = [0.0]
            
        if self.inputs['Z'].links and \
            type(self.inputs['Z'].links[0].from_socket) == StringsSocket:
            if not self.inputs['Z'].node.socket_value_update:
                self.inputs['Z'].node.update()
            Z = eval(self.inputs['Z'].links[0].from_socket.StringsProperty)[0]
        else:
            Z = [0.0]
        
        # outputs
        if 'Vectors' in self.outputs and len(self.outputs['Vectors'].links)>0:
            if not self.outputs['Vectors'].node.socket_value_update:
                self.outputs['Vectors'].node.update()
            
            max_num = max(len(X), len(Y), len(Z))
            
            self.fullList(X,max_num)
            self.fullList(Y,max_num)
            self.fullList(Z,max_num)
            
            series_vec = list(zip(X,Y,Z))
 
            self.outputs['Vectors'].VerticesProperty = str([series_vec])
            #print (series_vec)
            
    def fullList(self, l, count):
        d = count - len(l)
        if d > 0:
            l.extend([l[-1] for a in range(d)])
        return
                
    def update_socket(self, context):
        self.update()


    

def register():
    bpy.utils.register_class(GenVectorsNode)
    
def unregister():
    bpy.utils.unregister_class(GenVectorsNode)

if __name__ == "__main__":
    register()