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
from numpy import array, empty, concatenate, unique, sort, int32, ndarray

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import dataCorrect_np, updateNode
from sverchok.utils.sv_mesh_utils import polygons_to_edges, polygons_to_edges_np
from sverchok.utils.decorators import deprecated


@deprecated("Please use sverchok.utils.sv_mesh_utils.polygons_to_edges instead")
def pols_edges(obj, unique_edges=False):
    return polygons_to_edges(obj, unique_edges)

class Pols2EdgsNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Edges from Faces
    Tooltip: Get edges lists from polygons lists.
    """

    bl_idname = 'Pols2EdgsNode'
    bl_label = 'Polygons to Edges'
    bl_icon = 'EDGESEL'
    sv_icon = 'SV_POLYGONS_TO_EDGES'

    unique_edges: BoolProperty(
        name="Unique Edges", default=False, update=updateNode)

    regular_pols: BoolProperty(
        name='Regular polygons',
        description='Makes the node faster if all the incoming polygons have the same number of sides',
        default=False, update=updateNode)

    output_numpy: BoolProperty(
        name='Output NumPy',
        description='Output NumPy arrays',
        default=False, update=updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, "regular_pols")
        layout.prop(self, "unique_edges")

    def draw_buttons_ext(self, context, layout):
        '''draw buttons on the N-panel'''
        self.draw_buttons(context, layout)
        layout.prop(self, 'output_numpy')

    def rclick_menu(self, context, layout):
        '''right click sv_menu items'''
        self.draw_buttons(context, layout)
        layout.prop(self, "output_numpy")

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "pols")
        self.outputs.new('SvStringsSocket', "edgs")

    def process(self):
        if not self.outputs[0].is_linked:
            return

        polygons_ = self.inputs['pols'].sv_get(deepcopy=False)
        polygons = dataCorrect_np(polygons_)

        if self.output_numpy or isinstance(polygons[0], ndarray) or self.regular_pols:
            result = polygons_to_edges_np(polygons, self.unique_edges, self.output_numpy)
        else:
            result = polygons_to_edges(polygons, self.unique_edges)

        self.outputs['edgs'].sv_set(result)

    def draw_label(self):
        return (self.label or self.name) if not self.hide else "P to E"


def register():
    bpy.utils.register_class(Pols2EdgsNode)


def unregister():
    bpy.utils.unregister_class(Pols2EdgsNode)
