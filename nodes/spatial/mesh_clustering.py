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

from itertools import product, chain
import numpy as np
from sverchok.dependencies import pyacvd
if pyacvd is not None:
    from pyvista import examples, PolyData
#import pyacvd

import bpy
import bmesh
from bpy.props import BoolVectorProperty, EnumProperty, BoolProperty, FloatProperty, IntProperty
from mathutils import Matrix

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.nodes_mixins.recursive_nodes import SvRecursiveNode
from sverchok.utils.sv_mesh_utils import mesh_join
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata, pydata_from_bmesh
from sverchok.utils.modules.matrix_utils import matrix_apply_np

from sverchok.data_structure import dataCorrect, updateNode, zip_long_repeat, ensure_nesting_level, flatten_data
from sverchok.utils.geom import bounding_box_aligned

class SvMeshClusteringNode(SverchCustomTreeNode, bpy.types.Node, SvRecursiveNode):
    """
    Triggers: Bbox 2D or 3D
    Tooltip: Get vertices bounding box (vertices, sizes, center)
    """
    bl_idname = 'SvMeshClusteringNode'
    bl_label = 'Mesh Clustering (Alpha)'
    bl_icon = 'IMAGE_ALPHA'
    sv_icon = 'SV_DELAUNAY'
    sv_dependencies = {'pyacvd'}

    output_as_numpy : BoolProperty(
        name = "Output as numpy",
        description = "If checked then output sockets as numpy",
        default = False,
        update = updateNode)  # type: ignore

    subdiv_modes = [
        ( "butterfly", "Butterfly", "Butterfly and loop subdivision perform smoothing when dividing, and may introduce artifacts into the mesh when dividing", 0),
        (      "loop",      "Loop", "Butterfly and loop subdivision perform smoothing when dividing, and may introduce artifacts into the mesh when dividing", 1),
        (    "linear",    "Linear", "Linear subdivision results in the fastest mesh subdivision, but it does not smooth mesh edges, but rather splits each triangle into 4 smaller triangles", 2)
    ]

    quad_modes = [
        (    "BEAUTY",            "Beauty", "Split the quads in nice triangles, slower method", 1),
        (     "FIXED",             "Fixed", "Split the quads on the 1st and 3rd vertices", 2),
        ( "ALTERNATE",   "Fixed Alternate", "Split the quads on the 2nd and 4th vertices", 3),
        ("SHORT_EDGE", "Shortest Diagonal", "Split the quads based on the distance between the vertices", 4)
    ]

    ngon_modes = [
        (  "BEAUTY", "Beauty", "Arrange the new triangles nicely, slower method", 1),
        ("EAR_CLIP",   "Clip", "Split the ngons using a scanfill algorithm", 2)
    ]

    subdiv_mode: EnumProperty(
        name='Subdiv mode',
        description="Method of subdiv of mesh if param 'Cluster Subdivide'>0. If 'Cluster Subdivide'==0 then this parameter has no effect",
        items=subdiv_modes,
        default="loop",
        update=updateNode) # type: ignore
    
    quad_mode: EnumProperty(
        name='Quads mode',
        description="Quads processing mode",
        items=quad_modes,
        default="BEAUTY",
        update=updateNode) # type: ignore

    ngon_mode: EnumProperty(
        name="Polygons mode",
        description="Polygons processing mode",
        items=ngon_modes,
        default="BEAUTY",
        update=updateNode) # type: ignore
    
    cluster_subdivide : IntProperty(
        min=0, default=0, name='Subdivide',
        description="Cluster subdivide. (min=0). Connect with parameter 'Subdiv mode'.", update=updateNode) # type: ignore
    max_iter : IntProperty(
        min=1, default=100, name='Max iteration',
        description="Max iteration of clusterization. (min=0)", update=updateNode) # type: ignore

    cluster_counts : IntProperty(
        min=4, default=1000, name='Clusters',
        description="Cluster counts. (min=4)", update=updateNode) # type: ignore


    def update_sockets(self, context):
        updateNode(self, context)

    def draw_buttons_ext(self, context, layout):
        layout.row().prop(self, 'output_as_numpy')

    def draw_buttons(self, context, layout):

        col = layout.column()
        col.row().label(text="Triangulate mesh polygons:")

        row = col.row()
        split = row.split(factor=0.4)
        split.column().label(text="Quads mode:")
        split.column().row(align=True).prop(self, "quad_mode", text='')

        row = col.row()
        split = row.split(factor=0.5)
        split.column().label(text="Polygons mode:")
        split.column().row(align=True).prop(self, "ngon_mode", text='')

        row = col.row()
        split = row.split(factor=0.4)
        split.column().label(text="Subdiv mode:")
        split.column().row(align=True).prop(self, "subdiv_mode", text='')

        pass

    def sv_init(self, context):
        son = self.outputs.new
        self.inputs.new('SvStringsSocket' , 'cluster_subdivide').prop_name = 'cluster_subdivide'
        self.inputs.new('SvStringsSocket' , 'max_iter').prop_name = 'max_iter'
        self.inputs.new('SvStringsSocket' , 'cluster_counts').prop_name = 'cluster_counts'
        self.inputs.new('SvVerticesSocket', 'vertices')
        self.inputs.new('SvStringsSocket' , 'edges')
        self.inputs.new('SvStringsSocket' , 'polygons')
        self.inputs.new('SvMatrixSocket'  , "matrixes")

        self.inputs['vertices'].label = 'Vertices'
        self.inputs['edges'].label = 'Edges'
        self.inputs['polygons'].label = 'Polygons'
        self.inputs['matrixes'].label = 'Matrixes'

        self.inputs['cluster_subdivide'].label = "Cluster Subdivide"
        self.inputs['max_iter'].label = "Max Iteration"
        self.inputs['cluster_counts'].label = "Cluster counts"

        son('SvVerticesSocket', 'vertices')
        son('SvStringsSocket' , 'edges')
        son('SvStringsSocket' , 'polygons')
        son('SvVerticesSocket', 'polygon_centers')
        son('SvVerticesSocket', 'polygon_normals')

        self.outputs['vertices'].label = 'Vertices'
        self.outputs['edges'].label = 'Edges'
        self.outputs['polygons'].label = 'Polygons'
        self.outputs['polygon_centers'].label = 'Centers of Polygons'
        self.outputs['polygon_normals'].label = 'Normals of Polygons'
        self.width = 210
        

        self.update_sockets(context)

    def process(self):
        inputs = self.inputs
        _cluster_subdivide = inputs['cluster_subdivide'].sv_get(default=[[0]], deepcopy=False)
        cluster_subdivide = flatten_data(_cluster_subdivide)
        _max_iter = inputs['max_iter'].sv_get(default=[[20]], deepcopy=False)
        max_iter = flatten_data(_max_iter)
        _cluster_counts = inputs['cluster_counts'].sv_get(default=[[1000]], deepcopy=False)
        cluster_counts = flatten_data(_cluster_counts)

        _Vertices = inputs['vertices'].sv_get(default=[[]], deepcopy=False)
        Vertices  = ensure_nesting_level(_Vertices, 3)
        _Edges    = inputs['edges'].sv_get(default=[[]], deepcopy=False)
        Edges     = ensure_nesting_level(_Edges, 3)
        _Faces    = inputs['polygons'].sv_get(default=[[]], deepcopy=False)
        Faces     = ensure_nesting_level(_Faces, 3)
        _Matrixes    = inputs['matrixes'].sv_get(default=[[Matrix()]], deepcopy=False)
        Matrixes     = flatten_data(_Matrixes)

        len_parameters = max( len(Vertices), len(Matrixes) )
        cluster_subdivide = cluster_subdivide[: len_parameters]
        max_iter          = max_iter[:          len_parameters]
        cluster_counts    = cluster_counts[:    len_parameters]

        outputs = self.outputs
        if not any( [o.is_linked for o in outputs]):
            return
        
        res_verts = []
        res_edges = []
        res_faces = []
        res_polygon_centers = []
        res_polygon_normals = []
        for cluster_subdivide_i, max_iter_i, cluster_counts_i, verts_i, edges_i, faces_i, matrix_i in zip_long_repeat(cluster_subdivide, max_iter, cluster_counts, Vertices, Edges, Faces, Matrixes):
            if cluster_subdivide_i<0:
                cluster_subdivide_i=0
            if max_iter_i<0:
                max_iter_i=0
            if cluster_counts_i<4:
                cluster_counts_i=4

            if( max(map(len, faces_i))!=min(map(len, faces_i))):
                bm_I = bmesh_from_pydata(verts_i, edges_i, faces_i, markup_face_data=True, normal_update=True)
                b_faces = []
                for face in bm_I.faces:
                    b_faces.append(face)
                res = bmesh.ops.triangulate( bm_I, faces=b_faces, quad_method=self.quad_mode, ngon_method=self.ngon_mode )
                new_vertices_I, new_edges_I, new_faces_I = pydata_from_bmesh(bm_I, ret_edges=False)
                bm_I.free()
                pdmesh = PolyData.from_regular_faces( new_vertices_I, new_faces_I) # https://docs.pyvista.org/version/stable/api/core/_autosummary/pyvista.PolyData.from_regular_faces.html#pyvista-polydata-from-regular-faces
            else:
                pdmesh = PolyData.from_regular_faces( verts_i, faces_i) # https://docs.pyvista.org/version/stable/api/core/_autosummary/pyvista.PolyData.from_regular_faces.html#pyvista-polydata-from-regular-faces

            if pdmesh.is_all_triangles==False:
                pdmesh.triangulate(inplace=True) # https://docs.pyvista.org/version/stable/api/core/_autosummary/pyvista.polydatafilters.triangulate

            if(cluster_subdivide_i>0):
                pdmesh.subdivide(cluster_subdivide_i, self.subdiv_mode, inplace=True) # loop, butterfly, linear, https://docs.pyvista.org/version/stable/api/core/_autosummary/pyvista.polydatafilters.subdivide
                pdmesh.clean(inplace=True)  # after pdmesh subdiv all vertces and faces are disconnected. This operation merge them.

            clust = pyacvd.Clustering(pdmesh)
            # !!! do not use pyacvd subdiv. It has only linear mode
            # if(cluster_subdivide_i>0):
            #     clust.subdivide(cluster_subdivide_i)
            
            clust.cluster(cluster_counts_i, maxiter=max_iter_i)
            remesh = clust.create_mesh()
            if not matrix_i == Matrix():
                np_matrix_i = np.asarray(matrix_i)
                remesh.transform(np_matrix_i, transform_all_input_vectors=True, inplace=True)

            remesh_edges = np.reshape(remesh.extract_all_edges(use_all_points=True).lines, (-1,3))[:,[1,2]]  # https://docs.pyvista.org/version/stable/api/core/_autosummary/pyvista.CompositeFilters.extract_all_edges.html#pyvista.CompositeFilters.extract_all_edges

            if self.output_as_numpy:
                res_verts.append( np.array(remesh.points) )
                res_edges.append( np.array(remesh_edges, int) )
                res_faces.append( np.array(remesh.regular_faces, int) )
                if outputs['polygon_normals'].is_linked:
                    res_polygon_normals.append( np.array(remesh.face_normals) )
                if outputs['polygon_centers'].is_linked:
                    res_polygon_centers.append( np.array(remesh.cell_centers().points) )
            else:
                res_verts.append(remesh.points.tolist())
                res_edges.append(remesh_edges.tolist())
                res_faces.append(remesh.regular_faces.tolist())
                if outputs['polygon_normals'].is_linked:
                    res_polygon_normals.append( remesh.face_normals.tolist() )
                if outputs['polygon_centers'].is_linked:
                    res_polygon_centers.append( remesh.cell_centers().points.tolist() )

        outputs['vertices'].sv_set(res_verts)
        outputs['edges'].sv_set(res_edges)
        outputs['polygons'].sv_set(res_faces)
        outputs['polygon_normals'].sv_set(res_polygon_normals)
        outputs['polygon_centers'].sv_set(res_polygon_centers)

def register():
    bpy.utils.register_class(SvMeshClusteringNode)


def unregister():
    bpy.utils.unregister_class(SvMeshClusteringNode)
