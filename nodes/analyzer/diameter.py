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

from itertools import product

import bpy

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat
from sverchok.utils.geom import diameter

class SvDiameterNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Diameter
    Tooltip: Calculate diameter of input object
    """

    bl_idname = 'SvDiameterNode'
    bl_label = "Diameter"
    bl_icon = 'ARROW_LEFTRIGHT'

    def sv_init(self, context):
        self.inputs.new('VerticesSocket', 'Vertices')
        self.inputs.new('VerticesSocket', 'Direction')
        self.outputs.new('StringsSocket', 'Diameter')

    def process(self):
        if not self.inputs['Vertices'].is_linked:
            return
        if not any(s.is_linked for s in self.outputs):
            return
        
        any_direction = not self.inputs['Direction'].is_linked

        out_results = []

        vertices_s = self.inputs['Vertices'].sv_get(default=[[]])
        directions_s = self.inputs['Direction'].sv_get(default=[[]])
        objects = match_long_repeat([vertices_s, directions_s])

        for vertices, directions in zip(*objects):
            if any_direction:
                direction = None
            else:
                direction = directions[0]
            diam = diameter(vertices, direction)
            out_results.append([diam])

        self.outputs['Diameter'].sv_set(out_results)


def register():
    bpy.utils.register_class(SvDiameterNode)

def unregister():
    bpy.utils.unregister_class(SvDiameterNode)

