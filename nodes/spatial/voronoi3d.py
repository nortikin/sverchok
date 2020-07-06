
from collections import defaultdict

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

        @throttled
        def update_sockets(self, context):
            self.inputs['Clipping'].hide_safe = not self.do_clip

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

            for site_idx in faces_per_site.keys():
                if self.closed_only and site_idx in open_sites:
                    continue
                done_verts = dict()
                bm = bmesh.new()
                for face in faces_per_site[site_idx]:
                    face_bm_verts = []
                    for vertex_idx in face:
                        if vertex_idx not in done_verts:
                            bm_vert = bm.verts.new(diagram.vertices[vertex_idx])
                            done_verts[vertex_idx] = bm_vert
                        else:
                            bm_vert = done_verts[vertex_idx]
                        face_bm_verts.append(bm_vert)
                    bm.faces.new(face_bm_verts)
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
                face_bm_verts = []
                for vertex_idx in face:
                    vertex = vertices[vertex_idx]
                    bm_vert = bm.verts.new(vertex)
                    face_bm_verts.append(bm_vert)
                bm.faces.new(face_bm_verts)
                bm.verts.index_update()
                bm.verts.ensure_lookup_table()
                bm.faces.index_update()
                bm.edges.index_update()
                ridge_verts, ridge_edges, ridge_faces = pydata_from_bmesh(bm)
                result_verts.append(ridge_verts)
                result_edges.append(ridge_edges)
                result_faces.append(ridge_faces)
            return result_verts, result_edges, result_faces

        def bisect(self, bm, point, normal, fill):
            bm.normal_update()
            geom_in = bm.verts[:] + bm.edges[:] + bm.faces[:]
            res = bmesh.ops.bisect_plane(
                bm, geom=geom_in, dist=0.00001,
                plane_co=point, plane_no=normal, use_snap_center=False,
                clear_outer=True, clear_inner=False)
            if fill:
                fres = bmesh.ops.edgenet_prepare(
                    bm, edges=[e for e in res['geom_cut'] if isinstance(e, bmesh.types.BMEdge)]
                )
                bmesh.ops.edgeloop_fill(bm, edges=fres['edges'])
            bm.verts.index_update()
            bm.edges.index_update()
            bm.faces.index_update()

        def calc_bounds(self, vertices, clipping):
            x_min = min(v[0] for v in vertices)
            y_min = min(v[1] for v in vertices)
            z_min = min(v[2] for v in vertices)
            x_max = max(v[0] for v in vertices)
            y_max = max(v[1] for v in vertices)
            z_max = max(v[2] for v in vertices)
            return (x_min - clipping, x_max + clipping,
                    y_min - clipping, y_max + clipping,
                    z_min - clipping, z_max + clipping)

        def clip_bmesh(self, bm, bounds, fill):
            x_min, x_max, y_min, y_max, z_min, z_max = bounds

            self.bisect(bm, (x_min, 0, 0), (-1, 0, 0), fill)
            self.bisect(bm, (x_max, 0, 0), (1, 0, 0), fill)
            self.bisect(bm, (0, y_min, 0), (0, -1, 0), fill)
            self.bisect(bm, (0, y_max, 0), (0, 1, 0), fill)
            self.bisect(bm, (0, 0, z_min), (0, 0, -1), fill)
            self.bisect(bm, (0, 0, z_max), (0, 0, 1), fill)

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
                self.clip_bmesh(bm, bounds, fill)
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
                    bounds = self.calc_bounds(sites, clipping)

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

