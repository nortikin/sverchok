import bmesh, mathutils
from mathutils import Vector, Matrix
from node_s import *
from util import *

#
# Convex Hull
# by Linus Yng

def make_hull(vertices):
    if not vertices:
        return False
    
    bm=bmesh.new() 
    bm_verts = [bm.verts.new(v) for v in vertices]
    bmesh.ops.convex_hull(bm, input=bm_verts, use_existing_faces=False)
             
    edges = []
    faces = []
    bm.verts.index_update()
    bm.faces.index_update()
    verts = [vert.co[:] for vert in bm.verts[:]]
    for face in bm.faces:
        faces.append([v.index for v in face.verts[:]])
    bm.clear()
    bm.free()
    return (verts,faces)


class SvConvexHullNode(Node, SverchCustomTreeNode):
    '''Create convex hull'''
    bl_idname = 'SvConvexHullNode'
    bl_label = 'Convex Hull'
    bl_icon = 'OUTLINER_OB_EMPTY'
    

    def init(self, context):
        self.inputs.new('VerticesSocket', 'Vertices', 'Vertices')
        
        self.outputs.new('VerticesSocket', 'Vertices', 'Vertices')
        self.outputs.new('StringsSocket', 'Polygons', 'Polygons')
                
    def draw_buttons(self, context, layout):
        pass
        
    def update(self):
   
        if 'Vertices' in self.inputs and self.inputs['Vertices'].links:
                
            verts = Vector_generate(SvGetSocketAnyType(self,self.inputs['Vertices']))

            verts_out = []
            polys_out = []
                     
            for v_obj in verts:
                res = make_hull(v_obj)
                if not res:
                    return
                verts_out.append(res[0])
                polys_out.append(res[1])
             
            if 'Vertices' in self.outputs and self.outputs['Vertices'].links:
                SvSetSocketAnyType(self, 'Vertices',verts_out)
            
            if 'Polygons' in self.outputs and self.outputs['Polygons'].links:
                SvSetSocketAnyType(self, 'Polygons', polys_out) 
            
     

    def update_socket(self, context):
        self.update()

def register():
    bpy.utils.register_class(SvConvexHullNode)   
    
def unregister():
    bpy.utils.unregister_class(SvConvexHullNode)

if __name__ == "__main__":
    register()







