from node_s import *
from util import *
import operator
import bmesh
from mathutils import Matrix,Vector

class SvAdaptiveEdgeNode(Node, SverchCustomTreeNode):
    '''Map edge object to recipent edges'''
    bl_idname = 'SvAdaptiveEdgeNode'
    bl_label = 'Adaptive Edges'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
   
    def init(self, context):
        self.inputs.new('VerticesSocket', 'VersR', 'VersR')
        self.inputs.new('StringsSocket', 'EdgeR', 'EdgeR')
        self.inputs.new('VerticesSocket', 'VersD', 'VersD')
        self.inputs.new('StringsSocket', 'EdgeD', 'EdgeD')
        
        self.outputs.new('VerticesSocket', 'Vertices', 'Vertices')
        self.outputs.new('StringsSocket', 'Edges', 'Edges')
                

    def update(self):
        
        in_sockets = ['VersR','EdgeR','VersD','EdgeD']
        for name in in_sockets:
            if not name in self.inputs:
                return
        for name in in_sockets:
            if not self.inputs[name].links:
                return
            
        versR = Vector_generate(SvGetSocketAnyType(self,self.inputs['VersR']))        
        versD = Vector_generate(SvGetSocketAnyType(self,self.inputs['VersD']))        
        edgeR = SvGetSocketAnyType(self,self.inputs['EdgeR'])        
        edgeD = SvGetSocketAnyType(self,self.inputs['EdgeD'])
        verts_out = []
        edges_out = []
        
        # only first obj
        verD = [v-versD[0][0] for v in versD[0]]
        edgD = edgeD[0]
        d_vector = verD[-1].copy()
        d_scale = d_vector.length
        d_vector.normalize()

        for vc,edg in zip(versR,edgeR):
            v_out = []
            e_out = []
            for e in edg:

                e_vector = vc[e[1]]-vc[e[0]]
                e_scale = e_vector.length
                e_vector.normalize()
                q1 = d_vector.rotation_difference(e_vector)
                mat_s = Matrix.Scale(e_scale/d_scale,4)
                mat_r = Matrix.Rotation(q1.angle,4,q1.axis)
                mat_l = Matrix.Translation(vc[e[0]])
                mat = mat_l * mat_r * mat_s
                e_out.extend([list(map(lambda x:operator.add(len(v_out),x),e)) for e in edgD])  
                v_out.extend([mat*v for v in verD])
                   
            verts_out.append(v_out)
            edges_out.append(e_out)
                    
        if 'Vertices' in self.outputs and self.outputs['Vertices'].links:
            SvSetSocketAnyType(self, 'Vertices',Vector_degenerate(verts_out))
        
        if 'Edges' in self.outputs and self.outputs['Edges'].links:
            SvSetSocketAnyType(self, 'Edges',edges_out) 
 

    def update_socket(self, context):
        self.update()

def register():
    bpy.utils.register_class(SvAdaptiveEdgeNode)   
    
def unregister():
    bpy.utils.unregister_class(SvAdaptiveEdgeNode)

if __name__ == "__main__":
    register()








