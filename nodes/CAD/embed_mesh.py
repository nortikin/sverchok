import bpy,mathutils,bmesh,math

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.utils.modules.vertex_utils import adjacent_edg_pol
from sverchok.utils.modules.edge_utils import adjacent_faces_idx
from sverchok.utils.modules.polygon_utils import pols_edges
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata,pydata_from_bmesh
from sverchok.utils.meshes import join,to_mesh
from sverchok.nodes.analyzer.distance_point_line import compute_distance
class Embed_Mesh:
    def __init__(self,accuracy):
        self.epsilon = 1/10**accuracy
    def get_mesh(self,Verts,Edges,Faces, V_index):
        'get mesh data by vertices index list'
        adjacent_e = adjacent_edg_pol(Verts,Edges)
        adjacent_f = adjacent_edg_pol(Verts,Faces)
        Mesh = []
        for V_i in V_index:
            verts = [Verts[i] for i in V_i]
            a_edges = set(tuple(e) for i in V_i for e in adjacent_e[i])
            a_faces = set(tuple(f) for i in V_i for f in adjacent_f[i])
            edges = []
            for e in a_edges:
                try:
                    ind1 , ind2 = V_i.index(e[0]),V_i.index(e[1])
                    edges.append((ind1,ind2))
                except:
                    pass
            faces = []
            for f in a_faces:
                try:
                    face = tuple(V_i.index(i) for i in f)
                    faces.append(face)
                except:
                    pass
            Mesh.append([verts,edges,faces])
        return Mesh
    def to_xy(self,verts:mathutils.Vector,point):
        "point on 3d face to 2d face"
        vector1,vector2 = verts[0]-verts[1] , verts[2]-verts[1]
        l1,l2 = vector1.length,vector2.length
        angle = vector1.angle(vector2)

        point0_xy = mathutils.Vector((l1,0,0))
        point1_xy = mathutils.Vector((0,0,0))
        
        x,y = math.cos(angle)*l2 ,math.sin(angle)*l2
        point3_xy = mathutils.Vector((x,y,0))

        point_xy = []
        for p in point:
            new_point = mathutils.geometry.barycentric_transform(
                p,verts[0],verts[1],verts[2],point0_xy,point1_xy,point3_xy).to_2d()
            point_xy.append(new_point)
        return point_xy
    def delaunay_mesh(self,V_A,F_A,V_B,E_B,F_B,Index):
        'return delaunay mesh'
        #get [f_ind,...] and [[v_ind,...],...]
        F_ind = tuple(set(Index))
        V_ind = [[] for i in F_ind]
        for v_i,f_ind in enumerate(Index):
            ind = F_ind.index(f_ind)
            V_ind[ind] += [v_i]
        #get mesh data by V_ind
        Mesh = self.get_mesh(V_B,E_B,F_B,V_ind)
        #delaunay each face and get new_mesh
        New_mesh = []
        for f_i,mesh in zip(F_ind,Mesh):
            verts,edges,faces = mesh
            verts_a = [mathutils.Vector(V_A[i]) for i in F_A[f_i]]
            verts = [mathutils.Vector(v) for v in verts]

            verts += verts_a
            verts_xy = self.to_xy(verts_a,verts)

            n1,n2 = len(verts),len(verts_a)
            face_edge = [(e1,e2) for e1,e2 in zip(range(n1)[-n2:],list(range(n1)[1-n2:])+[range(n1)[-n2]])]
            edges += face_edge
            #Remove faces with point coincidences to prevent Mode 4 of the delaunay_2d_cdt from crashing
            for n,f in enumerate(faces):
                num = len(set([verts[i].to_tuple() for i in f]))
                if num != len(f):
                    faces[n] = []

            data = mathutils.geometry.delaunay_2d_cdt(verts_xy,edges,faces,4,self.epsilon,False)

            #Delaunay may remove certain coincident points, which will scramble the edge and surface data of the mesh, correct it (re-search sorting)
            re_verts = []
            for ver in data[0]:
                try:
                    i = verts_xy.index(ver)
                except:
                    l = [(v-ver).length for v in verts_xy]
                    i = l.index(min(l))
                re_verts.append(verts[i])
            
            New_mesh.append([[v.to_tuple() for v in re_verts],data[1],data[2]])
        
        return F_ind,New_mesh
    def bmesh_ops(self,mesh,V_B,E_B):
        "merge by distan and connect pair "
        bm:bmesh = bmesh_from_pydata(*mesh,normal_update=True)
        bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=self.epsilon)
        bmesh.ops.dissolve_degenerate(bm,dist=self.epsilon,edges=bm.edges)
        bm.verts.ensure_lookup_table()

        #Split edge, a surface with a dissolved area of 0
        kd = mathutils.kdtree.KDTree(len(bm.verts[:]))
        for i,v in enumerate(bm.verts):
            kd.insert(v.co,i)
        kd.balance()
        V_B = [mathutils.Vector(v) for v in V_B]
        pair_v = []
        for e in E_B:
            v1,v2 = V_B[e[0]],V_B[e[1]]
            i1,i2 = kd.find(v1)[1],kd.find(v2)[1]
            if i1 == i2 :
                continue
            pair_v.append([bm.verts[i1],bm.verts[i2]])
        path_edges = []
        for pair in pair_v:
            edge = bm.edges.get(pair)
            if edge is None:
                bm_edge = bmesh.ops.connect_vert_pair(bm,verts=pair)
                path_edges.extend([e for e in bm_edge['edges']])
            else:
                path_edges.append(edge)
        bm.edges.ensure_lookup_table()
        out_ind = [e.index for e in path_edges]

        out_v,out_e,out_f = pydata_from_bmesh(bm)
        bm.free()
        return out_v,out_e,out_f,out_ind
    def restructure(self,Index,V_B,V_A,E_A,F_A):
        'Consider the situation where the points are on the edges and reconstruct the data'
        #Prepare mesh A, coplanar data of edges, edge data of polygons, data to tuple data
        adjacent_faces = adjacent_faces_idx(E_A,F_A)
        edges = pols_edges(F_A)
        E_A = [tuple(e) for e in E_A]
        #For each pair (point:polygon): Whether the point is on the edge of the polygon, find another polygon that uses that edge, and if it exists, update to add a pair (point:polygon)
        new_Index = tuple((i for i in Index))
        for v_i,f_i in enumerate(Index):
            face_edges = edges[f_i]
            p = mathutils.Vector(V_B[v_i])
            for edge in face_edges:
                line1,line2 = mathutils.Vector(V_A[edge[0]]),mathutils.Vector(V_A[edge[1]])
                if compute_distance(p,line1,line2,[self.epsilon])[1]:
                    try:
                        ind = E_A.index(edge)
                    except:
                        ind = E_A.index((edge[1],edge[0]))
                    faces = adjacent_faces[ind].copy()
                    faces.remove(f_i)
                    if faces:
                        V_B.append(V_B[v_i])
                        new_Index += (faces[0],)
        return V_B,new_Index
    def main(self,V_A,E_A,F_A,V_B,E_B,F_B,Index):
        """
        V_A,E_A,F_A,V_B,E_B,F_B: mesh data of A,B
        Index:The face index of A, the attribution of each point of B
        return new mesh(B embed A) and edges index of B in new mesh
        """
        #Consider the points on the side
        V_B,Index = self.restructure(Index,V_B,V_A,E_A,F_A)
        #delaunay face of Index-data
        F_ind,New_mesh = self.delaunay_mesh(V_A,F_A,V_B,E_B,F_B,Index)
        #join delaunay mesh and remain mesh
        f_mask = [True for i in F_A]
        for i in F_ind:
            f_mask[i] = False
        F_A = [f for i,f in enumerate(F_A) if f_mask[i]]
        meshes = New_mesh + [[V_A,E_A,F_A]]
        meshes = [to_mesh(*mesh) for mesh in meshes]
        py_mesh = join(meshes)
        mesh = [py_mesh.vertices.data,py_mesh.edges.data,py_mesh.polygons.data]
        #merge by distan and connect pair 
        out_v,out_e,out_f,out_ind = self.bmesh_ops(mesh,V_B,E_B)
        return out_v,out_e,out_f,out_ind

