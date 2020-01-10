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
from bpy.props import BoolProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import dataCorrect
from sverchok.utils.sv_mesh_utils import polygons_to_edges
from sverchok.utils.decorators import deprecated

@deprecated("Please use sverchok.utils.sv_mesh_utils.polygons_to_edges instead")
def pols_edges(obj, unique_edges=False):
    return polygons_to_edges(obj, unique_edges)

class Pols2EdgsNode(bpy.types.Node, SverchCustomTreeNode):
    ''' take polygon and to edges '''
    bl_idname = 'Pols2EdgsNode'
    bl_label = 'Polygons to Edges'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_POLYGONS_TO_EDGES'

    unique_edges: BoolProperty(
        name="Unique Edges", default=False, update=SverchCustomTreeNode.process_node)

    def draw_buttons(self, context, layout):
        layout.prop(self, "unique_edges")

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "pols")
        self.outputs.new('SvStringsSocket', "edgs")

    def process(self):
        if not self.outputs[0].is_linked:
            return
        X_ = self.inputs['pols'].sv_get()
        X = dataCorrect(X_)
        result = polygons_to_edges(X, self.unique_edges)
        self.outputs['edgs'].sv_set(result)


def register():
    bpy.utils.register_class(Pols2EdgsNode)


def unregister():
    bpy.utils.unregister_class(Pols2EdgsNode)
