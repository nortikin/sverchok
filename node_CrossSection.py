import bpy, bmesh, mathutils
from mathutils import Vector, Matrix
from node_s import *
from util import *
from math import *


def section(cut_me_vertices, cut_me_edges, mx, pp, pno, FILL=False, TRI=True):
    """Finds the section mesh between a mesh and a plane 
    cut_me: Blender Mesh - the mesh to be cut
    mx: Matrix - The matrix of object of the mesh for correct coordinates
    pp: Vector - A point on the plane
    pno: Vector - The cutting plane's normal
    Returns: Mesh - the resulting mesh of the section if any or
             Boolean - False if no section exists""" 
    
    
    def equation_plane(point, normal_dest):
        #получаем коэффициенты уравнения плоскости по точке и нормали
        normal = normal_dest.normalized()
        A = normal.x
        B = normal.y
        C = normal.z
        D = (A*point.x+B*point.y+C*point.z)*-1
        
        if A<0.0:
            A *= -1
            B *= -1
            C *= -1
            D *= -1
            
        return (A,B,C,D)

    
    def point_on_plane(v1, ep):
        formula = ep[0]*v1.x+ep[1]*v1.y+ep[2]*v1.z+ep[3]
        if formula==0.0:
            return True
        else:
            return False
    
    if not cut_me_edges or not cut_me_vertices:
        return False
    
    verts = []
    ed_xsect = {}
    x_me = {}
    
    ep = equation_plane(pp, pno)
    cut_me_polygons=[]
    if len(cut_me_edges[0])>2:
        cut_me_polygons = cut_me_edges.copy() 
        cut_me_edges=[]

    new_me = bpy.data.meshes.new('tempus')
    new_me.from_pydata(cut_me_vertices, cut_me_edges, cut_me_polygons)
    new_me.update(calc_edges=True)
        
    for ed_idx,ed in enumerate(new_me.edges):
        # getting a vector from each edge vertices to a point on the plane  
        # first apply transformation matrix so we get the real section
        
        vert1 = ed.vertices[0]
        v1 = new_me.vertices[vert1].co * mx.transposed() 

        vert2 = ed.vertices[1]
        v2 = new_me.vertices[vert2].co * mx.transposed()
        
        vec = v2-v1
        mul = vec * pno
        if mul==0.0:
            if not point_on_plane(v1, ep):
                #parallel and not on plane
                continue
        
        epv = ep[0]*vec.x + ep[1]*vec.y + ep[2]*vec.z
        if epv==0: 
            t0=0
        else:
            t0 = -(ep[0]*v1.x+ep[1]*v1.y+ep[2]*v1.z + ep[3]) / epv
            
        pq = vec*t0+v1
        if (pq-v1).length <= vec.length and (pq-v2).length <= vec.length :
            verts.append(pq)
            ed_xsect[ed.key] = len(ed_xsect)
        
    edges = []
    for f in new_me.polygons:
        # get the edges that the intersecting points form
        # to explain this better:
        # If a face has an edge that is proven to be crossed then use the
        # mapping we created earlier to connect the edges properly
        ps = [ ed_xsect[key] for key in f.edge_keys if key in ed_xsect]

        if len(ps) == 2:
            edges.append(tuple(ps))
    
    x_me['Verts'] = verts
    x_me['Edges'] = edges
    bpy.data.meshes.remove(new_me) 
    if x_me:
        if edges and FILL:
            me = bpy.data.meshes.new('Section')
            me.from_pydata(verts,edges,[])
            
            #create a temp object and link it to the current scene to be able to 
            #apply rem Doubles and fill 
            tmp_ob = bpy.data.objects.new('Mesh', me)
    
            sce = bpy.context.scene
            sce.objects.link(tmp_ob)
            
            # do a remove doubles to cleanup the mesh, this is needed when there
            # is one or more edges coplanar to the plane.
            sce.objects.active = tmp_ob
    
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_mode(type="EDGE", action="ENABLE")
            bpy.ops.mesh.select_all(action="SELECT")
    
            # remove doubles:
            bpy.ops.mesh.remove_doubles()
            
            #one or not one polygon? here is the answer!
            if TRI:
                bpy.ops.mesh.edge_face_add()
            else:
                bpy.ops.mesh.fill()
                bpy.ops.mesh.tris_convert_to_quads()

            # recalculate outside normals:
            bpy.ops.mesh.normals_make_consistent(inside=False)
    
            bpy.ops.object.mode_set(mode='OBJECT')
            pols=[]
            for p in me.polygons:
                vs=[]
                for v in p.vertices:
                    vs.append(v)
                pols.append(vs)
            
            verts=[]
            for v in me.vertices:
                verts.append(v.co)

            if not pols:
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_mode(type="VERT", action="ENABLE")
                bpy.ops.mesh.select_all(action="SELECT")
                bpy.ops.mesh.edge_face_add()
                bpy.ops.object.mode_set(mode='OBJECT')
                
                for p in me.polygons:
                    vs=[]
                    for v in p.vertices:
                        vs.append(v)
                    pols.append(vs)
            
            x_me['Verts'] = verts    
            x_me['Edges'] = pols
            
            #Cleanup
            sce.objects.unlink(tmp_ob)
            del tmp_ob
        return x_me
    else:
        return False
    


