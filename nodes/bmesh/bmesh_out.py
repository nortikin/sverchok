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
from sverchok.utils.sv_bmesh_utils import pydata_from_bmesh
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from bpy.props import BoolProperty

class SvBMoutputNode(SverchCustomTreeNode, bpy.types.Node):
    ''' BMesh Out '''
    bl_idname = 'SvBMoutputNode'
    bl_label = 'BMesh Out'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_ALPHA'

    free : BoolProperty(
    name = "Free Bmesh",
    description="Destroy the bmesh object from memory",
    default = True,
    update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self,'free')
    
    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', 'Bmesh')
        self.outputs.new('SvVerticesSocket', 'Verts')
        self.outputs.new('SvStringsSocket', 'Edges')
        self.outputs.new('SvStringsSocket', 'Faces')

    def process(self):
        v, e, p = self.outputs
        vlist = []
        elist = []
        plist = []
        if v.is_linked:
            bml = self.inputs['Bmesh'].sv_get()
            for i in bml:
                V,E,P = pydata_from_bmesh(i)
                vlist.append(V)
                elist.append(E)
                plist.append(P)
            if self.free:
                for bm in bml:
                    bm.free()
        v.sv_set(vlist)
        e.sv_set(elist)
        p.sv_set(plist)


def register():
    bpy.utils.register_class(SvBMoutputNode)


def unregister():
    bpy.utils.unregister_class(SvBMoutputNode)
