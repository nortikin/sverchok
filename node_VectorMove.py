import bpy
from node_s import *
from util import *
from mathutils import Vector, Matrix

class VectorMoveNode(Node, SverchCustomTreeNode):
    ''' Vector Move vectors '''
    bl_idname = 'VectorMoveNode'
    bl_label = 'Vectors Move'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    def init(self, context):
        self.inputs.new('VerticesSocket', "vertices", "vertices")
        self.inputs.new('VerticesSocket', "vectors", "vectors")
        self.inputs.new('StringsSocket', "multiplier", "multiplier")
        self.outputs.new('VerticesSocket', "vertices", "vertices")
        

    def update(self):
        # inputs
        if 'vertices' in self.inputs and self.inputs['vertices'].links and \
            type(self.inputs['vertices'].links[0].from_socket) == VerticesSocket:
            if not self.inputs['vertices'].node.socket_value_update:
                self.inputs['vertices'].node.update()
            vers_ = eval(self.inputs['vertices'].links[0].from_socket.VerticesProperty)
            vers = Vector_generate(vers_)
        else:
            vers = []
        
        if 'vectors' in self.inputs and self.inputs['vectors'].links and \
            type(self.inputs['vectors'].links[0].from_socket) == VerticesSocket:
            if not self.inputs['vectors'].node.socket_value_update:
                self.inputs['vectors'].node.update()
            vecs_ = eval(self.inputs['vectors'].links[0].from_socket.VerticesProperty)
            vecs = Vector_generate(vecs_)
        else:
            vecs = []
            
        if 'multiplier' in self.inputs and self.inputs['multiplier'].links and \
            type(self.inputs['multiplier'].links[0].from_socket) == StringsSocket:
            if not self.inputs['multiplier'].node.socket_value_update:
                self.inputs['multiplier'].node.update()
            mult = eval(self.inputs['multiplier'].links[0].from_socket.StringsProperty)
        else:
            mult = [[1.0]]
        
        # outputs
        if 'vertices' in self.outputs and len(self.outputs['vertices'].links)>0:
           if not self.inputs['vertices'].node.socket_value_update:
               self.inputs['vertices'].node.update()
           
           mov = self.moved(vers, vecs, mult)
           self.outputs['vertices'].VerticesProperty = str(mov, )
    
    def moved(self, vers, vecs, mult):
        r = len(vers) - len(vecs)
        rm = len(vers) - len(mult)
        moved = []
        if r > 0:
            vecs.extend([vecs[-1] for a in range(r)])
        if rm > 0:
            mult.extend([mult[-1] for a in range(rm)])
        for i, ob in enumerate(vers):       # object
            d = len(ob) - len(vecs[i])
            dm = len(ob) - len(mult[i])
            if d > 0:
                vecs[i].extend([vecs[i][-1] for a in range(d)])
            if dm > 0:
                mult[i].extend([mult[i][-1] for a in range(dm)])
            temp = []
            for k, vr in enumerate(ob):     # vectors
                #print('move',str(len(ob)), str(len(vecs[i])), str(vr), str(vecs[i][k]))
                v = ((vr + vecs[i][k]*mult[i][k]))[:]
                temp.append(v)   #[0]*mult[0], v[1]*mult[0], v[2]*mult[0]))
            moved.append(temp)
        #print ('move', str(moved))
        return moved
                
    def update_socket(self, context):
        self.update()


    

def register():
    bpy.utils.register_class(VectorMoveNode)
    
def unregister():
    bpy.utils.unregister_class(VectorMoveNode)

if __name__ == "__main__":
    register()