import bpy
from node_s import *
from util import *

class Pols2EdgsNode(Node, SverchCustomTreeNode):
    ''' take polygon and to edges '''
    bl_idname = 'Pols2EdgsNode'
    bl_label = 'Polygons 2 Edges'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    def init(self, context):
        self.inputs.new('StringsSocket', "pols", "pols")
        self.outputs.new('StringsSocket', "edgs", "edgs")
        
    def update(self):
        if 'edgs' in self.outputs and len(self.outputs['edgs'].links)>0:
            if 'pols' in self.inputs and len(self.inputs['pols'].links)>0:
                X_ = SvGetSocketAnyType(self, self.inputs['pols'])
                X = dataCorrect(X_)
                #print('p2e-X',str(X))
                result = self.pols_edges(X)
                SvSetSocketAnyType(self, 'edgs', result)

    def pols_edges(self,obj):
        out = []
        for faces in obj:
            out_edges = set()
            for face in faces:
                for edge in zip(face,face[1:]+[face[0]]):
                    out_edges.add(tuple(sorted(edge)))
            out.append(list(out_edges))
        return out
    def polstoedgs(self, pols):
        out = []
        for obj in pols:
            object = []
            for pols in obj:
                edgs = []
                for i, ind in enumerate(pols):
                    #print('p2e',str(i%2), str(ind))
                    this = [ind, pols[i-1]]
                    this.sort()
                    if this not in edgs and this not in object: 
                        edgs.append(this)
                object.extend(edgs)
            out.append(object)
        #print('p2e',str(out))
        return out

def register():
    bpy.utils.register_class(Pols2EdgsNode)
    
def unregister():
    bpy.utils.unregister_class(Pols2EdgsNode)


if __name__ == "__main__":
    register()
