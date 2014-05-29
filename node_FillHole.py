import bmesh, mathutils
from mathutils import Vector, Matrix
from node_s import *
from util import *



def fill_holes(vertices, edges, s):

    if not edges and not vertices:
        return False

    if len(edges[0])!=2:
        return False

    bm=bmesh.new()
    bm_verts =[bm.verts.new(v) for v in vertices]
    for e in edges:
        bm.edges.new([bm_verts[e[0]],bm_verts[e[1]]])

    res=bmesh.ops.holes_fill(bm, edges=bm.edges[:], sides=s)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
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


class SvFillHolesNode(Node, SverchCustomTreeNode):
    '''Fills holes'''
    bl_idname = 'SvFillsHoleNode'
    bl_label = 'Fill Holes'
    bl_icon = 'OUTLINER_OB_EMPTY'

    sides = bpy.props.IntProperty(name='Sides', description='Side to fill',
                                default=4, min=3, update=updateNode)

    def init(self, context):
        self.inputs.new('VerticesSocket', 'vertices')
        self.inputs.new('StringsSocket', 'edges')
        self.inputs.new('StringsSocket', 'Sides').prop_name='sides'

        self.outputs.new('VerticesSocket', 'vertices', 'vertices')
        self.outputs.new('StringsSocket', 'edges', 'edges')
        self.outputs.new('StringsSocket', 'polygons', 'polygons')

    def update(self):
        if not 'polygons' in  self.outputs:
            return

        if 'vertices' in self.inputs and self.inputs['vertices'].links and \
            'edges' in self.inputs and self.inputs['edges'].links:

            verts = SvGetSocketAnyType(self,self.inputs['vertices'])
            edges = SvGetSocketAnyType(self,self.inputs['edges'])
            sides = repeat_last(self.inputs['Sides'].sv_get()[0])
            verts_out = []
            edges_out = []
            polys_out = []

            for v,e,s in zip(verts,edges,sides):
                res = fill_holes(v,e,int(s)) 
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
    bpy.utils.register_class(SvFillHolesNode)

def unregister():
    bpy.utils.unregister_class(SvFillHolesNode)

if __name__ == "__main__":
    register()