class CrossSectionNode(Node, SverchCustomTreeNode):
    bl_idname = 'CrossSectionNode'
    bl_label = 'Cross Section'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    fill_check = bpy.props.BoolProperty(name='fill', description='to fill section', default=False, update=updateNode)
    tri = bpy.props.BoolProperty(name='tri', description='triangle or polygon', default=True, update=updateNode)
    
    def init(self, context):
        self.inputs.new('VerticesSocket', 'vertices', 'vertices')
        self.inputs.new('StringsSocket', 'edg_pol', 'edg_pol')
        self.inputs.new('MatrixSocket', 'matrix', 'matrix')
        self.inputs.new('MatrixSocket', 'cut_matrix', 'cut_matrix')
        
        self.outputs.new('VerticesSocket', 'vertices', 'vertices')
        self.outputs.new('StringsSocket', 'edges', 'edges')
        #self.outputs.new('MatrixSocket', 'matrix', 'matrix')
                
    def draw_buttons(self, context, layout):
        layout.prop(self, "fill_check", text="Fill section")
        layout.prop(self, "tri", text="alt+F / F")
        
    def update(self):
        if 'vertices' in self.inputs and self.inputs['vertices'].links \
            and self.inputs['edg_pol'].links \
            and self.inputs['cut_matrix'].links:
                
            if not self.inputs['vertices'].node.socket_value_update:
                self.inputs['vertices'].node.update()
            if not self.inputs['edg_pol'].node.socket_value_update:
                self.inputs['edg_pol'].node.update()
            if not self.inputs['cut_matrix'].node.socket_value_update:
                self.inputs['cut_matrix'].node.update()
        
            verts_ob = Vector_generate(eval(self.inputs['vertices'].links[0].from_socket.VerticesProperty))
            edg_pols_ob = eval(self.inputs['edg_pol'].links[0].from_socket.StringsProperty)
            
            if self.inputs['matrix'].links:
                if not self.inputs['matrix'].node.socket_value_update:
                    self.inputs['matrix'].node.update()
                matrixs = eval(self.inputs['matrix'].links[0].from_socket.MatrixProperty)
            else:
                matrixs = []
                for le in verts_ob:
                    matrixs.append(Matrix())
            cut_mats = eval(self.inputs['cut_matrix'].links[0].from_socket.MatrixProperty)
            
            verts_out = []
            edges_out = []
            for cut_mat in cut_mats:
                cut_mat = Matrix(cut_mat)
                pp = Vector((0.0, 0.0, 0.0)) * cut_mat.transposed()
                pno = Vector((0.0, 0.0, 1.0)) * cut_mat.to_3x3().transposed()
                
                verts_pre_out = []
                edges_pre_out = []
                for idx_mob, matrix in enumerate(matrixs):
                    idx_vob = min(idx_mob, len(verts_ob)-1)
                    idx_epob = min(idx_mob, len(edg_pols_ob)-1)
                    matrix = Matrix(matrix)
                    
                    x_me = section(verts_ob[idx_vob], edg_pols_ob[idx_epob], matrix, pp, pno, self.fill_check, self.tri)
                    if x_me:
                        verts_pre_out.append(x_me['Verts'])
                        edges_pre_out.append(x_me['Edges'])
                
                if verts_pre_out:
                    verts_out.extend(verts_pre_out)
                    edges_out.extend(edges_pre_out)
            
            if 'vertices' in self.outputs and len(self.outputs['vertices'].links)>0:
                if not self.outputs['vertices'].node.socket_value_update:
                    self.outputs['vertices'].node.update()
                output = Vector_degenerate(verts_out)
                self.outputs['vertices'].VerticesProperty = str(output)
            
            if 'edges' in self.outputs and len(self.outputs['edges'].links)>0:
                if not self.outputs['edges'].node.socket_value_update:
                    self.outputs['edges'].node.update()
                self.outputs['edges'].StringsProperty = str(edges_out) 
            
        else:
            self.outputs['vertices'].VerticesProperty = str([])
            self.outputs['edges'].StringsProperty = str([])
        

    def update_socket(self, context):
        self.update()

def register():
    bpy.utils.register_class(CrossSectionNode)   
    
def unregister():
    bpy.utils.unregister_class(CrossSectionNode)

if __name__ == "__main__":
    register()







