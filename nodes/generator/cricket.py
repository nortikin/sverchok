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
import bmesh

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat
from sverchok.utils.modules import sv_bmesh

class SvCricketNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: cricket
    Tooltip:  lowpoly cricket model
    
    """

    bl_idname = "SvCricketNode"
    bl_label = "Cricket"
    bl_icon = "GHOST_ENABLED"

    cricket_scale: bpy.props.FloatProperty(name='scale', default=4.0, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "Scale").prop_name = "cricket_scale"
        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket',  "Faces")

    def process(self):
        # return if no outputs are connected
        if not any(s.is_linked for s in self.outputs):
            return

        out_verts = []
        out_faces = []

        in_scale = self.inputs['Scale'].sv_get(default=[[self.cricket_scale]])
        
        verts, _, faces = sv_bmesh.create_cricket(as_pydata=True, scale=in_scale[0][0])
        out_verts.append(verts)
        out_faces.append(faces)

        self.outputs['Vertices'].sv_set(out_verts)
        self.outputs['Faces'].sv_set(out_faces)


classes = [SvCricketNode]
register, unregister = bpy.utils.register_classes_factory(classes)
