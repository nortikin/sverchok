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
from bpy.props import BoolProperty, IntProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode


class SvBMObjinputNode(bpy.types.Node, SverchCustomTreeNode):
    ''' BMesh Object In '''
    bl_idname = 'SvBMObjinputNode'
    bl_label = 'BMesh Obj in'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_OBJECT_IN_BMESH'

    UseSKey: BoolProperty(name='with_shapekey', default=False, update=updateNode)
    keyIND: IntProperty(name='SHKey_ind', default=0, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvObjectSocket', 'Objects')
        self.outputs.new('SvStringsSocket', 'vert-hide')
        self.outputs.new('SvStringsSocket', 'edge-hide')
        self.outputs.new('SvStringsSocket', 'edge-seam')
        self.outputs.new('SvStringsSocket', 'edge-smooth')
        self.outputs.new('SvStringsSocket', 'face-hide')
        self.outputs.new('SvStringsSocket', 'face-material indx')
        self.outputs.new('SvStringsSocket', 'face-smooth')
        self.outputs.new('SvStringsSocket', 'bmesh_list')

    def draw_buttons_ext(self, context, layout):
        row = layout.row(align=True)
        row.prop(self, "UseSKey", text="Use ShapeKey")
        row.prop(self, "keyIND", text="Key Index")

    def process(self):
        o1, o2, o3, o4, o5, o6, o7, bmL = self.outputs
        Val = []
        obj = self.inputs[0].sv_get()
        useSHP = self.UseSKey
        SHPIND = self.keyIND
        for OB in obj:
            bm = bmesh.new()
            bm.from_mesh(OB.data, use_shape_key=useSHP, shape_key_index=SHPIND)
            Val.append(bm)
        if o1.is_linked:
            o1.sv_set([[v.hide for v in bm.verts] for bm in Val])
        if o2.is_linked:
            o2.sv_set([[e.hide for e in bm.edges] for bm in Val])
        if o3.is_linked:
            o3.sv_set([[e.seam for e in bm.edges] for bm in Val])
        if o4.is_linked:
            o4.sv_set([[e.smooth for e in bm.edges] for bm in Val])
        if o5.is_linked:
            o5.sv_set([[f.hide for f in bm.faces] for bm in Val])
        if o6.is_linked:
            o6.sv_set([[f.material_index for f in bm.faces] for bm in Val])
        if o7.is_linked:
            o7.sv_set([[f.smooth for f in bm.faces] for bm in Val])
        if bmL.is_linked:
            bmL.sv_set(Val)

def register():
    bpy.utils.register_class(SvBMObjinputNode)


def unregister():
    bpy.utils.unregister_class(SvBMObjinputNode)
