import bmesh
import bpy
from node_tree import SverchCustomTreeNode
from data_structure import (updateNode, Vector_generate,
                            SvSetSocketAnyType, SvGetSocketAnyType)

# based on CrossSectionNode
# but using python bmesh code for driving
# by Linus Yng

def soldify(vertices, faces, t):

    if not faces or not vertices:
        return False

    if len(faces[0])==2:
        return False

    bm=bmesh.new()
    bm_verts =[bm.verts.new(v) for v in vertices]
    for face in faces:
        bm.faces.new([bm_verts[i] for i in face])

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


class SvSolidifyNode(bpy.types.Node, SverchCustomTreeNode):
    '''Soldifies geometry'''
    bl_idname = 'SvSolidifyNode'
    bl_label = 'Solidify'
    bl_icon = 'OUTLINER_OB_EMPTY'

    thickness = bpy.props.FloatProperty(name='thickness', description='Shell thickness', default=0.1, update=updateNode)

    def init(self, context):
        self.inputs.new('VerticesSocket', 'vertices', 'vertices')
        self.inputs.new('StringsSocket', 'polygons', 'polygons')

        self.outputs.new('VerticesSocket', 'vertices', 'vertices')
        self.outputs.new('StringsSocket', 'edges', 'edges')
        self.outputs.new('StringsSocket', 'polygons', 'polygons')

    def draw_buttons(self, context, layout):
        layout.prop(self,'thickness',text="Thickness")

    def update(self):
        if not self.outputs['vertices'].links:
            return

        if 'vertices' in self.inputs and self.inputs['vertices'].links and \
            'polygons' in self.inputs and self.inputs['polygons'].links:


            verts = Vector_generate(SvGetSocketAnyType(self,self.inputs['vertices']))
            polys = SvGetSocketAnyType(self,self.inputs['polygons'])
            #print (verts,polys)

            verts_out = []
            edges_out = []
            polys_out = []

            for obj in zip(verts,polys):
                res = soldify(obj[0], obj[1], self.thickness)
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
