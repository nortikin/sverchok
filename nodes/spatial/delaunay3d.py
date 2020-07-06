
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
import bmesh
from mathutils import Matrix

import sverchok
from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok.utils.sv_mesh_utils import polygons_to_edges, mesh_join
from sverchok.utils.sv_bmesh_utils import pydata_from_bmesh, bmesh_from_pydata
from sverchok.utils.logging import info, exception
from sverchok.dependencies import scipy

if scipy is not None:
    from scipy.spatial import Delaunay

    class SvExDelaunay3DNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Delaunay 3D
        Tooltip: Generate 3D Delaunay Triangulation
        """
        bl_idname = 'SvExDelaunay3DNode'
        bl_label = 'Delaunay 3D'
        bl_icon = 'OUTLINER_OB_EMPTY'
        sv_icon = 'SV_VORONOI'

        join : BoolProperty(
            name = "Join",
            default = False,
            update = updateNode)

        threshold : FloatProperty(
            name = "Threshold",
            default = 1e-4,
            precision = 4,
            update = updateNode)

        def draw_buttons(self, context, layout):
            layout.prop(self, "join", toggle=True)

        def sv_init(self, context):
            self.inputs.new('SvVerticesSocket', "Vertices")
            self.inputs.new('SvStringsSocket', "Threshold").prop_name = 'threshold'
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

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            vertices_s = self.inputs['Vertices'].sv_get()
            threshold_s = self.inputs['Threshold'].sv_get()

            verts_out = []
            edges_out = []
            faces_out = []
            for vertices, threshold in zip_long_repeat(vertices_s, threshold_s):
                if isinstance(threshold, (list, tuple)):
                    threshold = threshold[0]

                tri = Delaunay(np.array(vertices))
                if self.join:
                    verts_new = vertices
                    edges_new = set()
                    faces_new = set()
                    for simplex in tri.simplices:
                        if self.is_planar(vertices, simplex, threshold):
                            continue
                        edges_new.update(set(self.make_edges(simplex)))
                        faces_new.update(set(self.make_faces(simplex)))
                    verts_out.append(verts_new)
                    edges_out.append(list(edges_new))
                    faces_out.append(list(faces_new))
                else:
                    verts_new = []
                    edges_new = []
                    faces_new = []
                    for simplex in tri.simplices:
                        if self.is_planar(vertices, simplex, threshold):
                            continue
                        verts_simplex = self.get_verts(vertices, simplex)
                        edges_simplex = self.make_edges([0, 1, 2, 3])
                        faces_simplex = self.make_faces([0, 1, 2, 3])
                        verts_new.append(verts_simplex)
                        edges_new.append(edges_simplex)
                        faces_new.append(faces_simplex)
                    verts_out.extend(verts_new)
                    edges_out.extend(edges_new)
                    faces_out.extend(faces_new)

            self.outputs['Vertices'].sv_set(verts_out)
            self.outputs['Edges'].sv_set(edges_out)
            self.outputs['Faces'].sv_set(faces_out)

def register():
    if scipy is not None:
        bpy.utils.register_class(SvExDelaunay3DNode)

def unregister():
    if scipy is not None:
        bpy.utils.unregister_class(SvExDelaunay3DNode)

