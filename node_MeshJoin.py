from node_s import *
from util import *
import operator


class SvMeshJoinNode(Node, SverchCustomTreeNode):
    '''MeshJoin, join many mesh into on mesh object'''
    bl_idname = 'SvMeshJoinNode'
    bl_label = 'Mesh Join'
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
            offset = 0         
            for obj in zip(verts,poly_edge): 
                verts_out.extend(obj[0])
                if offset:
                    res=[list(map(lambda x:operator.add(offset,x),ep)) for ep in obj[1]]
                    poly_edge_out.extend(res)   
                else:
                    poly_edge_out.extend(obj[1])
                offset += len(obj[0])

            if 'Vertices' in self.outputs and self.outputs['Vertices'].links:
                SvSetSocketAnyType(self, 'Vertices',[verts_out])
            
            if 'PolyEdge' in self.outputs and self.outputs['PolyEdge'].links:
                SvSetSocketAnyType(self, 'PolyEdge',[poly_edge_out]) 
     

    def update_socket(self, context):
        self.update()

def register():
    bpy.utils.register_class(SvMeshJoinNode)   
    
def unregister():
    bpy.utils.unregister_class(SvMeshJoinNode)

if __name__ == "__main__":
    register()







