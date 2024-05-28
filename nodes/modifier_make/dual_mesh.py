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

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (match_long_repeat, updateNode, flatten_data)
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata, dual_mesh, add_mesh_to_bmesh
from sverchok.utils.nodes_mixins.sockets_config import ModifierNode
from bpy.props import BoolVectorProperty, EnumProperty, BoolProperty, FloatProperty, IntProperty


class SvDualMeshNodeMK2(ModifierNode, SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Dual Mesh
    Tooltip: Create dual mesh for the given mesh
    """
    bl_idname = 'SvDualMeshNodeMK2'
    bl_label = "Dual Mesh"
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_DUAL_MESH'

    keep_boundaries : BoolProperty(
        name = "Keep Boundaries",
        description = "Keep non-manifold boundaries of the mesh in place by avoiding the dual transformation there. Has no influence if Levels==0",
        default = False,
        update = updateNode)  # type: ignore
    
    dual_mesh_levels : IntProperty(
        min=0, default=1, name='Levels',
        description="Dual Mesh Levels. (min=0 - disable dual mesh, default=1)", update=updateNode) # type: ignore

    def sv_init(self, context):
        self.width = 150
        self.inputs.new('SvVerticesSocket', 'vertices')
        self.inputs.new('SvStringsSocket' , 'edges')
        self.inputs.new('SvStringsSocket' , 'polygons')
        self.inputs.new('SvStringsSocket' , 'dual_mesh_levels').prop_name = 'dual_mesh_levels'

        self.inputs['vertices'].label = 'Vertices'
        self.inputs['edges']   .label = 'Edges'
        self.inputs['polygons'].label = 'Polygons'

        self.outputs.new('SvVerticesSocket', 'vertices')
        self.outputs.new('SvStringsSocket' , 'edges')
        self.outputs.new('SvStringsSocket' , 'polygons')
        self.outputs.new('SvStringsSocket' , 'dual_mesh_levels')

        self.outputs['vertices'].label = 'Vertices'
        self.outputs['edges']   .label = 'Edges'
        self.outputs['polygons'].label = 'Polygons'
        self.outputs['dual_mesh_levels'].label = 'Levels'

    @property
    def sv_internal_links(self):
        return [
            (self.inputs[0], self.outputs[0]),
            (self.inputs[2], self.outputs[1]),
        ]
    
    def draw_buttons(self, context, layout):
        col = layout.column()
        col.row().prop(self, 'keep_boundaries')

    def process(self):
        if not any((s.is_linked for s in self.outputs)):
            return

        verts_s = self.inputs['vertices'].sv_get()
        edges_s = self.inputs['edges'].sv_get(default=[[]])
        polygons_s = self.inputs['polygons'].sv_get()
        _dual_mesh_levels = self.inputs['dual_mesh_levels'].sv_get(default=[[1]], deepcopy=False)
        dual_mesh_levels = flatten_data(_dual_mesh_levels)

        verts_out = []
        edges_out = []
        polygons_out = []

        objects = match_long_repeat([verts_s, edges_s, polygons_s, dual_mesh_levels])
        for verts, edges, polygons, dual_mesh_level in zip(*objects):
            if dual_mesh_level<0:
                dual_mesh_level=0
            new_verts, new_edges, new_polygons = verts, edges, polygons
            if dual_mesh_level>0:
                bm = bmesh_from_pydata(new_verts, new_edges, new_polygons, markup_edge_data=True, normal_update=True)
                for I in range(dual_mesh_level):
                    if I>0:
                        bm.clear()
                        add_mesh_to_bmesh(bm, new_verts, new_edges, new_polygons)
                    new_verts, new_edges, new_polygons = dual_mesh(bm, keep_boundaries=self.keep_boundaries)
                bm.free()
                if not new_polygons:
                    break  # if no mesh
                pass

            verts_out.append(new_verts)
            edges_out.append(new_edges)
            polygons_out.append(new_polygons)

        self.outputs['vertices'].sv_set(verts_out)
        self.outputs['edges'].sv_set(edges_out)
        self.outputs['polygons'].sv_set(polygons_out)
        self.outputs['dual_mesh_levels'].sv_set([[l] for l in dual_mesh_levels])

def register():
    bpy.utils.register_class(SvDualMeshNodeMK2)


def unregister():
    bpy.utils.unregister_class(SvDualMeshNodeMK2)

