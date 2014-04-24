from node_s import *
from util import *
import operator

from itertools import chain

class SvDeleteLooseNode(Node, SverchCustomTreeNode):
    '''Delete vertices not used in face or edge'''
    bl_idname = 'SvDeleteLooseNode'
    bl_label = 'Delete Loose'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
   
    def init(self, context):
        self.inputs.new('VerticesSocket', 'Vertices', 'Vertices')
        self.inputs.new('StringsSocket', 'PolyEdge', 'PolyEdge')
        
        self.outputs.new('VerticesSocket', 'Vertices', 'Vertices')
        self.outputs.new('StringsSocket', 'PolyEdge', 'PolyEdge')
                

    def update(self):
               
        if 'Vertices' in self.inputs and self.inputs['Vertices'].links and \
            'PolyEdge' in self.inputs and self.inputs['PolyEdge'].links:
                    
            verts = SvGetSocketAnyType(self,self.inputs['Vertices'])
            poly_edge = SvGetSocketAnyType(self,self.inputs['PolyEdge'])
            verts_out = []
            poly_edge_out = []
            for ve,pe in zip(verts,poly_edge): 
                indx = set(chain.from_iterable(pe))
                verts_out.append([v for i,v in enumerate(ve) if i in indx])
                v_index = dict([(j,i) for i,j in enumerate(sorted(indx))])
                poly_edge_out.append([list(map(lambda n:v_index[n],p)) for p in pe])
                
            if 'Vertices' in self.outputs and self.outputs['Vertices'].links:
                SvSetSocketAnyType(self, 'Vertices',verts_out)
            
            if 'PolyEdge' in self.outputs and self.outputs['PolyEdge'].links:
                SvSetSocketAnyType(self, 'PolyEdge',poly_edge_out) 
     

    def update_socket(self, context):
        self.update()

def register():
    bpy.utils.register_class(SvDeleteLooseNode)   
    
def unregister():
    bpy.utils.unregister_class(SvDeleteLooseNode)

if __name__ == "__main__":
    register()







