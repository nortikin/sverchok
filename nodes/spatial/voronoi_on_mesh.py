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
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level, ensure_min_nesting
from sverchok.ui.sv_icons import custom_icon
from sverchok.utils.sv_bmesh_utils import recalc_normals
from sverchok.utils.sv_mesh_utils import mesh_join
from sverchok.utils.voronoi3d import voronoi_on_mesh
import numpy as np


class SvVoronoiOnMeshNodeMK4(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Voronoi Mesh
    Tooltip: Generate Voronoi diagram on the surface of a mesh object
    """
    bl_idname = 'SvVoronoiOnMeshNodeMK4'
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
        update=updateNode) # type: ignore

    normals : BoolProperty(
        name = "Correct normals",
        default = True,
        description="Make sure that all normals of generated meshes point outside",
        update = updateNode) # type: ignore

    def update_sockets(self, context):
        self.inputs['spacing'].hide_safe = self.mode not in {'VOLUME', 'SURFACE'}
        updateNode(self, context)

    mode : EnumProperty(
        name = "Mode",
        items = modes,
        default = 'VOLUME',
        update = update_sockets) # type: ignore
    
    join_modes = [
            ('FLAT', "Separate All Meshes", "Post processing: Separate the result meshes into individual meshes", custom_icon("SV_VOM_SEPARATE_ALL_MESHES"), 0),
            ('SEPARATE', "Keep Source Meshes", "Post processing: Keep parts of the source meshes as source meshes.", custom_icon("SV_VOM_KEEP_SOURCE_MESHES"), 1),
            ('JOIN', "Join All Meshes", "Post processing: Join all results meshes into a single mesh", custom_icon("SV_VOM_JOIN_ALL_MESHES"), 2)
        ]

    join_mode : EnumProperty(
        name = "Output mode",
        items = join_modes,
        default = 'FLAT',
        update = updateNode) # type: ignore

    def updateMaskMode(self, context):
        if self.mask_mode=='MASK':
            self.inputs["voronoi_sites_mask"].label = "Mask of Sites"
        elif self.mask_mode=='INDEXES':
            self.inputs["voronoi_sites_mask"].label = "Indexes of Sites"
        updateNode(self, context)

    mask_modes = [
            ('MASK', "Booleans", "Boolean values (0/1) as mask of Voronoi Sites per objects [[0,1,0,0,1,1],[1,1,0,0,1],...]. Has no influence if socket is not connected (All sites are used)", 0),
            ('INDEXES', "Indexes", "Indexes as mask of Voronoi Sites per objects [[1,2,0,4],[0,1,4,5,7],..]. Has no influence if socket is not connected (All sites are used)", 1),
        ]
    mask_mode : EnumProperty(
        name = "Mask mode",
        items = mask_modes,
        default = 'MASK',
        #update = updateMaskMode
        update = updateNode
        ) # type: ignore

    mask_inversion : BoolProperty(
        name = "Invert",
        default = False,
        description="Invert mask of sites. Has no influence if socket is not connected (All sites are used)",
        update = updateNode) # type: ignore


    accuracy : IntProperty(
            name = "Accuracy",
            description = "Accuracy for mesh bisecting procedure",
            default = 6,
            min = 1,
            update = updateNode) # type: ignore

    def draw_vertices_out_socket(self, socket, context, layout):
        layout.prop(self, 'join_mode', text='')
        if socket.is_linked:  # linked INPUT or OUTPUT
            layout.label(text=f"{socket.label}. {socket.objects_number or ''}")
        else:
            layout.label(text=f'{socket.label}')
        pass

    def draw_voronoi_sites_mask_in_socket(self, socket, context, layout):
        grid = layout.grid_flow(row_major=True, columns=2)
        if not socket.is_linked:
            grid.enabled = False
        col2 = grid.column()
        col2_row1 = col2.row()
        col2_row1.alignment='LEFT'
        if socket.is_linked:
            col2_row1.label(text=f"Mask of sites. {socket.objects_number or ''}:")
        else:
            col2_row1.label(text=f"Mask of sites:")
        col2_row2 = col2.row()
        col2_row2.alignment='LEFT'
        col2_row2.column(align=True).prop(self, "mask_inversion")
        col3 = grid.column()
        col3.prop(self, "mask_mode", expand=True)


    def sv_init(self, context):
        self.width = 250
        self.inputs.new('SvVerticesSocket', 'vertices').label = 'Vertices'
        self.inputs.new('SvStringsSocket', 'polygons').label = 'Polygons'
        self.inputs.new('SvVerticesSocket', 'voronoi_sites').label = 'Voronoi Sites'
        self.inputs.new('SvStringsSocket', 'voronoi_sites_mask').label = "Mask of Voronoi Sites"
        self.inputs.new('SvStringsSocket', 'spacing').prop_name = 'spacing'

        self.inputs['voronoi_sites_mask'].custom_draw = 'draw_voronoi_sites_mask_in_socket'

        self.outputs.new('SvVerticesSocket', "vertices").label = 'Vertices'
        self.outputs.new('SvStringsSocket', "edges").label = 'Edges'
        self.outputs.new('SvStringsSocket', "polygons").label = 'Polygons'
        self.outputs.new('SvStringsSocket', "sites_idx").label = 'Used Sites Idx'
        self.outputs.new('SvStringsSocket', "sites_verts").label = 'Used Sites Verts'

        self.outputs['vertices'].custom_draw = 'draw_vertices_out_socket'

        self.update_sockets(context)

    def draw_buttons(self, context, layout):
        layout.label(text="Mode:")
        layout.prop(self, "mode", expand=True)
        # split = layout.column().split(factor=0.6)
        # split.column().prop(self, "mask_mode", text='')
        # split.column().prop(self, "mask_inversion", text='Invert')
        if self.mode == 'VOLUME':
            layout.prop(self, 'normals')
        # layout.label(text='Recombine result:')
        # layout.prop(self, 'join_mode', text='')

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, 'accuracy')

    def process(self):

        if not any(socket.is_linked for socket in self.outputs):
            return

        verts_in = self.inputs['vertices'].sv_get(deepcopy=False)
        faces_in = self.inputs['polygons'].sv_get(deepcopy=False)
        sites_in = self.inputs['voronoi_sites'].sv_get(deepcopy=False)

        mask_in = self.inputs['voronoi_sites_mask'] #.sv_get(deepcopy=False)
        if mask_in.is_linked==False:
            mask_in = [[]]
        else:
            mask_in = mask_in.sv_get(deepcopy=False)
            
        spacing_in = self.inputs['spacing'].sv_get(deepcopy=False)

        verts_in = ensure_nesting_level(verts_in, 3)
        input_level = get_data_nesting_level(sites_in, search_first_data=True)
        if input_level<=2:
            sites_in = ensure_nesting_level(sites_in, 3)

        faces_in = ensure_nesting_level(faces_in, 3)
        spacing_in = ensure_min_nesting(spacing_in, 2)
        mask_in = ensure_min_nesting(mask_in, 2)

        precision = 10 ** (-self.accuracy)

        verts_out = []
        edges_out = []
        faces_out = []
        sites_idx_out = []
        sites_verts_out = []

        for verts, faces, sites, spacing, mask in zip_long_repeat(verts_in, faces_in, sites_in, spacing_in, mask_in):
            # if mask is zero or not connected then do not mask any. Except of inversion,
            if not mask:
                np_mask = np.ones(len(sites), dtype=bool)
                if self.inputs['voronoi_sites_mask'].is_linked and self.mask_inversion==True:
                    np_mask = np.invert(np_mask)
                mask = np_mask.tolist()
            else:
                if self.mask_mode=='MASK':
                    if self.mask_inversion==True:
                        mask = list( map( lambda v: False if v==0 else True, mask) )
                        mask = mask[:len(sites)]
                        np_mask = np.zeros(len(sites), dtype=bool)
                        np_mask[0:len(mask)]=mask
                        np_mask = np.invert(np_mask)
                        mask = np_mask.tolist()
                    pass
                elif self.mask_mode=='INDEXES':
                    mask_len = len(sites)
                    mask_range = []
                    for x in mask:
                        if -mask_len<x<mask_len:
                            mask_range.append(x)
                    np_mask = np.zeros(len(sites), dtype=bool)
                    np_mask[mask_range] = True
                    if self.mask_inversion==True:
                        np_mask = np.invert(np_mask)
                    mask = np_mask.tolist()

            new_verts, new_edges, new_faces, new_used_sites_idx, new_used_sites_verts = voronoi_on_mesh(verts, faces, sites, thickness=0,
                            spacing = spacing,
                            #clip_inner = self.clip_inner, clip_outer = self.clip_outer,
                            do_clip=True, clipping=None,
                            mode = self.mode,
                            normal_update = self.normals,
                            precision = precision,
                            mask = mask
                            )

            # collect sites_idx and used_sites_verts independently of self.join_mode
            sites_idx_out.append(new_used_sites_idx)
            sites_verts_out.append(new_used_sites_verts)
            
            if self.join_mode == 'FLAT':
                verts_out.extend(new_verts)
                edges_out.extend(new_edges)
                faces_out.extend(new_faces)
            elif self.join_mode == 'SEPARATE' or self.join_mode == 'JOIN':
                verts1, edges1, faces1 = mesh_join(new_verts, new_edges, new_faces)
                verts_out.append(verts1)
                edges_out.append(edges1)
                faces_out.append(faces1)

        if self.join_mode == 'JOIN':
            verts1, edges1, faces1 = mesh_join(verts_out, edges_out, faces_out)
            verts_out = [verts1]
            edges_out = [edges1]
            faces_out = [faces1]

        self.outputs['vertices'].sv_set(verts_out)
        self.outputs['edges'].sv_set(edges_out)
        self.outputs['polygons'].sv_set(faces_out)
        self.outputs['sites_idx'].sv_set(sites_idx_out)
        self.outputs['sites_verts'].sv_set(sites_verts_out)

classes = [SvVoronoiOnMeshNodeMK4]
register, unregister = bpy.utils.register_classes_factory(classes)