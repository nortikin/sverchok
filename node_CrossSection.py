import bpy, bmesh, mathutils
from mathutils import Vector, Matrix
from node_s import *
from util import *
from math import *


def section(cut_me_vertices, cut_me_edges, mx, pp, pno):
    """Finds the section mesh between a mesh and a plane 
    cut_me: Blender Mesh - the mesh to be cut
    mx: Matrix - The matrix of object of the mesh for correct coordinates
    pp: Vector - A point on the plane
    pno: Vector - The cutting plane's normal
    Returns: Mesh - the resulting mesh of the section if any or
             Boolean - False if no section exists""" 
    
    verts = []
    ed_xsect = {}
    x_me = {}
    cut_me_polygons = cut_me_edges.copy() if len(cut_me_edges)>2 else []
    
    cut_me_edges = []
    for elem_p in cut_me_polygons:
        for idx,elem_v in enumerate(elem_p[:-1]):
            cut_me_edges.append((elem_v, elem_p[idx+1]))
    
    print('\ncut_me_polygons, cut_me_edges\n',cut_me_polygons, cut_me_edges)
        
    for ed_idx,ed in enumerate(cut_me_edges):
        # getting a vector from each edge vertices to a point on the plane  
        # first apply transformation matrix so we get the real section
        
        vert1 = ed[0]
        v1 = cut_me_vertices[vert1] * mx.transposed() 
        co1 = v1 - pp
        vert2 = ed[1]
        v2 = cut_me_vertices[vert2] * mx.transposed() 
        co2 = v2 - pp

        # projecting them on the normal vector
        proj1 = co1.project(pno).length
        proj2 = co2.project(pno).length

        if (proj1 != 0):
            rad1 = co1.angle(pno)
            angle1 = round((180 * rad1 / pi),4)

        else: angle1 = 0
        if (proj2 != 0):
            rad2 = co2.angle(pno)
            angle2 = round((180 * rad2 / pi),4)

        else: angle2 = 0
        
        if ((proj1 == 0) or (proj2 == 0) or  \
            (angle1 > 90) != (angle2 > 90)) and  \
            (proj1+proj2 > 0):
            
            proj1 /= proj1+proj2
            co = ((v2-v1)*proj1)+v1

            verts.append(co)
            ed_xsect[ed_idx] = (ed,len(verts)-1)
            
            
    x_me['Verts'] = verts
    edges = set()
    for f in cut_me_edges:
        ps=set()
        for v in f:
            for ed in ed_xsect.keys():
                if v in ed_xsect[ed][0]:
                    ps.add((ed, ed_xsect[ed][1]))
    
        lps=list(ps)
        if len(lps)==2:
            print('bnbnbn',ps)    
            edges.add((lps[0][1], lps[1][1]))
            
    x_me['Edges'] = list(edges)
    
    print('\nX-me',x_me)    
    if verts:
        return x_me
    else:
        return False


class CrossSectionNode(Node, SverchCustomTreeNode):
    bl_idname = 'CrossSectionNode'
    bl_label = 'Cross Section'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    def init(self, context):
        self.inputs.new('VerticesSocket', 'vertices', 'vertices')
        self.inputs.new('StringsSocket', 'edg_pol', 'edg_pol')
        self.inputs.new('MatrixSocket', 'matrix', 'matrix')
        self.inputs.new('MatrixSocket', 'cut_matrix', 'cut_matrix')
        
        self.outputs.new('VerticesSocket', 'vertices', 'vertices')
        self.outputs.new('StringsSocket', 'edges', 'edges')
        #self.outputs.new('MatrixSocket', 'matrix', 'matrix')
                
    
    def update(self):
        if 'vertices' in self.inputs and self.inputs['vertices'].links \
            and self.inputs['edg_pol'].links and self.inputs['matrix'].links \
            and self.inputs['cut_matrix'].links:
                
            if not self.inputs['vertices'].node.socket_value_update:
                self.inputs['vertices'].node.update()
            if not self.inputs['edg_pol'].node.socket_value_update:
                self.inputs['edg_pol'].node.update()
            if not self.inputs['matrix'].node.socket_value_update:
                self.inputs['matrix'].node.update()
            if not self.inputs['cut_matrix'].node.socket_value_update:
                self.inputs['cut_matrix'].node.update()
        
            verts_ob = Vector_generate(eval(self.inputs['vertices'].links[0].from_socket.VerticesProperty))
            edg_pols_ob = eval(self.inputs['edg_pol'].links[0].from_socket.StringsProperty)
            matrixs = eval(self.inputs['matrix'].links[0].from_socket.MatrixProperty)
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
                    
                    x_me = section(verts_ob[idx_vob], edg_pols_ob[idx_epob], matrix, pp, pno)
                    if x_me:
                        verts_pre_out.append(x_me['Verts'])
                        edges_pre_out.append(x_me['Edges'])
                
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
            
           

    def update_socket(self, context):
        self.update()

def register():
    bpy.utils.register_class(CrossSectionNode)   
    
def unregister():
    bpy.utils.unregister_class(CrossSectionNode)

if __name__ == "__main__":
    register()











