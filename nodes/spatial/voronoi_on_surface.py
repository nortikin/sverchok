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

import numpy as np
from collections import defaultdict

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
import bmesh
from mathutils import Vector

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, throttle_and_update_node, ensure_nesting_level
from sverchok.utils.surface.core import SvSurface
from sverchok.utils.voronoi import voronoi_bounded
from sverchok.utils.logging import debug, info
from sverchok.utils.sv_mesh_utils import mask_vertices, polygons_to_edges
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata, pydata_from_bmesh, bmesh_clip
from sverchok.utils.geom import calc_bounds
from sverchok.dependencies import scipy

if scipy is not None:
    from scipy.spatial import Voronoi

class SvVoronoiOnSurfaceNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Voronoi Surface
    Tooltip: Generate Voronoi diagram on a Surface
    """
    bl_idname = 'SvVoronoiOnSurfaceNode'
    bl_label = 'Voronoi on Surface'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_VORONOI'

    def get_modes(self, context):
        modes = [('UV', "UV Space", "Generate 2D Voronoi diagram in surface's UV space", 0)]
        if scipy is not None:
            modes.append(('RIDGES', "3D Ridges", "Generate ridges of 3D Voronoi diagram", 1))
            modes.append(('REGIONS', "3D Regions", "Generate regions of 3D Voronoi diagram", 2))
        return modes
    
    @throttle_and_update_node
    def update_sockets(self, context):
        self.inputs['MaxSides'].hide_safe = self.mode != 'UV' or not self.make_faces
        self.inputs['Thickness'].hide_safe = self.mode == 'UV'
        self.inputs['Clipping'].hide_safe = self.mode == 'UV' or not self.do_clip
        self.outputs['UVVertices'].hide_safe = self.mode != 'UV'
        self.outputs['Faces'].hide_safe = self.mode == 'UV' and not self.make_faces

    mode : EnumProperty(
        name = "Mode",
        items = get_modes,
        update = update_sockets)

    make_faces: BoolProperty(
        name = "Make faces",
        description = "Use `fill holes` function to make Voronoi polygons",
        default = False,
        update = update_sockets)

    ordered_faces : BoolProperty(
        name = "Ordered faces",
        description = "Make sure that faces are generated in the same order as corresponding input vertices",
        default = False,
        update = updateNode)

    max_sides: IntProperty(
        name='Sides',
        description='Maximum number of polygon sides',
        default=10,
        min=3,
        update=updateNode)

    thickness : FloatProperty(
        name = "Thickness",
        default = 1.0,
        min = 0.0,
        update=updateNode)

    normals : BoolProperty(
        name = "Correct normals",
        default = True,
        update = updateNode)

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
        self.inputs.new('SvSurfaceSocket', 'Surface')
        self.inputs.new('SvVerticesSocket', "UVPoints")
        self.inputs.new('SvStringsSocket', 'MaxSides').prop_name = 'max_sides'
        self.inputs.new('SvStringsSocket', 'Thickness').prop_name = 'thickness'
        self.inputs.new('SvStringsSocket', "Clipping").prop_name = 'clipping'
        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket', "Edges")
        self.outputs.new('SvStringsSocket', "Faces")
        self.outputs.new('SvVerticesSocket', "UVVertices")
        self.update_sockets(context)

    def draw_buttons(self, context, layout):
        layout.prop(self, "mode")
        if self.mode == 'UV':
            layout.prop(self, "make_faces")
        if self.mode in {'RIDGES', 'REGIONS'} or self.make_faces:
            layout.prop(self, 'do_clip')
            layout.prop(self, 'normals')

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        if self.make_faces:
            layout.prop(self, 'ordered_faces')

    def voronoi_uv(self, surface, uvpoints, maxsides):
        u_min, u_max, v_min, v_max = surface.get_domain()
        u_mid = 0.5*(u_min + u_max)
        v_mid = 0.5*(v_min + v_max)

#         def invert_points(pts):
#             result = []
#             for pt in pts:
#                 u,v,_ = pt
#                 if u_min <= u <= u_max and v_min <= v <= v_max:
#                     if u > u_mid:
#                         u1 = u_max
#                     else:
#                         u1 = u_min
#                     if v > v_mid:
#                         v1 = v_max
#                     else:
#                         v1 = v_min
#                     u2 = u + 2*(u1 - u)
#                     v2 = v + 2*(v1 - v)
#                     result.append((u2, v2, 0))
#             return result

        n = len(uvpoints)
        clip = ((u_max - u_min) + (v_max - v_min)) / 4.0
        #all_sites = uvpoints + invert_points(uvpoints)
        #print(uvpoints)
        uv_verts, edges, faces = voronoi_bounded(uvpoints,
                    bound_mode='BOX',
                    clip=clip,
                    draw_bounds = False,
                    draw_hangs = False,
                    make_faces = self.make_faces,
                    ordered_faces = self.ordered_faces,
                    max_sides = maxsides)
        #print(uv_verts)
        us = np.array([p[0] for p in uv_verts])
        vs = np.array([p[1] for p in uv_verts])
        u_mask = np.logical_and(us >= u_min, us <= u_max)
        v_mask = np.logical_and(vs >= v_min, vs <= v_max)
        mask = np.logical_and(u_mask, v_mask).tolist()

        uv_verts, edges, faces = mask_vertices(uv_verts, edges, faces, mask)
        us = np.array([p[0] for p in uv_verts])
        vs = np.array([p[1] for p in uv_verts])
        verts = surface.evaluate_array(us, vs).tolist()

        return uv_verts, verts, edges, faces

    def voronoi_3d(self, surface, uvpoints, thickness, clipping, make_regions):
        npoints = len(uvpoints)
        u_min, u_max, v_min, v_max = surface.get_domain()
        u_mid = 0.5*(u_min + u_max)
        v_mid = 0.5*(v_min + v_max)

        us = np.array([p[0] for p in uvpoints])
        vs = np.array([p[1] for p in uvpoints])

        us_edge = np.empty(us.shape)
        us_edge[us > u_mid] = u_max
        us_edge[us <= u_mid] = u_min

        vs_edge = np.empty(vs.shape)
        vs_edge[vs > v_mid] = v_max
        vs_edge[vs <= v_mid] = v_min

        surface_points = surface.evaluate_array(us, vs)
        edge_points = surface.evaluate_array(us_edge, vs_edge)
        out_points = surface_points + 2*(edge_points - surface_points)

        normals = surface.normal_array(us, vs)
        k = 0.5*thickness
        plus_points = surface_points + k*normals
        minus_points = surface_points - k*normals
        all_points = surface_points.tolist() + out_points.tolist() + plus_points.tolist() + minus_points.tolist()
        diagram = Voronoi(all_points)
        
        region_verts = dict()
        region_verts_map = dict()
        for site_idx in range(npoints):
            region_idx = diagram.point_region[site_idx]
            region = diagram.regions[region_idx]
            vertices = [tuple(diagram.vertices[i,:]) for i in region]
            region_verts[site_idx] = vertices
            region_verts_map[site_idx] = {vert_idx: i for i, vert_idx in enumerate(region)}
        
        open_sites = set()
        region_faces = defaultdict(list)
        for ridge_idx, sites in enumerate(diagram.ridge_points):
            site_from, site_to = sites
#             if site_from < 0 or site_to < 0:
#                 print(ridge_idx, site_from, site_to)
            ridge = diagram.ridge_vertices[ridge_idx]
            if -1 in ridge:
                open_sites.add(site_from)
                open_sites.add(site_to)
            
            if make_regions:
                if site_from < npoints:
                    face_from = [region_verts_map[site_from][i] for i in ridge]
                    region_faces[site_from].append(face_from)
               
                if site_to < npoints:
                    face_to = [region_verts_map[site_to][i] for i in ridge]
                    region_faces[site_to].append(face_to)
            else:
                if site_from < npoints and site_to < npoints:
                    face_from = [region_verts_map[site_from][i] for i in ridge]
                    region_faces[site_from].append(face_from)
                    face_to = [region_verts_map[site_to][i] for i in ridge]
                    region_faces[site_to].append(face_to)
        
        verts = [region_verts[i] for i in range(npoints) if i not in open_sites]
        faces = [region_faces[i] for i in range(npoints) if i not in open_sites]

        empty_faces = [len(f) == 0 for f in faces]
        verts = [vs for vs, mask in zip(verts, empty_faces) if not mask]
        faces = [fs for fs, mask in zip(faces, empty_faces) if not mask]
        edges = polygons_to_edges(faces, True)

        if not make_regions:
            verts_n, edges_n, faces_n = [], [], []
            for verts_i, edges_i, faces_i in zip(verts, edges, faces):
                used_verts = set(sum(faces_i, []))
                mask = [i in used_verts for i in range(len(verts_i))]
                verts_i, edges_i, faces_i = mask_vertices(verts_i, edges_i, faces_i, mask)
                verts_n.append(verts_i)
                edges_n.append(edges_i)
                faces_n.append(faces_i)
            verts, edges, faces = verts_n, edges_n, faces_n

        if self.do_clip:
            verts_n, edges_n, faces_n = [], [], []
            bounds = calc_bounds(surface_points.tolist(), clipping)
            for verts_i, edges_i, faces_i in zip(verts, edges, faces):
                print(bounds)
                bm = bmesh_from_pydata(verts_i, edges_i, faces_i)
                bmesh_clip(bm, bounds, fill=True)
                verts_i, edges_i, faces_i = pydata_from_bmesh(bm)
                bm.free()
                verts_n.append(verts_i)
                edges_n.append(edges_i)
                faces_n.append(faces_i)
            verts, edges, faces = verts_n, edges_n, faces_n

        return verts, edges, faces

    def recalc_normals(self, verts, edges, faces, loop=False):
        if loop:
            verts_out, edges_out, faces_out = [], [], []
            for vs, es, fs in zip_long_repeat(verts, edges, faces):
                vs, es, fs = self.recalc_normals(vs, es, fs, loop=False)
                verts_out.append(vs)
                edges_out.append(es)
                faces_out.append(fs)
            return verts_out, edges_out, faces_out
        else:
            bm = bmesh_from_pydata(verts, edges, faces)
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
            verts, edges, faces = pydata_from_bmesh(bm)
            bm.free()
            return verts, edges, faces

    def process(self):

        if not any(socket.is_linked for socket in self.outputs):
            return

        surface_in = self.inputs['Surface'].sv_get()
        uvpoints_in = self.inputs['UVPoints'].sv_get()
        maxsides_in = self.inputs['MaxSides'].sv_get()
        thickness_in = self.inputs['Thickness'].sv_get()
        clipping_in = self.inputs['Clipping'].sv_get()

        surface_in = ensure_nesting_level(surface_in, 2, data_types=(SvSurface,))
        uvpoints_in = ensure_nesting_level(uvpoints_in, 4)
        maxsides_in = ensure_nesting_level(maxsides_in, 2)
        thickness_in = ensure_nesting_level(thickness_in, 2)
        clipping_in = ensure_nesting_level(clipping_in, 2)

        verts_out = []
        edges_out = []
        faces_out = []
        uvverts_out = []
        for params in zip_long_repeat(surface_in, uvpoints_in, maxsides_in, thickness_in, clipping_in):
            new_verts = []
            new_edges = []
            new_faces = []
            new_uvverts = []
            for surface, uvpoints, maxsides, thickness, clipping in zip_long_repeat(*params):
                if self.mode == 'UV':
                    uvverts, verts, edges, faces = self.voronoi_uv(surface, uvpoints, maxsides)
                    new_uvverts.append(uvverts)
                else:
                    verts, edges, faces = self.voronoi_3d(surface, uvpoints, thickness, clipping, self.mode == 'REGIONS')

                if (self.mode in {'RIDGES', 'REGIONS'} or self.make_faces) and self.normals:
                    verts, edges, faces = self.recalc_normals(verts, edges, faces, loop = (self.mode in {'REGIONS', 'RIDGES'}))

                new_verts.append(verts)
                new_edges.append(edges)
                new_faces.append(faces)

            verts_out.append(new_verts)
            edges_out.append(new_edges)
            faces_out.append(new_faces)
            if self.mode == 'UV':
                uvverts_out.append(new_uvverts)

        self.outputs['Vertices'].sv_set(verts_out)
        self.outputs['Edges'].sv_set(edges_out)
        self.outputs['Faces'].sv_set(faces_out)
        self.outputs['UVVertices'].sv_set(uvverts_out)

def register():
    bpy.utils.register_class(SvVoronoiOnSurfaceNode)

def unregister():
    bpy.utils.unregister_class(SvVoronoiOnSurfaceNode)

