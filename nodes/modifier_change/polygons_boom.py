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
from sverchok.data_structure import SvSetSocketAnyType, SvGetSocketAnyType


class PolygonBoomNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Destroy object to many object of polygons '''
    bl_idname = 'PolygonBoomNode'
    bl_label = 'PolygonBoom'
    bl_icon = 'OUTLINER_OB_EMPTY'

    def sv_init(self, context):
        self.inputs.new('VerticesSocket', "vertices", "vertices")
        self.inputs.new('StringsSocket', 'edg_pol', 'edg_pol')
        self.outputs.new('VerticesSocket', 'vertices', 'vertices')
        self.outputs.new('StringsSocket', 'edg_pol', 'edg_pol')

    def draw_buttons(self, context, layout):
        pass

    def process(self):
        # inputs
        if 'vertices' in self.outputs and self.outputs['vertices'].links or \
                'edg_pol' in self.outputs and self.outputs['edg_pol'].links:
            if 'vertices' in self.inputs and self.inputs['vertices'].links and \
                'edg_pol' in self.inputs and self.inputs['edg_pol'].links:
                vertices = SvGetSocketAnyType(self, self.inputs['vertices'])
                edgs_pols = SvGetSocketAnyType(self, self.inputs['edg_pol'])
            else:
                return
            vert_out = []
            edpo_out = []
            for k, ob in enumerate(edgs_pols):
                for ep in ob:
                    new_vers = []
                    new_edpo = []
                    for i, index in enumerate(ep):
                        new_vers.append(vertices[k][index])
                        new_edpo.append(i)
                    vert_out.append(new_vers)
                    edpo_out.append([new_edpo])

            if 'vertices' in self.outputs and self.outputs['vertices'].links:
                SvSetSocketAnyType(self, 'vertices', vert_out)
            if 'edg_pol' in self.outputs and self.outputs['edg_pol'].links:
                SvSetSocketAnyType(self, 'edg_pol', edpo_out)


def register():
    bpy.utils.register_class(PolygonBoomNode)


def unregister():
    bpy.utils.unregister_class(PolygonBoomNode)
