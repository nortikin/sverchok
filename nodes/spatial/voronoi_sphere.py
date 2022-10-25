
import numpy as np

import bpy
from bpy.props import FloatProperty
import bmesh

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat
from sverchok.utils.math import project_to_sphere
from sverchok.utils.sv_bmesh_utils import pydata_from_bmesh, bmesh_from_pydata
from sverchok.dependencies import scipy

if scipy is not None:
    from scipy.spatial import SphericalVoronoi


class SvExVoronoiSphereNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Voronoi Sphere
    Tooltip: Generate Voronoi diagram on the surface of the sphere
    """
    bl_idname = 'SvExVoronoiSphereNode'
    bl_label = 'Voronoi Sphere'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_VORONOI'
    sv_dependencies = {'scipy'}

    radius: FloatProperty(name="Radius", default=1.0, min=0.0, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        d = self.inputs.new('SvVerticesSocket', "Center")
        d.use_prop = True
        d.default_property = (0.0, 0.0, 0.0)
        self.inputs.new('SvStringsSocket', "Radius").prop_name = "radius"

        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket', "Edges")
        self.outputs.new('SvStringsSocket', "Faces")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        vertices_s = self.inputs['Vertices'].sv_get()
        radius_s = self.inputs['Radius'].sv_get()
        center_s = self.inputs['Center'].sv_get()

        verts_out = []
        edges_out = []
        faces_out = []

        for sites, center, radius in zip_long_repeat(vertices_s, center_s, radius_s):
            if isinstance(radius, (list, tuple)):
                radius = radius[0]
            center = center[0]
            sites = np.array([project_to_sphere(center, radius, v) for v in sites])

            vor = SphericalVoronoi(sites, radius=radius, center=np.array(center))
            vor.sort_vertices_of_regions()

            new_verts = vor.vertices.tolist()
            new_faces = vor.regions
            #new_edges = polygons_to_edges([new_faces], True)[0]

            bm2 = bmesh_from_pydata(new_verts, [], new_faces, normal_update=True)
            bmesh.ops.recalc_face_normals(bm2, faces=bm2.faces)
            new_verts, new_edges, new_faces = pydata_from_bmesh(bm2)
            bm2.free()

            verts_out.append(new_verts)
            edges_out.append(new_edges)
            faces_out.append(new_faces)

        self.outputs['Vertices'].sv_set(verts_out)
        self.outputs['Edges'].sv_set(edges_out)
        self.outputs['Faces'].sv_set(faces_out)


def register():
    bpy.utils.register_class(SvExVoronoiSphereNode)


def unregister():
    bpy.utils.unregister_class(SvExVoronoiSphereNode)
