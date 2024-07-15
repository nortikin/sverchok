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
import math
import numpy as np
from mathutils import Matrix, Vector, Quaternion

from bpy.props import BoolProperty, IntProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (Vector_generate, updateNode, match_long_repeat, ensure_nesting_level, zip_long_repeat)
from sverchok.utils.nodes_mixins.sockets_config import ModifierLiteNode


class SvAdaptiveEdgeNodeMK2(ModifierLiteNode, SverchCustomTreeNode, bpy.types.Node):
    '''Map edge object to recipient edges'''
    bl_idname = 'SvAdaptiveEdgeNodeMK2'
    bl_label = 'Adaptive Edges'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_ADAPTATIVE_EDGES'

    mesh_join: BoolProperty(
        name="Join meshes",
        default=True,
        update=updateNode,
        ) # type: ignore
    
    adaptive_edges_mask_modes = [
            ('MASK', "Booleans", "Boolean values (0/1) as mask of Adaptive Edges per objects [[0,1,0,0,1,1],[1,1,0,0,1],...]. Has no influence if socket is not connected (All edges are used)", 0),
            ('INDEXES', "Indexes", "Indexes as mask of Adaptive Edges per objects [[1,2,0,4],[0,1,4,5,7],..]. Has no influence if socket is not connected (All edges are used)", 1),
        ]
    adaptive_edges_mask_mode : EnumProperty(
        name = "Mask mode",
        items = adaptive_edges_mask_modes,
        default = 'MASK',
        #update = updateMaskMode
        update = updateNode
        ) # type: ignore

    adaptive_edges_mask_inversion : BoolProperty(
        name = "Invert",
        default = False,
        description="Invert mask of sites. Has no influence if socket is not connected (All sites are used)",
        update = updateNode) # type: ignore

    
    adaptive_index_0: IntProperty(
        name="adaptive_index_0",
        description = "First adaptive index of plane mesh",
        default=0,
        update=updateNode,
        ) # type: ignore
    
    adaptive_index_1: IntProperty(
        name="adaptive_index_1",
        description = "Second adaptive index of plane mesh",
        default=-1,
        update=updateNode,
        ) # type: ignore

    def draw_buttons(self, context, layout):
        layout.prop(self, "mesh_join")

    def draw_adaptive_edges_mask_in_socket(self, socket, context, layout):
        grid = layout.grid_flow(row_major=True, columns=2)
        if not socket.is_linked:
            grid.enabled = False
        col2 = grid.column()
        col2_row1 = col2.row()
        col2_row1.alignment='LEFT'
        if socket.is_linked:
            col2_row1.label(text=f"Mask of adaptive edges. {socket.objects_number or ''}:")
        else:
            col2_row1.label(text=f"Mask of adaptive edges:")
        col2_row2 = col2.row()
        col2_row2.alignment='LEFT'
        col2_row2.column(align=True).prop(self, "adaptive_edges_mask_inversion")
        col3 = grid.column()
        col3.prop(self, "adaptive_edges_mask_mode", expand=True)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'adaptive_verts')
        self.inputs.new('SvStringsSocket', 'adaptive_edges')
        self.inputs.new('SvStringsSocket', 'adaptive_edges_mask').label = "Mask of Adaptive Edges"
        self.inputs.new('SvVerticesSocket', 'mesh_verts')
        self.inputs.new('SvStringsSocket', 'mesh_edges')
        self.inputs.new('SvStringsSocket', "adaptive_index_0").prop_name = 'adaptive_index_0'
        self.inputs.new('SvStringsSocket', "adaptive_index_1").prop_name = 'adaptive_index_1'

        self.inputs['adaptive_edges_mask'].custom_draw = 'draw_adaptive_edges_mask_in_socket'

        self.inputs["adaptive_verts"  ].label = "Adaptive verts"
        self.inputs["adaptive_edges"  ].label = "Adaptive edges"
        self.inputs["mesh_verts"      ].label = "Verts"
        self.inputs["mesh_edges"      ].label = "Edges"
        self.inputs["adaptive_index_0"].label = "First adaptive index"
        self.inputs["adaptive_index_1"].label = "Second adaptive index"

        self.outputs.new('SvVerticesSocket', 'Vertices')
        self.outputs.new('SvStringsSocket', 'Edges')

    def process(self):
        if not all(s.is_linked for s in self.inputs if s.name in ['adaptive_verts', 'adaptive_edges', 'mesh_verts', 'mesh_edges']):
            return
        if not any(socket.is_linked for socket in self.outputs):
            return

        adaptive_verts_in = self.inputs['adaptive_verts'].sv_get()
        mesh_verts_in = self.inputs['mesh_verts'].sv_get()
        adaptive_edges_in = self.inputs['adaptive_edges'].sv_get()
        mesh_edges_in = self.inputs['mesh_edges'].sv_get()
        ai0_in = self.inputs['adaptive_index_0'].sv_get(default=0)
        ai1_in = self.inputs['adaptive_index_1'].sv_get(default=-1)

        adaptive_edges_mask_in_socket = self.inputs['adaptive_edges_mask'] #.sv_get(deepcopy=False)
        if adaptive_edges_mask_in_socket.is_linked==False:
            adaptive_edges_mask_in = [[]]
        else:
            adaptive_edges_mask_in = adaptive_edges_mask_in_socket.sv_get(deepcopy=False)
        adaptive_edges_mask_in2 = ensure_nesting_level(adaptive_edges_mask_in, 2)

        verts_out = []
        edges_out = []
        verts_out1 = []
        edges_out1 = []
        mesh_join = self.mesh_join

        adaptive_verts_in3 = ensure_nesting_level(adaptive_verts_in, 3)
        mesh_verts_in3     = ensure_nesting_level(mesh_verts_in, 3)
        adaptive_edges_in3 = ensure_nesting_level(adaptive_edges_in, 3)
        mesh_edges_in3     = ensure_nesting_level(mesh_edges_in, 3)
        ai0_in2            = ensure_nesting_level(ai0_in, 2)
        ai0_in2_wrapped    = [[[v] for v in vi] for vi in ai0_in2 ][0]
        ai1_in2            = ensure_nesting_level(ai1_in, 2)
        ai1_in2_wrapped    = [[[v] for v in vi] for vi in ai1_in2 ][0]

        ai0_in2_wrapped = ai0_in2_wrapped[:len(mesh_verts_in3)] # not longer
        ai1_in2_wrapped = ai1_in2_wrapped[:len(mesh_verts_in3)]

        mesh_verts_in3, ai0_in2_wrapped = match_long_repeat([mesh_verts_in3, ai0_in2_wrapped])
        mesh_verts_in3, ai1_in2_wrapped = match_long_repeat([mesh_verts_in3, ai1_in2_wrapped])

        adaptive_edges_mask_in2_wrapped = adaptive_edges_mask_in2[:len(adaptive_verts_in3)] # not longer than adaptive objects
        adaptive_verts_in3, adaptive_edges_mask_in2_wrapped = match_long_repeat([adaptive_verts_in3, adaptive_edges_mask_in2_wrapped]) # only adaptive_edges_mask_in2_wrapped can be changed here

        adaptive_verts_in3_vectors = Vector_generate(adaptive_verts_in3)
        mesh_verts_in3_vectors = Vector_generate(mesh_verts_in3)

        mesh_verts_in3_0 = []
        for I, objD_verts in enumerate(mesh_verts_in3_vectors):
            objD_vert0 = objD_verts[ ai0_in2_wrapped[I][0] ]
            objD_new_verts = []
            for objD_vert in objD_verts:
                objD_new_verts.append(objD_vert-objD_vert0)

            user_vector = objD_new_verts[ ai1_in2_wrapped[I][0] ].copy()
            user_vector.normalize()
            VOx = Vector((1,0,0))
            if user_vector.cross( VOx ).magnitude>0:
                # vector of mesh D has to be collinear Ox
                q = VOx.rotation_difference(user_vector)
                mat_r = Matrix.Rotation(q.angle, 4, q.axis)
                objD_new_verts = [ v @ mat_r for v in objD_new_verts]
                pass

            mesh_verts_in3_0.append( objD_new_verts )
            pass

        for vc, edg, adaptive_edges_mask in zip(adaptive_verts_in3_vectors, adaptive_edges_in3, adaptive_edges_mask_in2_wrapped):
            #adaptive_edges_mask = adaptive_edges_mask[:len(edg)]  # not longer than len of edg
            if mesh_join:
                v_out = []
                v_out_app = v_out.append
            e_out = []
            e_out_app = e_out.append

            # if adaptive_edges_mask is zero or not connected then do not mask any. Except of inversion,
            if not adaptive_edges_mask:
                np_mask = np.zeros(len(edg), dtype=bool)
                if self.inputs['adaptive_edges_mask'].is_linked and self.adaptive_edges_mask_inversion==True:
                    np_mask = np.invert(np_mask)
                adaptive_edges_mask = np_mask.tolist()
            else:
                if self.adaptive_edges_mask_mode=='MASK':
                    if self.adaptive_edges_mask_inversion==True:
                        adaptive_edges_mask = list( map( lambda v: False if v==0 else True, adaptive_edges_mask) )
                        adaptive_edges_mask = adaptive_edges_mask[:len(edg)]
                        np_adaptive_edges_mask = np.zeros(len(edg), dtype=bool)
                        np_adaptive_edges_mask[0:len(adaptive_edges_mask)]=adaptive_edges_mask
                        np_adaptive_edges_mask = np.invert(np_adaptive_edges_mask)
                        adaptive_edges_mask = np_adaptive_edges_mask.tolist()
                    pass
                elif self.adaptive_edges_mask_mode=='INDEXES':
                    adaptive_edges_mask_len = len(edg)
                    adaptive_edges_mask_range = []
                    for x in adaptive_edges_mask:
                        if -adaptive_edges_mask_len<x<adaptive_edges_mask_len:
                            adaptive_edges_mask_range.append(x)
                    np_adaptive_edges_mask = np.zeros(len(edg), dtype=bool)
                    np_adaptive_edges_mask[adaptive_edges_mask_range] = True
                    if self.adaptive_edges_mask_inversion==True:
                        np_adaptive_edges_mask = np.invert(np_adaptive_edges_mask)
                    adaptive_edges_mask = np_adaptive_edges_mask.tolist()

            _, mesh_verts0_long, mesh_edges_long, ai1_in2_long, adaptive_edges_mask_long = match_long_repeat([ edg, mesh_verts_in3_0, mesh_edges_in3, ai1_in2_wrapped, adaptive_edges_mask])
            for e, verD, edgD, ai1, adaptive_edge_mask in zip(edg, mesh_verts0_long, mesh_edges_long, ai1_in2_long, adaptive_edges_mask_long):
                if adaptive_edge_mask==True:
                    continue
                # for every edge or for objectR???
                d_vector = verD[ ai1[0] ].copy()
                d_scale = d_vector.length
                d_vector.normalize()
                # leave for now
                if not mesh_join:
                    v_out = []
                    v_out_app = v_out.append
                e_vector = vc[e[1]] - vc[e[0]]
                e_scale = e_vector.length
                e_vector.normalize()
                q1 = d_vector.rotation_difference(e_vector)
                dot_de = d_vector.dot(e_vector)

                # This is a only exception when edge direct is oposide custom vector of mesh. It should rotate manually:
                if dot_de<-0.99999:
                    Oz = Vector((0,0,1))
                    q1 = Quaternion( Oz, math.radians(180) )

                mat_s = Matrix.Scale(e_scale / d_scale, 4)
                mat_r = Matrix.Rotation(q1.angle, 4, q1.axis)
                mat_l = Matrix.Translation(vc[e[0]])
                mat = mat_l @ mat_r @ mat_s

                offset = len(v_out)
                for v in verD:
                    v_out_app((mat @ v)[:])

                if mesh_join:
                    for edge in edgD:
                        e_out_app([i + offset for i in edge])
                else:
                    verts_out1.append(v_out)
                    edges_out1.append(edgD)
                pass

            if mesh_join:
                verts_out1.append(v_out)
                edges_out1.append(e_out)
            pass

        if self.outputs['Vertices'].is_linked:
            self.outputs['Vertices'].sv_set(verts_out1)

        if self.outputs['Edges'].is_linked:
            self.outputs['Edges'].sv_set(edges_out1)


def register():
    bpy.utils.register_class(SvAdaptiveEdgeNodeMK2)


def unregister():
    bpy.utils.unregister_class(SvAdaptiveEdgeNodeMK2)
