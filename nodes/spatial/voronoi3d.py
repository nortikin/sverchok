# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from collections import defaultdict

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty
import bmesh

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, get_data_nesting_level
from sverchok.utils.sv_mesh_utils import polygons_to_edges, mesh_join
from sverchok.utils.sv_bmesh_utils import pydata_from_bmesh, bmesh_from_pydata, bmesh_clip
from sverchok.utils.geom import calc_bounds
from sverchok.utils.dummy_nodes import add_dummy
from sverchok.dependencies import scipy

if scipy is None:
    add_dummy('SvExVoronoi3DNode', "Voronoi 3D", 'scipy')
else:
    from scipy.spatial import Voronoi

    class SvExVoronoi3DNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Voronoi 3D
        Tooltip: Generate 3D Voronoi diagram
        """
        bl_idname = 'SvExVoronoi3DNode'
        bl_label = 'Voronoi 3D'
        bl_icon = 'OUTLINER_OB_EMPTY'
        sv_icon = 'SV_VORONOI'

        out_modes = [
            ('RIDGES', "Ridges", "Ridges", 0),
            ('REGIONS', "Regions", "Regions", 1)
        ]

        out_mode : EnumProperty(
            name = "Output",
            items = out_modes,
            default = 'REGIONS',
            update = updateNode)

        join : BoolProperty(
            name = "Join",
            default = False,
            update = updateNode)

        closed_only : BoolProperty(
            name = "Closed regions only",
            default = True,
            update = updateNode)

        normals : BoolProperty(
            name = "Correct normals",
            default = True,
            update = updateNode)

        def update_sockets(self, context):
            self.inputs['Clipping'].hide_safe = not self.do_clip
            updateNode(self, context)

        do_clip : BoolProperty(
            name = "Clip",
            default = True,
            update = update_sockets)

        clipping : FloatProperty(
            name = "Clipping",
            default = 1.0,
            min = 0.0,
            update = updateNode)

        def sv_init(self, context):
            self.inputs.new('SvVerticesSocket', "Vertices")
            self.inputs.new('SvStringsSocket', "Clipping").prop_name = 'clipping'
            self.outputs.new('SvVerticesSocket', "Vertices")
            self.outputs.new('SvStringsSocket', "Edges")
            self.outputs.new('SvStringsSocket', "Faces")
            self.update_sockets(context)

        def draw_buttons(self, context, layout):
            layout.prop(self, "out_mode", expand=True)
            if self.out_mode == 'REGIONS':
                layout.prop(self, "closed_only")
                layout.prop(self, "normals")
            layout.prop(self, "do_clip")
            layout.prop(self, "join")

        def make_regions(self, diagram):
            faces_per_site = defaultdict(list)
            nsites = len(diagram.point_region)
            nridges = len(diagram.ridge_points)
            open_sites = set()
            for ridge_idx in range(nridges):
                site_idx_1, site_idx_2 = diagram.ridge_points[ridge_idx]
                face = diagram.ridge_vertices[ridge_idx]
                if -1 in face:
                    open_sites.add(site_idx_1)
                    open_sites.add(site_idx_2)
                    continue
                faces_per_site[site_idx_1].append(face)
                faces_per_site[site_idx_2].append(face)

            new_verts = []
            new_edges = []
            new_faces = []

            for site_idx in sorted(faces_per_site.keys()):
                if self.closed_only and site_idx in open_sites:
                    continue
                done_verts = dict()
                bm = bmesh.new()
                new_vert = bm.verts.new
                new_face = bm.faces.new
                for face in faces_per_site[site_idx]:
                    face_bm_verts = []
                    for vertex_idx in face:
                        if vertex_idx not in done_verts:
                            bm_vert = new_vert(diagram.vertices[vertex_idx])
                            done_verts[vertex_idx] = bm_vert
                        else:
                            bm_vert = done_verts[vertex_idx]
                        face_bm_verts.append(bm_vert)
                    new_face(face_bm_verts)
                bm.verts.index_update()
                bm.verts.ensure_lookup_table()
                bm.faces.index_update()
                bm.edges.index_update()

                if self.closed_only and any (v.is_boundary for v in bm.verts):
                    bm.free()
                    continue

                if self.normals:
                    bm.normal_update()
                    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])

                region_verts, region_edges, region_faces = pydata_from_bmesh(bm)
                bm.free()
                new_verts.append(region_verts)
                new_edges.append(region_edges)
                new_faces.append(region_faces)

            return new_verts, new_edges, new_faces

        def split_ridges(self, vertices, edges, faces):
            result_verts = []
            result_edges = []
            result_faces = []
            for face in faces:
                bm = bmesh.new()
                new_vert = bm.verts.new
                new_face = bm.faces.new
                face_bm_verts = []
                for vertex_idx in face:
                    vertex = vertices[vertex_idx]
                    bm_vert = new_vert(vertex)
                    face_bm_verts.append(bm_vert)
                new_face(face_bm_verts)
                bm.verts.index_update()
                bm.verts.ensure_lookup_table()
                bm.faces.index_update()
                bm.edges.index_update()
                ridge_verts, ridge_edges, ridge_faces = pydata_from_bmesh(bm)
                result_verts.append(ridge_verts)
                result_edges.append(ridge_edges)
                result_faces.append(ridge_faces)
            return result_verts, result_edges, result_faces

        def clip_mesh(self, bounds, vertices, edges, faces, fill=False, iterate=None):
            if iterate is None:
                iterate = get_data_nesting_level(vertices) > 2
            if iterate:
                vertices_result = []
                edges_result = []
                faces_result = []
                for vertices_item, edges_item, faces_item in zip(vertices, edges, faces):
                    new_vertices, new_edges, new_faces = self.clip_mesh(bounds, vertices_item, edges_item, faces_item, fill=fill, iterate=False)
                    if new_vertices:
                        vertices_result.append(new_vertices)
                        edges_result.append(new_edges)
                        faces_result.append(new_faces)
                return vertices_result, edges_result, faces_result
            else:
                bm = bmesh_from_pydata(vertices, edges, faces)
                bmesh_clip(bm, bounds, fill)
                vertices, edges, faces = pydata_from_bmesh(bm)
                bm.free()
                return vertices, edges, faces

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            vertices_s = self.inputs['Vertices'].sv_get()
            clipping_s = self.inputs['Clipping'].sv_get()

            verts_out = []
            edges_out = []
            faces_out = []
            for sites, clipping in zip_long_repeat(vertices_s, clipping_s):
                if isinstance(clipping, (list, tuple)):
                    clipping = clipping[0]

                diagram = Voronoi(sites)
                if self.do_clip:
                    bounds = calc_bounds(sites, clipping)

                if self.out_mode == 'RIDGES':
                    new_verts = diagram.vertices.tolist()
                    new_faces = [e for e in diagram.ridge_vertices if not -1 in e]
                    new_edges = polygons_to_edges([new_faces], True)[0]
                    if self.join:
                        if self.do_clip:
                            new_verts, new_edges, new_faces = self.clip_mesh(bounds, new_verts, new_edges, new_faces, fill=False)
                        verts_out.append(new_verts)
                        edges_out.append(new_edges)
                        faces_out.append(new_faces)
                    else:
                        new_verts, new_edges, new_faces = self.split_ridges(new_verts, new_edges, new_faces)
                        if self.do_clip:
                            new_verts, new_edges, new_faces = self.clip_mesh(bounds, new_verts, new_edges, new_faces, fill=False, iterate=True)
                        verts_out.extend(new_verts)
                        edges_out.extend(new_edges)
                        faces_out.extend(new_faces)
                else: # REGIONS
                    new_verts, new_edges, new_faces = self.make_regions(diagram)
                    if self.join:
                        new_verts, new_edges, new_faces = mesh_join(new_verts, new_edges, new_faces)
                        new_verts = [new_verts]
                        new_edges = [new_edges]
                        new_faces = [new_faces]
                    if self.do_clip:
                        new_verts, new_edges, new_faces = self.clip_mesh(bounds, new_verts, new_edges, new_faces, fill=True)
                    verts_out.extend(new_verts)
                    edges_out.extend(new_edges)
                    faces_out.extend(new_faces)

            self.outputs['Vertices'].sv_set(verts_out)
            self.outputs['Edges'].sv_set(edges_out)
            self.outputs['Faces'].sv_set(faces_out)

def register():
    if scipy is not None:
        bpy.utils.register_class(SvExVoronoi3DNode)

def unregister():
    if scipy is not None:
        bpy.utils.unregister_class(SvExVoronoi3DNode)
