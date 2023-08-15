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

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level,\
    ensure_min_nesting
from sverchok.utils.sv_bmesh_utils import recalc_normals
from sverchok.utils.sv_mesh_utils import mesh_join
from sverchok.utils.voronoi3d import voronoi_on_mesh


class SvVoronoiOnMeshNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Voronoi Mesh
    Tooltip: Generate Voronoi diagram on the surface of a mesh object
    """
    bl_idname = 'SvVoronoiOnMeshNode'
    bl_label = 'Voronoi on Mesh'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_VORONOI'
    sv_dependencies = {'scipy'}

    modes = [
            ('VOLUME', "Split Volume", "Split volume of the mesh into regions of Voronoi diagram", 0),
            ('SURFACE', "Split Surface", "Split the surface of the mesh into regions of Vornoi diagram", 1),
            #('RIDGES', "Ridges near Surface", "Generate ridges of 3D Voronoi diagram near the surface of the mesh", 2),
            #('REGIONS', "Regions near Surface", "Generate regions of 3D Voronoi diagram near the surface of the mesh", 3)
        ]

    spacing : FloatProperty(
        name = "Spacing",
        default = 0.0,
        min = 0.0,
        description="Percent of space to leave between generated fragment meshes",
        update=updateNode)

    normals : BoolProperty(
        name = "Correct normals",
        default = True,
        description="Make sure that all normals of generated meshes point outside",
        update = updateNode)

    def update_sockets(self, context):
        self.inputs['Spacing'].hide_safe = self.mode not in {'VOLUME', 'SURFACE'}
        updateNode(self, context)

    mode : EnumProperty(
        name = "Mode",
        items = modes,
        default = 'VOLUME',
        update = update_sockets)
    
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

    accuracy : IntProperty(
            name = "Accuracy",
            description = "Accuracy for mesh bisecting procedure",
            default = 6,
            min = 1,
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
        #self.outputs.new('SvVerticesSocket', "AllSites")
        self.update_sockets(context)

    def draw_buttons(self, context, layout):
        layout.label(text="Mode:")
        layout.prop(self, "mode", text='')
        if self.mode == 'VOLUME':
            layout.prop(self, 'normals')
        layout.label(text='Output nesting:')
        layout.prop(self, 'join_mode', text='')

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, 'accuracy')

    def process(self):

        if not any(socket.is_linked for socket in self.outputs):
            return

        verts_in = self.inputs['Vertices'].sv_get(deepcopy=False)
        faces_in = self.inputs['Faces'].sv_get(deepcopy=False)
        sites_in = self.inputs['Sites'].sv_get(deepcopy=False)
        #thickness_in = self.inputs['Thickness'].sv_get()
        spacing_in = self.inputs['Spacing'].sv_get(deepcopy=False)

        verts_in = ensure_nesting_level(verts_in, 4)
        input_level = get_data_nesting_level(sites_in)
        sites_in = ensure_nesting_level(sites_in, 4)
        faces_in = ensure_nesting_level(faces_in, 4)
        #thickness_in = ensure_nesting_level(thickness_in, 2)
        spacing_in = ensure_min_nesting(spacing_in, 2)

        nested_output = input_level > 3

        precision = 10 ** (-self.accuracy)

        verts_out = []
        edges_out = []
        faces_out = []
        sites_out = []
        for params in zip_long_repeat(verts_in, faces_in, sites_in, spacing_in):
            new_verts = []
            new_edges = []
            new_faces = []
            new_sites = []
            for verts, faces, sites, spacing in zip_long_repeat(*params):
                verts, edges, faces, sites = voronoi_on_mesh(verts, faces, sites, thickness=0,
                            spacing = spacing,
                            #clip_inner = self.clip_inner, clip_outer = self.clip_outer,
                            do_clip=True, clipping=None,
                            mode = self.mode,
                            normal_update = self.normals,
                            precision = precision)

                if self.join_mode == 'FLAT':
                    new_verts.extend(verts)
                    new_edges.extend(edges)
                    new_faces.extend(faces)
                    new_sites.extend(sites)
                elif self.join_mode == 'SEPARATE':
                    new_verts.append(verts)
                    new_edges.append(edges)
                    new_faces.append(faces)
                    new_sites.append(sites)
                else: # JOIN
                    verts, edges, faces = mesh_join(verts, edges, faces)
                    new_verts.append(verts)
                    new_edges.append(edges)
                    new_faces.append(faces)
                    new_sites.append(sites)

            if nested_output:
                verts_out.append(new_verts)
                edges_out.append(new_edges)
                faces_out.append(new_faces)
                sites_out.append(new_sites)
            else:
                verts_out.extend(new_verts)
                edges_out.extend(new_edges)
                faces_out.extend(new_faces)
                sites_out.extend(new_sites)

        self.outputs['Vertices'].sv_set(verts_out)
        self.outputs['Edges'].sv_set(edges_out)
        self.outputs['Faces'].sv_set(faces_out)
        #self.outputs['AllSites'].sv_set(sites_out)


def register():
    bpy.utils.register_class(SvVoronoiOnMeshNode)


def unregister():
    bpy.utils.unregister_class(SvVoronoiOnMeshNode)