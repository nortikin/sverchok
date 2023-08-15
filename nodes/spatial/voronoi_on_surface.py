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

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok.utils.surface.core import SvSurface
from sverchok.utils.voronoi import voronoi_bounded
from sverchok.utils.sv_mesh_utils import mask_vertices
from sverchok.utils.sv_bmesh_utils import recalc_normals
from sverchok.utils.voronoi3d import voronoi_on_surface
from sverchok.dependencies import scipy

class SvVoronoiOnSurfaceNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Voronoi Surface
    Tooltip: Generate Voronoi diagram on a Surface
    """
    bl_idname = 'SvVoronoiOnSurfaceNode'
    bl_label = 'Voronoi on Surface'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_VORONOI'

    modes = [('UV', "UV Space", "Generate 2D Voronoi diagram in surface's UV space", 0)]
    if scipy is not None:
        modes.append(('RIDGES', "3D Ridges", "Generate ridges of 3D Voronoi diagram", 1))
        modes.append(('REGIONS', "3D Regions", "Generate regions of 3D Voronoi diagram", 2))

    def update_sockets(self, context):
        self.inputs['MaxSides'].hide_safe = self.mode != 'UV' or not self.make_faces
        self.inputs['Thickness'].hide_safe = self.mode == 'UV'
        self.inputs['Clipping'].hide_safe = self.mode == 'UV' or not self.do_clip
        self.outputs['UVVertices'].hide_safe = self.mode != 'UV'
        self.outputs['Faces'].hide_safe = self.mode == 'UV' and not self.make_faces
        updateNode(self, context)

    mode : EnumProperty(
        name = "Mode",
        items=modes,
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
        description="Thickness of Voronoi diagram objects",
        update=updateNode)

    normals : BoolProperty(
        name = "Correct normals",
        default = True,
        description="Recalculate the normals of generated objects so that they all point outwards",
        update = updateNode)

    do_clip : BoolProperty(
        name = "Clip",
        default = True,
        description="Cut the generated diagram by clipping planes. If not checked, then this node can potentially generate very large objects near edges of the surface",
        update = update_sockets)

    clipping : FloatProperty(
        name = "Clipping",
        default = 1.0,
        min = 0.0,
        description="The distance from outermost sites to the clipping planes",
        update = updateNode)

    flat_output : BoolProperty(
        name = "Flat output",
        default = True,
        description="If checked, the node will generate one flat list of objects for all sets of input parameters. Otherwise, a separate list of objects will be generated for each set of input parameter values",
        update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvSurfaceSocket', 'Surface')
        self.inputs.new('SvVerticesSocket', "UVPoints").enable_input_link_menu = False
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
        if self.mode in {'RIDGES', 'REGIONS'}:
            layout.prop(self, 'flat_output')
            layout.prop(self, 'do_clip')
        if self.mode in {'RIDGES', 'REGIONS'} or self.make_faces:
            layout.prop(self, 'normals')

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        if self.mode == 'UV' and self.make_faces:
            layout.prop(self, 'ordered_faces')

    def voronoi_uv(self, surface, uvpoints, maxsides):
        u_min, u_max, v_min, v_max = surface.get_domain()
        u_mid = 0.5*(u_min + u_max)
        v_mid = 0.5*(v_min + v_max)

        def invert_points(pts):
            result = []
            for pt in pts:
                u,v,_ = pt
                if u_min <= u <= u_max and v_min <= v <= v_max:
                    if u > u_mid:
                        u1 = u_max
                    else:
                        u1 = u_min
                    if v > v_mid:
                        v1 = v_max
                    else:
                        v1 = v_min
                    u2 = u + 2*(u1 - u)
                    v2 = v + 2*(v1 - v)
                    result.append((u2, v2, 0))
            return result

        n = len(uvpoints)
        clip = ((u_max - u_min) + (v_max - v_min)) / 4.0
        all_sites = uvpoints + invert_points(uvpoints)
        uv_verts, edges, faces = voronoi_bounded(all_sites,
                    bound_mode='BOX',
                    clip=clip,
                    draw_bounds = True,
                    draw_hangs = True,
                    make_faces = self.make_faces,
                    ordered_faces = self.ordered_faces,
                    max_sides = maxsides)
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

    def process(self):

        if not any(socket.is_linked for socket in self.outputs):
            return

        surface_in = self.inputs['Surface'].sv_get()
        uvpoints_in = self.inputs['UVPoints'].sv_get()
        maxsides_in = self.inputs['MaxSides'].sv_get()
        thickness_in = self.inputs['Thickness'].sv_get()
        clipping_in = self.inputs['Clipping'].sv_get()

        surface_in = ensure_nesting_level(surface_in, 2, data_types=(SvSurface,))
        input_level = get_data_nesting_level(uvpoints_in)
        uvpoints_in = ensure_nesting_level(uvpoints_in, 4)
        maxsides_in = ensure_nesting_level(maxsides_in, 2)
        thickness_in = ensure_nesting_level(thickness_in, 2)
        clipping_in = ensure_nesting_level(clipping_in, 2)

        nested_output = input_level > 3

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
                    verts, edges, faces, used_sites = voronoi_on_surface(surface, uvpoints, thickness, self.do_clip, clipping, self.mode == 'REGIONS')

                if (self.mode in {'RIDGES', 'REGIONS'} or self.make_faces) and self.normals:
                    verts, edges, faces = recalc_normals(verts, edges, faces, loop = (self.mode in {'REGIONS', 'RIDGES'}))

                new_verts.append(verts)
                new_edges.append(edges)
                new_faces.append(faces)

            if self.mode in {'RIDGES', 'REGIONS'} and self.flat_output:
                new_verts = sum(new_verts, [])
                new_edges = sum(new_edges, [])
                new_faces = sum(new_faces, [])

            if nested_output:
                verts_out.append(new_verts)
                edges_out.append(new_edges)
                faces_out.append(new_faces)
                if self.mode == 'UV':
                    uvverts_out.append(new_uvverts)
            else:
                verts_out.extend(new_verts)
                edges_out.extend(new_edges)
                faces_out.extend(new_faces)
                if self.mode == 'UV':
                    uvverts_out.extend(new_uvverts)

        self.outputs['Vertices'].sv_set(verts_out)
        self.outputs['Edges'].sv_set(edges_out)
        self.outputs['Faces'].sv_set(faces_out)
        self.outputs['UVVertices'].sv_set(uvverts_out)

def register():
    bpy.utils.register_class(SvVoronoiOnSurfaceNode)

def unregister():
    bpy.utils.unregister_class(SvVoronoiOnSurfaceNode)

