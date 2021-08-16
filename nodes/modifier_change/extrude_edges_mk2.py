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
from sverchok.data_structure import updateNode
from sverchok.utils.mesh.extrude_edges import extrude_edges, extrude_edges_bmesh
from sverchok.utils.nodes_mixins.recursive_nodes import SvRecursiveNode

class SvExtrudeEdgesNodeMk2(bpy.types.Node, SverchCustomTreeNode, SvRecursiveNode):
    '''
    Triggers: Extrude edges
    Tooltip: Extrude some edges of the mesh
    '''
    bl_idname = 'SvExtrudeEdgesNodeMk2'
    bl_label = 'Extrude Edges'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_EXTRUDE_EDGES'
    implementation_items = [
        ('BMESH', 'Bmesh', 'Slower (Legacy. Face data is not transferred identically)', 0),
        ('NUMPY', 'Numpy', 'Faster', 1)]
    implementation: bpy.props.EnumProperty(
        name='Implementation',
        items=implementation_items,
        default='NUMPY',
        update=updateNode
    )
    def draw_buttons_ext(self, context, layout):
        layout.prop(self, 'implementation')
        layout.prop(self, 'list_match')

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvStringsSocket', 'Edges')
        self.inputs.new('SvStringsSocket', 'Faces')
        self.inputs.new('SvStringsSocket', 'EdgeMask')
        self.inputs.new('SvStringsSocket', 'FaceData')
        self.inputs.new('SvMatrixSocket', "Matrices")

        self.outputs.new('SvVerticesSocket', 'Vertices')
        self.outputs.new('SvStringsSocket', 'Edges')
        self.outputs.new('SvStringsSocket', 'Faces')
        self.outputs.new('SvVerticesSocket', 'NewVertices')
        self.outputs.new('SvStringsSocket', 'NewEdges')
        self.outputs.new('SvStringsSocket', 'NewFaces')
        self.outputs.new('SvStringsSocket', 'FaceData')

    def pre_setup(self):
        self.inputs[0].is_mandatory = True
        self.inputs[1].nesting_level = 3
        self.inputs[2].nesting_level = 3
        self.inputs[5].nesting_level = 2
        self.inputs[5].default_mode = 'MATRIX'

    def process_data(self, params):

        output_data = [[] for s in self.outputs]

        for vertices, edges, faces, edge_mask, face_data, matrices in zip(*params):

            if edge_mask or self.implementation == 'BMESH':
                extrude = extrude_edges_bmesh
            else:
                extrude = extrude_edges
            res = extrude(vertices, edges, faces, edge_mask, face_data, matrices)
            for o, r in zip(output_data, res):
                o.append(r)

        return output_data


def register():
    bpy.utils.register_class(SvExtrudeEdgesNodeMk2)


def unregister():
    bpy.utils.unregister_class(SvExtrudeEdgesNodeMk2)
