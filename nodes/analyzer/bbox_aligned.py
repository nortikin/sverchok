# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

from itertools import product
import numpy as np
import bpy
from bpy.props import BoolVectorProperty, EnumProperty, BoolProperty, FloatProperty
from mathutils import Matrix

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.nodes_mixins.recursive_nodes import SvRecursiveNode
from sverchok.utils.sv_mesh_utils import mesh_join
from sverchok.utils.modules.matrix_utils import matrix_apply_np

from sverchok.data_structure import dataCorrect, updateNode, zip_long_repeat
from sverchok.utils.geom import bounding_box_aligned

class SvAlignedBBoxNode(SverchCustomTreeNode, bpy.types.Node, SvRecursiveNode):
    """
    Triggers: Bbox 2D or 3D
    Tooltip: Get vertices bounding box (vertices, sizes, center)
    """
    bl_idname = 'SvAlignedBBoxNode'
    bl_label = 'Aligned Bounding Box'
    bl_icon = 'SHADING_BBOX'
    sv_icon = 'SV_BOUNDING_BOX'

    mesh_join : BoolProperty(
        name = "merge",
        description = "If checked, join mesh elements into one object",
        default = False,
        update = updateNode)
    
    factor : FloatProperty(
                name = "Factor",
                description = "Matrix interpolation",
                default = 1.0,
                min=0.0, max=1.0, 
                update = updateNode)


    def update_sockets(self, context):
        updateNode(self, context)


    def draw_buttons(self, context, layout):
        layout.row().prop(self, 'mesh_join')
        pass

    def sv_init(self, context):
        son = self.outputs.new
        self.inputs.new('SvVerticesSocket', 'Vertices')
        #self.inputs.new('SvStringsSocket', 'Faces')
        self.inputs.new('SvMatrixSocket', 'Matrix')
        self.inputs.new('SvStringsSocket', 'Factor').prop_name = 'factor'

        son('SvVerticesSocket', 'Vertices')
        #son('SvVerticesSocket', 'Vertices_tests')
        son('SvStringsSocket', 'Edges')
        son('SvStringsSocket', 'Faces')
        son('SvMatrixSocket', "Matrix")

        son('SvStringsSocket', 'Length')
        son('SvStringsSocket', 'Width')
        son('SvStringsSocket', 'Height')
        

        self.update_sockets(context)

    def process(self):
        inputs = self.inputs
        Vertices = inputs["Vertices"].sv_get(default=None)
        Faces    = [[]] #inputs["Faces"].sv_get(default=[[]])
        Matrixes = inputs["Matrix"].sv_get(default=-1)
        if Matrixes==-1:
            Matrixes = [None]
        Factors  = inputs["Factor"].sv_get()

        outputs = self.outputs
        if not outputs['Vertices'].is_linked or not all([Vertices,]):
            return
        
        lst_bba_vertices = []
        lst_bba_edges = []
        lst_bba_faces = []
        lst_bba_matrix = []
        lst_bba_Length = []
        lst_bba_Width = []
        lst_bba_Height = []
        m = None
        for verts, faces, matrix, factor in zip_long_repeat(Vertices, Faces, Matrixes, Factors[0]):
            # align verts to Oxy plane. Find first vectors that are not complanar and use then to align to Oxy

            

            np_verts = np.array(verts)

            evec_external = None
            # T, R, S = None, None, None
            # if matrix is not None:
            #     T, R, S = matrix.decompose()
            #     R = np.array(R.to_matrix())
            # if faces:
            #     # calc faces normals:
            #     edges_vectors = np.empty((0,2), dtype=np.int32)
            #     for face in faces:
            #         np_faces = np.array(face)
            #         edges = np.dstack( (np_faces, np.roll(np_faces,1) ) )
            #         edges_vectors = np.vstack( (edges_vectors, edges[0]) ) if edges_vectors.size else edges[0]
            #         #edges_vectors.extend( edges )
            #     unique_edges_indexes = np.unique( np.sort( edges_vectors ).reshape(-1,2), axis=0 )
            #     edges_vectors = np_verts[ unique_edges_indexes ][:,1] - np_verts[ unique_edges_indexes ][:,0]
            #     edges_vectors_unique, edges_vectors_count = np.unique( edges_vectors, axis=0, return_counts=True)
            #     # np_unique_vectors = np.empty((0,3), dtype=np.float64)
            #     # np_unique_vectors = np.vstack( (np_unique_vectors, edges_vectors_unique[0]) )
            #     np_unique_vectors = np.array( [ edges_vectors[0] ])
            #     # np_unique_counts = np.empty((0), dtype=np.int32)
            #     # np_unique_counts = np.dstack( (np_unique_counts, edges_vectors_count[0]) )
            #     np_counts = np.array( 0 )
            #     for i, vec in enumerate(edges_vectors[1:]):  # skip first element. It is used
            #         exists_vectors = ( abs(np.linalg.norm(np.cross( np_unique_vectors, np.repeat([vec], np_unique_vectors.shape[0], axis=0)), axis=1))>1e-6 )
            #         #print(f'{i}. exists_vectors={exists_vectors.tolist()}')
            #         if np.all(exists_vectors):
            #             np_unique_vectors = np.vstack( (np_unique_vectors, vec) )
            #             np_counts  = np.dstack( ( np_counts, 1) )
            #         else:
            #             np_counts = np_counts+np.invert(exists_vectors)*1
                
            #     max_vectors = np.argsort( np_counts ).reshape(-1)
            #     evec_external = np_unique_vectors[[max_vectors[-3:]]][0]
            #     #evec_external = evec_external/np.linalg.norm(evec_external, axis=0)
            #     evec_external = [ex/np.linalg.norm(ex, axis=0) for ex in evec_external]
            #     #print(f'max_vectors={max_vectors.tolist()}, {np_counts.tolist()}')

            #     X = evec_external[-1]
            #     Y = evec_external[-2]
            #     Z = np.cross(X,Y)
            #     Y = np.cross(Z,X)
            #     X = X/np.linalg.norm(X)
            #     Y = Y/np.linalg.norm(Y)
            #     Z = Z/np.linalg.norm(Z)
            #     m = np.matrix(
            #         [[X[0], Y[0], Z[0], 0.0],
            #         [X[1], Y[1], Z[1], 0.0],
            #         [X[2], Y[2], Z[2], 0.0],
            #         [ 0.0,  0.0,  0.0, 1.0]] )
            #     np_verts = matrix_apply_np(np_verts, np.linalg.inv(m) )
            #     pass
            # else:
            #     vb0 = np_verts[0]
            #     vbc0 = None
            #     vbc1 = None
            #     for v in np_verts:
            #         if np.linalg.norm(vb0-v)>1e-5:
            #             vbc0 = v - vb0
            #             break

            #     if vbc0 is not None:
            #         for v in np_verts:
            #             if abs(np.linalg.norm(np.cross(vb0-v, vbc0)))>1e-5:
            #                 vbc1 = v - vb0
            #                 break

            #     if vbc0 is not None and vbc1 is not None:
            #         # vbc0 and vbc1 has to reorient all vertices to Oxy (vbc0 to Ox)
            #         X = vbc0
            #         Y = vbc1
            #         Z = np.cross(X,Y)
            #         Y = np.cross(Z,X)
            #         X = X/np.linalg.norm(X)
            #         Y = Y/np.linalg.norm(Y)
            #         Z = Z/np.linalg.norm(Z)
            #         m = np.matrix(
            #             [[X[0], Y[0], Z[0], 0.0],
            #             [X[1], Y[1], Z[1], 0.0],
            #             [X[2], Y[2], Z[2], 0.0],
            #             [ 0.0,  0.0,  0.0, 1.0]] )
            #         np_verts = matrix_apply_np(np_verts, np.linalg.inv(m) )
            #         # np_verts_min = np.min(np_verts, axis=0)
            #         # np_verts_max = np.max(np_verts, axis=0)
            #         # np_verts = np.vstack( (np_verts,
            #         #               [np_verts_min[2]-.01, 0.0, 0.0],
            #         #               [np_verts_max[2]+.01, 0.0, 0.0],
            #         #               [0.0, np_verts_min[2]-.02, 0.0],
            #         #               [0.0, np_verts_max[2]+.02, 0.0],
            #         #               [0.0, 0.0, np_verts_min[2]-.03],
            #         #               [0.0, 0.0, np_verts_max[2]+.03],
            #         #               ) )
            #         pass

            # if m is not None:
            #     x_min, x_max = np.min(np_verts[:,0]), np.max(np_verts[:,0])
            #     y_min, y_max = np.min(np_verts[:,1]), np.max(np_verts[:,1])
            #     z_min, z_max = np.min(np_verts[:,2]), np.max(np_verts[:,2])
            #     x_size = x_max - x_min
            #     y_size = y_max - y_min
            #     z_size = z_max - z_min

            #     if abs(x_size-z_size)<1e-6 and abs(y_size-z_size)<1e-6:
            #         # object is symmetrical all axis
            #         print(f'symmetrical 3d: {x_size}, {y_size}, {z_size}')
            #         np_verts = np.vstack( (np_verts,
            #                       [x_min-.01, 0.0, 0.0],
            #                       [x_max+.01, 0.0, 0.0],
            #                       [0.0, y_min-.02, 0.0],
            #                       [0.0, y_max+.02, 0.0],
            #                       [0.0, 0.0, z_min-.03],
            #                       [0.0, 0.0, z_max+.03],
            #                       ) )
            #         pass
            #     elif abs(x_size-z_size)<1e-6 or abs(y_size-z_size)<1e-6 or abs(x_size-y_size)<1e-6:
            #         print(f'symmetrical 2d: {x_size}, {y_size}, {z_size}')
            #         if abs(x_size-z_size)<1e-6:
            #             np_verts = np.vstack( (np_verts,
            #                         [x_min-.01, 0.0, 0.0],
            #                         [x_max+.01, 0.0, 0.0],
            #                         [0.0, 0.0, z_min-.03],
            #                         [0.0, 0.0, z_max+.03],
            #                         ) )
            #             pass
            #         elif abs(y_size-z_size)<1e-6:
            #             np_verts = np.vstack( (np_verts,
            #                         [0.0, y_min-.02, 0.0],
            #                         [0.0, y_max+.02, 0.0],
            #                         [0.0, 0.0, z_min-.03],
            #                         [0.0, 0.0, z_max+.03],
            #                         ) )
            #             pass
            #         else:
            #             np_verts = np.vstack( (np_verts,
            #                         [x_min-.01, 0.0, 0.0],
            #                         [x_max+.01, 0.0, 0.0],
            #                         [0.0, y_min-.02, 0.0],
            #                         [0.0, y_max+.02, 0.0],
            #                         ) )
            #             pass
            #     else:
            #         print(f'symmetrical no: {x_size}, {y_size}, {z_size}')
            #         pass


            bba, mat, bbox_size = bounding_box_aligned(np_verts, evec_external=matrix, factor=factor)
            #print(f'bbox_size={bbox_size}')
            # if m is not None:
            #     bba = matrix_apply_np(bba, m )
            #     mat = m
            #     pass
            lst_bba_vertices.append( bba.tolist() )
            lst_bba_edges .append( [[0,1], [1,2], [2,3], [3,0], [0,4], [1,5], [2,6], [3,7], [4,5], [5,6], [6,7], [7,4]])
            lst_bba_faces .append( [[0,3,2,1], [0,1,5,4], [1,2,6,5], [2,3,7,6], [3,0,4,7], [4,5,6,7]])
            lst_bba_matrix.append( mat )
            lst_bba_Length.append( bbox_size[0] )
            lst_bba_Width .append( bbox_size[1] )
            lst_bba_Height.append( bbox_size[2] )

        if self.mesh_join:
            lst_bba_vertices, lst_bba_edges, lst_bba_faces = mesh_join(lst_bba_vertices, lst_bba_edges, lst_bba_faces)
            lst_bba_vertices, lst_bba_edges, lst_bba_faces = [lst_bba_vertices], [lst_bba_edges], [lst_bba_faces]
            # calc length, width, height
            pass

        outputs['Vertices'].sv_set(lst_bba_vertices)
        #outputs['Vertices_tests'].sv_set([np_verts.tolist()])
        outputs['Edges'].sv_set(lst_bba_edges)
        outputs['Faces'].sv_set(lst_bba_faces)
        outputs['Matrix'].sv_set(lst_bba_matrix)
        outputs['Length'].sv_set(lst_bba_Length)
        outputs['Width'].sv_set(lst_bba_Width)
        outputs['Height'].sv_set(lst_bba_Height)



def register():
    bpy.utils.register_class(SvAlignedBBoxNode)


def unregister():
    bpy.utils.unregister_class(SvAlignedBBoxNode)
