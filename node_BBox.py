from node_s import *
from util import *
from itertools import product

class SvBBoxNode(Node, SverchCustomTreeNode):
    '''Bounding box'''
    bl_idname = 'SvBBoxNode'
    bl_label = 'Bounding box'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    def init(self, context):
        self.inputs.new('VerticesSocket', 'Vertices')
        
        self.outputs.new('VerticesSocket', 'Vertices')
        self.outputs.new('StringsSocket', 'Edges', 'Edges')

    def update(self):
        if not 'Edges' in self.outputs:
            return        
        if not self.inputs['Vertices'].links:
            return        
        if not any([self.outputs['Vertices'].links, self.outputs['Edges'].links]):
            return 

        vert = SvGetSocketAnyType(self,self.inputs['Vertices'])
        vert = dataCorrect(vert, nominal_dept=2)

        if vert:
            verts_out = []
            edges_out = []
            edges =[
                (0,1),(1,3),(3,2),(2,0), # bottom edges
                (4,5),(5,7),(7,6),(6,4), # top edges
                (0,4),(1,5),(2,6),(3,7)  # sides
            ]
            
            for v in vert:
                maxmin=list(zip(map(max,*v),map(min,*v)))
                out=list(product(*reversed(maxmin)))
                verts_out.append([l[::-1] for l in out[::-1]])
                edges_out.append(edges)
            
            if self.outputs['Vertices'].links:
                SvSetSocketAnyType(self, 'Vertices',verts_out)
            
            if self.outputs['Edges'].links:
                SvSetSocketAnyType(self, 'Edges', edges_out)
              
    def update_socket(self, context):
        self.update()

def register():
    bpy.utils.register_class(SvBBoxNode)   
    
def unregister():
    bpy.utils.unregister_class(SvBBoxNode)

if __name__ == "__main__":
    register()
