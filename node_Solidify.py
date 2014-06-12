import bmesh, mathutils
from mathutils import Vector, Matrix
from node_s import *
from util import *

from sv_bmesh_utils import bmesh_from_pydata
# by Linus Yng

def soldify(vertices, faces, t):

    if not faces or not vertices:
        return False
   
    if len(faces[0])==2:
        return False
    bm = bmesh_from_pydata(vertices,[],faces)            
             
    geom_in = bm.verts[:]+bm.edges[:]+bm.faces[:]
    
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    res=bmesh.ops.solidify(bm, geom=geom_in, thickness=t)

    edges = []
    faces = []
    bm.verts.index_update()
    bm.edges.index_update()
    bm.faces.index_update()
    for edge in bm.edges[:]:
        edges.append([v.index for v in edge.verts[:]])
    verts = [vert.co[:] for vert in bm.verts[:]]
    for face in bm.faces:
        faces.append([v.index for v in face.verts[:]])
    bm.clear()
    bm.free()
    return (verts,edges,faces)


class SvSolidifyNode(Node, SverchCustomTreeNode):
    '''Soldifies geometry'''
    bl_idname = 'SvSolidifyNode'
    bl_label = 'Solidify'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    thickness = bpy.props.FloatProperty(name='Thickness', description='Shell thickness', default=0.1, update=updateNode)

    def init(self, context):
        
        self.inputs.new('StringsSocket', 'thickness').prop_name = 'thickness'
        self.inputs.new('VerticesSocket', 'vertices', 'vertices')
        self.inputs.new('StringsSocket', 'polygons', 'polygons')
        
        self.outputs.new('VerticesSocket', 'vertices', 'vertices')
        self.outputs.new('StringsSocket', 'edges', 'edges')
        self.outputs.new('StringsSocket', 'polygons', 'polygons')
                
    def update(self):
        if not self.outputs['vertices'].is_linked:
            return
            
        if 'vertices' in self.inputs and self.inputs['vertices'].links and \
            'polygons' in self.inputs and self.inputs['polygons'].links:
                
       
            verts = Vector_generate(SvGetSocketAnyType(self,self.inputs['vertices']))
            polys = SvGetSocketAnyType(self,self.inputs['polygons'])
            if 'thickness' in self.inputs:
                thickness = self.inputs['thickness'].sv_get()[0]
            else:
                thickness = [self.thickness]
                
            #print (verts,polys)

            verts_out = []
            edges_out = []
            polys_out = []
                     
            for v,p,t in zip(verts,polys,repeat_last(thickness)):
                res = soldify(v,p,t)
                if not res:
                    return
                verts_out.append(res[0])
                edges_out.append(res[1])
                polys_out.append(res[2])
             
            if 'vertices' in self.outputs and self.outputs['vertices'].links:
                SvSetSocketAnyType(self, 'vertices',verts_out)
            
            if 'edges' in self.outputs and self.outputs['edges'].links:
                SvSetSocketAnyType(self, 'edges',edges_out) 
                
            if 'polygons' in self.outputs and self.outputs['polygons'].links:
                SvSetSocketAnyType(self, 'polygons', polys_out) 
            
     
    def update_socket(self, context):
        self.update()

def register():
    bpy.utils.register_class(SvSolidifyNode)   
    
def unregister():
    bpy.utils.unregister_class(SvSolidifyNode)

if __name__ == "__main__":
    register()
