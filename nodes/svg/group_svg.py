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

from math import sin, cos, pi, degrees, radians
from mathutils import Matrix
import bpy
from bpy.props import StringProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (fullList, match_long_repeat, updateNode)
from sverchok.data_structure import match_long_repeat as mlr
from sverchok.utils.svg import SvgGroup



class SvSvgGroupNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Group SVG
    Tooltip: Svg circle/ellipse shape, the shapes will be wrapped in SVG Groups
    """
    bl_idname = 'SvSvgGroupNode'
    bl_label = 'Group SVG'
    bl_icon = 'MESH_CIRCLE'
    sv_icon = 'SV_GROUP_SVG'

    group_name: StringProperty(name='Name', description='Group Name', default="layer 1", update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvSvgSocket', "SVG Objects")
        self.inputs.new('SvVerticesSocket', "Offset")
        self.outputs.new('SvSvgSocket', "SVG Objects")

    def draw_buttons(self, context, layout):
        layout.prop(self, 'group_name')

    def process(self):

        if not any(s.is_linked for s in self.outputs):
            return
        objs_in = self.inputs['SVG Objects'].sv_get(deepcopy=False)
        locs_in = self.inputs['Offset'].sv_get(deepcopy=False, default=None)
        if locs_in:
            groups = []
            idx = 0
            for locs in locs_in:
                for loc in locs:
                    groups.append(SvgGroup(objs_in, name=f'{self.group_name}_{idx}', location=loc))
                    idx += 1
            self.outputs[0].sv_set(groups)
        else:
            self.outputs[0].sv_set([SvgGroup(objs_in, name=self.group_name)])


def register():
    bpy.utils.register_class(SvSvgGroupNode)


def unregister():
    bpy.utils.unregister_class(SvSvgGroupNode)