class SvEmbedMesh(SverchCustomTreeNode,bpy.types.Node):
    """
    Triggers: Embed the structure of mesh B into A
    Tooltip: The structure of mesh B is embedded into A, and the points of B must be on the face of A
    """
    bl_idname = 'SvEmbedMesh'
    bl_label = 'Embed Mesh'
    bl_icon = "AUTOMERGE_ON"

    accuracy: bpy.props.IntProperty(name='Accuracy',
    description='The overall accuracy of the algorithm, which controls multiple key places',
    default=5,min=3,max=12,update=updateNode)

    def draw_buttons_ext(self, context, layout):
        layout.prop(self,'accuracy')

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket','VertsA')
        self.inputs.new('SvStringsSocket','EdgesA')
        self.inputs.new('SvStringsSocket', "FacesA")
        self.inputs.new('SvVerticesSocket','VertsB')
        self.inputs.new('SvStringsSocket','EdgesB')
        self.inputs.new('SvStringsSocket', "FacesB")
        self.inputs.new('SvStringsSocket','Index')

        self.outputs.new('SvVerticesSocket','Verts')
        self.outputs.new('SvStringsSocket','Edges')
        self.outputs.new('SvStringsSocket', "Faces")
        self.outputs.new('SvStringsSocket', "Index")
    def process(self):
        out = []
        for V_A,E_A,F_A,V_B,E_B,F_B,I in zip(
        self.inputs['VertsA'].sv_get(default=[[]]),
        self.inputs['EdgesA'].sv_get(default=[[]]),
        self.inputs['FacesA'].sv_get(default=[[]]),
        self.inputs['VertsB'].sv_get(default=[[]]),
        self.inputs['EdgesB'].sv_get(default=[[]]),
        self.inputs['FacesB'].sv_get(default=[[]]),
        self.inputs['Index'].sv_get(default=[[]])) :
            out.append(Embed_Mesh(self.accuracy).main(V_A,E_A,F_A,V_B,E_B,F_B,I))
        out_v,out_e,out_f,out_ind = zip(*out)
        self.outputs['Verts'].sv_set(out_v)
        self.outputs['Edges'].sv_set(out_e)
        self.outputs['Faces'].sv_set(out_f)
        self.outputs['Index'].sv_set(out_ind)

def register():
    bpy.utils.register_class(SvEmbedMesh)


def unregister():
    bpy.utils.unregister_class(SvEmbedMesh)
