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
        description="Cluster subdivide. (min=0)", update=updateNode) # type: ignore
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
        # layout.row().prop(self, 'cluster_subdivide')
        # layout.row().prop(self, 'max_iter')
        # layout.row().prop(self, 'cluster_counts')

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

        pass

    def sv_init(self, context):
        son = self.outputs.new
        self.inputs.new('SvStringsSocket', "cluster_subdivide").prop_name = 'cluster_subdivide'
        self.inputs.new('SvStringsSocket', "max_iter").prop_name = 'max_iter'
        self.inputs.new('SvStringsSocket', "cluster_counts").prop_name = 'cluster_counts'
        self.inputs.new('SvVerticesSocket', 'Vertices')
        self.inputs.new('SvStringsSocket', 'Edges')
        self.inputs.new('SvStringsSocket', 'Faces')

        self.inputs["cluster_subdivide"].label = "Cluster Subdivide"
        self.inputs["max_iter"].label = "Max Iteration"
        self.inputs["cluster_counts"].label = "Cluster counts"

        son('SvVerticesSocket', 'Vertices')
        son('SvStringsSocket', 'Edges')
        son('SvStringsSocket', 'Faces')
        self.width = 210
        

        self.update_sockets(context)

    def process(self):
        inputs = self.inputs
        _cluster_subdivide = inputs["cluster_subdivide"].sv_get(default=[[0]], deepcopy=False)
        cluster_subdivide = flatten_data(_cluster_subdivide)
        _max_iter = inputs["max_iter"].sv_get(default=[[20]], deepcopy=False)
        max_iter = flatten_data(_max_iter)
        _cluster_counts = inputs["cluster_counts"].sv_get(default=[[1000]], deepcopy=False)
        cluster_counts = flatten_data(_cluster_counts)

        _Vertices = inputs["Vertices"].sv_get(default=[[]], deepcopy=False)
        Vertices  = ensure_nesting_level(_Vertices, 3)
        _Edges    = inputs["Edges"].sv_get(default=[[]], deepcopy=False)
        Edges     = ensure_nesting_level(_Edges, 3)
        _Faces    = inputs["Faces"].sv_get(default=[[]], deepcopy=False)
        Faces     = ensure_nesting_level(_Faces, 3)

        cluster_subdivide = cluster_subdivide[: len(Vertices)]
        max_iter          = max_iter[: len(Vertices)]
        cluster_counts    = cluster_counts[: len(Vertices)]

        outputs = self.outputs
        if not any( [o.is_linked for o in outputs]):
            return
        
        res_verts = []
        res_edges = []
        res_faces = []
        for cluster_subdivide_i, max_iter_i, cluster_counts_i, verts_i, edges_i, faces_i in zip_long_repeat(cluster_subdivide, max_iter, cluster_counts, Vertices, Edges, Faces):
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
                new_vertices_I, new_edges_I, new_faces_I = pydata_from_bmesh(bm_I)
                bm_I.free()
                pdmesh = PolyData.from_regular_faces( new_vertices_I, new_faces_I)
            else:
                pdmesh = PolyData.from_regular_faces( verts_i, faces_i)

            clust = pyacvd.Clustering(pdmesh)
            if(cluster_subdivide_i>0):
                clust.subdivide(cluster_subdivide_i)
            clust.cluster(cluster_counts_i, maxiter=max_iter_i)
            remesh = clust.create_mesh()
            # remesh is triangulated here
            edges0 = remesh.regular_faces[:,[0,1]]  # edges AB
            edges1 = remesh.regular_faces[:,[1,2]]  # edges BC
            edges2 = remesh.regular_faces[:,[2,0]]  # edges CA
            # stack
            remesh_edges = np.vstack((edges0, edges1, edges2))

            if self.output_as_numpy:
                res_verts.append(remesh.points)
                res_edges.append(remesh_edges)
                res_faces.append(remesh.regular_faces)
            else:
                res_verts.append(remesh.points.tolist())
                res_edges.append(remesh_edges.tolist())
                res_faces.append(remesh.regular_faces.tolist())

        outputs['Vertices'].sv_set(res_verts)
        outputs['Edges'].sv_set(res_edges)
        outputs['Faces'].sv_set(res_faces)

def register():
    bpy.utils.register_class(SvMeshClusteringNode)


def unregister():
    bpy.utils.unregister_class(SvMeshClusteringNode)
