# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
from itertools import combinations

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
import bmesh
from mathutils import Matrix

import sverchok
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok.utils.sv_mesh_utils import polygons_to_edges, mesh_join
from sverchok.utils.sv_bmesh_utils import pydata_from_bmesh, bmesh_from_pydata
from sverchok.utils.logging import info, exception
from sverchok.utils.dummy_nodes import add_dummy
from sverchok.dependencies import scipy

if scipy is None:
    add_dummy('SvDelaunay3dMk2Node', "Delaunay 3D", 'scipy')
else:
    from scipy.spatial import Delaunay

class SvDelaunay3dMk2Node(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Delaunay 3D
    Tooltip: Generate 3D Delaunay Triangulation
    """
    bl_idname = 'SvDelaunay3dMk2Node'
    bl_label = 'Delaunay 3D'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_DELAUNAY'

    join : BoolProperty(
        name = "Join",
        default = False,
        update = updateNode)

    volume_threshold : FloatProperty(
        name = "PlanarThreshold",
        min = 0,
        default = 1e-4,
        precision = 4,
        update = updateNode)

    edge_threshold : FloatProperty(
        name = "EdgeThreshold",
        min = 0,
        default = 0,
        precision = 4,
        update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, "join")

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvStringsSocket', "PlanarThreshold").prop_name = 'volume_threshold'
        self.inputs.new('SvStringsSocket', "EdgeThreshold").prop_name = 'edge_threshold'
        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket', "Edges")
        self.outputs.new('SvStringsSocket', "Faces")

    def make_edges(self, idxs):
        return [(i, j) for i in idxs for j in idxs if i < j]

    def make_faces(self, idxs):
        return [(i, j, k) for i in idxs for j in idxs for k in idxs if i < j and j < k]

    def get_verts(self, verts, idxs):
        return [verts[i] for i in idxs]

    def is_planar(self, verts, idxs, threshold):
        if threshold == 0:
            return False
        a, b, c, d = [verts[i] for i in idxs]
        a, b, c, d = np.array(a), np.array(b), np.array(c), np.array(d)
        v1 = b - a
        v2 = c - a
        v3 = d - a
        v1 = v1 / np.linalg.norm(v1)
        v2 = v2 / np.linalg.norm(v2)
        v3 = v3 / np.linalg.norm(v3)
        volume = np.cross(v1, v2).dot(v3) / 6
        return abs(volume) < threshold
    
    def is_too_long(self, verts, idxs, threshold):
        if threshold == 0:
            return False
        verts = [np.array(verts[i]) for i in idxs]
        for v1, v2 in combinations(verts, 2):
            d = np.linalg.norm(v1 - v2)
            if d > threshold:
                return True
        return False

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        vertices_s = self.inputs['Vertices'].sv_get()
        volume_threshold_s = self.inputs['PlanarThreshold'].sv_get()
        edge_threshold_s = self.inputs['EdgeThreshold'].sv_get()

        input_level = get_data_nesting_level(vertices_s)

        vertices_s = ensure_nesting_level(vertices_s, 4)
        volume_threshold_s = ensure_nesting_level(volume_threshold_s, 2)
        edge_threshold_s = ensure_nesting_level(edge_threshold_s, 2)

        nested_output = input_level > 3

        verts_out = []
        edges_out = []
        faces_out = []
        for params in zip_long_repeat(vertices_s, volume_threshold_s, edge_threshold_s):
            verts_item = []
            edges_item = []
            faces_item = []
            for vertices, volume_threshold, edge_threshold in zip_long_repeat(*params):

                tri = Delaunay(np.array(vertices))
                if self.join:
                    verts_new = vertices
                    edges_new = set()
                    faces_new = set()
                    for simplex_idx, simplex in enumerate(tri.simplices):
                        if self.is_too_long(vertices, simplex, edge_threshold) or self.is_planar(vertices, simplex, volume_threshold):
                            continue
                        edges_new.update(set(self.make_edges(simplex)))
                        faces_new.update(set(self.make_faces(simplex)))
                    verts_item.append(verts_new)
                    edges_item.append(list(edges_new))
                    faces_item.append(list(faces_new))
                else:
                    verts_new = []
                    edges_new = []
                    faces_new = []
                    for simplex in tri.simplices:
                        if self.is_too_long(vertices, simplex, edge_threshold) or self.is_planar(vertices, simplex, volume_threshold):
                            continue
                        verts_simplex = self.get_verts(vertices, simplex)
                        edges_simplex = self.make_edges([0, 1, 2, 3])
                        faces_simplex = self.make_faces([0, 1, 2, 3])
                        verts_new.append(verts_simplex)
                        edges_new.append(edges_simplex)
                        faces_new.append(faces_simplex)
                    verts_item.extend(verts_new)
                    edges_item.extend(edges_new)
                    faces_item.extend(faces_new)

                if nested_output:
                    verts_out.append(verts_item)
                    edges_out.append(edges_item)
                    faces_out.append(faces_item)
                else:
                    verts_out.extend(verts_item)
                    edges_out.extend(edges_item)
                    faces_out.extend(faces_item)

        self.outputs['Vertices'].sv_set(verts_out)
        self.outputs['Edges'].sv_set(edges_out)
        self.outputs['Faces'].sv_set(faces_out)

def register():
    if scipy is not None:
        bpy.utils.register_class(SvDelaunay3dMk2Node)

def unregister():
    if scipy is not None:
        bpy.utils.unregister_class(SvDelaunay3dMk2Node)

