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
import bmesh
from mathutils import Vector

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, throttle_and_update_node, ensure_nesting_level, get_data_nesting_level
from sverchok.utils.sv_bmesh_utils import recalc_normals
from sverchok.utils.sv_mesh_utils import mesh_join
from sverchok.utils.voronoi3d import voronoi_on_mesh
from sverchok.utils.dummy_nodes import add_dummy
from sverchok.dependencies import scipy

if scipy is None:
    add_dummy('SvVoronoiOnMeshNode', "Voronoi on Mesh", 'scipy')

class SvVoronoiOnMeshNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Voronoi Mesh
    Tooltip: Generate Voronoi diagram on the surface of a mesh object
    """
    bl_idname = 'SvVoronoiOnMeshNode'
    bl_label = 'Voronoi on Mesh'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_VORONOI'

    modes = [
            ('VOLUME', "Split Volume", "Split volume of the mesh into regions of Voronoi diagram", 0),
            ('SURFACE', "Split Surface", "Split the surface of the mesh into regions of Vornoi diagram", 1),
            #('RIDGES', "Ridges near Surface", "Generate ridges of 3D Voronoi diagram near the surface of the mesh", 2),
            #('REGIONS', "Regions near Surface", "Generate regions of 3D Voronoi diagram near the surface of the mesh", 3)
        ]

#     thickness : FloatProperty(
#         name = "Thickness",
#         default = 1.0,
#         min = 0.0,
#         update=updateNode)

    spacing : FloatProperty(
        name = "Spacing",
        default = 0.0,
        min = 0.0,
        update=updateNode)

    normals : BoolProperty(
        name = "Correct normals",
        default = True,
        update = updateNode)

    @throttle_and_update_node
    def update_sockets(self, context):
        #self.inputs['Thickness'].hide_safe = self.mode not in {'RIDGES', 'REGIONS'}
        self.inputs['Spacing'].hide_safe = self.mode not in {'VOLUME', 'SURFACE'}

    mode : EnumProperty(
        name = "Mode",
        items = modes,
        default = 'VOLUME',
        update = update_sockets)
    
#     clip_inner : BoolProperty(
#         name = "Clip Inner",
#         default = True,
#         update = updateNode)
# 
#     clip_outer : BoolProperty(
#         name = "Clip Outer",
#         default = True,
#         update = updateNode)

    join_modes = [
            ('FLAT', "Flat list", "Output a single flat list of mesh objects (Voronoi diagram ridges / regions) for all input meshes", 0),
            ('SEPARATE', "Separate lists", "Output a separate list of mesh objects (Voronoi diagram ridges / regions) for each input mesh", 1),
            ('JOIN', "Join meshes", "Output one mesh, joined from ridges / edges of Voronoi diagram, for each input mesh", 2)
        ]

    join_mode : EnumProperty(
        name = "Output mode",
        items = join_modes,
        default = 'FLAT',
        update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Vertices')
        self.inputs.new('SvStringsSocket', 'Faces')
        self.inputs.new('SvVerticesSocket', "Sites")
#         self.inputs.new('SvStringsSocket', 'Thickness').prop_name = 'thickness'
        self.inputs.new('SvStringsSocket', 'Spacing').prop_name = 'spacing'
        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket', "Edges")
        self.outputs.new('SvStringsSocket', "Faces")
        self.update_sockets(context)

    def draw_buttons(self, context, layout):
        layout.label(text="Mode:")
        layout.prop(self, "mode", text='')
#         if self.mode in {'REGIONS', 'RIDGES'}:
#             row = layout.row(align=True)
#             row.prop(self, 'clip_inner', toggle=True)
#             row.prop(self, 'clip_outer', toggle=True)
        layout.prop(self, 'normals')
        layout.label(text='Output nesting:')
        layout.prop(self, 'join_mode', text='')

    def process(self):

        if not any(socket.is_linked for socket in self.outputs):
            return

        verts_in = self.inputs['Vertices'].sv_get()
        faces_in = self.inputs['Faces'].sv_get()
        sites_in = self.inputs['Sites'].sv_get()
        #thickness_in = self.inputs['Thickness'].sv_get()
        spacing_in = self.inputs['Spacing'].sv_get()

        verts_in = ensure_nesting_level(verts_in, 4)
        input_level = get_data_nesting_level(sites_in)
        sites_in = ensure_nesting_level(sites_in, 4)
        faces_in = ensure_nesting_level(faces_in, 4)
        #thickness_in = ensure_nesting_level(thickness_in, 2)
        spacing_in = ensure_nesting_level(spacing_in, 2)

        nested_output = input_level > 3

        verts_out = []
        edges_out = []
        faces_out = []
        for params in zip_long_repeat(verts_in, faces_in, sites_in, spacing_in):
            new_verts = []
            new_edges = []
            new_faces = []
            for verts, faces, sites, spacing in zip_long_repeat(*params):
                verts, edges, faces = voronoi_on_mesh(verts, faces, sites, thickness=0,
                            spacing = spacing,
                            #clip_inner = self.clip_inner, clip_outer = self.clip_outer,
                            do_clip=True, clipping=None,
                            mode = self.mode)
                if self.normals:
                    verts, edges, faces = recalc_normals(verts, edges, faces, loop=True)

                if self.join_mode == 'FLAT':
                    new_verts.extend(verts)
                    new_edges.extend(edges)
                    new_faces.extend(faces)
                elif self.join_mode == 'SEPARATE':
                    new_verts.append(verts)
                    new_edges.append(edges)
                    new_faces.append(faces)
                else: # JOIN
                    verts, edges, faces = mesh_join(verts, edges, faces)
                    new_verts.append(verts)
                    new_edges.append(edges)
                    new_faces.append(faces)

            if nested_output:
                verts_out.append(new_verts)
                edges_out.append(new_edges)
                faces_out.append(new_faces)
            else:
                verts_out.extend(new_verts)
                edges_out.extend(new_edges)
                faces_out.extend(new_faces)

        self.outputs['Vertices'].sv_set(verts_out)
        self.outputs['Edges'].sv_set(edges_out)
        self.outputs['Faces'].sv_set(faces_out)

def register():
    if scipy is not None:
        bpy.utils.register_class(SvVoronoiOnMeshNode)

def unregister():
    if scipy is not None:
        bpy.utils.unregister_class(SvVoronoiOnMeshNode)

