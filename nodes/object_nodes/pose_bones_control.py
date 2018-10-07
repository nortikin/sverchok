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
from bpy.props import IntProperty, StringProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode


class SvArmatureControlNode(bpy.types.Node, SverchCustomTreeNode):
    '''Armature Pose Bones Control'''
    bl_idname = 'SvArmatureControlNode'
    bl_label = 'Control Armature'
    bl_icon = 'OUTLINER_OB_EMPTY'

    Sindex = IntProperty(name='Bone Index', default=0, update=updateNode)

    modes = [
        ("mi_per_bon", "Ind&Mat per Bone", "", 1),
        ("mi_per_obj", "Ind&Mat per Armature", "", 2)]

    mode = EnumProperty(items=modes, default='mi_per_bon', update=updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, "mode", expand=False)

    def sv_init(self, context):
        self.inputs.new('SvObjectSocket', 'Armature Object')
        self.inputs.new('StringsSocket', 'bone select index').prop_name = "Sindex"
        self.inputs.new('MatrixSocket', "matrix basis")

    def process(self):
        armobjL, selind, rotmat = self.inputs
        R = rotmat.sv_get()
        if self.mode == "mi_per_bon":
            for ilist, armobj in zip(selind.sv_get(), armobjL.sv_get()):
                armatbl = [armobj.pose.bones[i] for i in ilist]
                for bone, r in zip(armatbl, R):
                    bone.matrix_basis = r
        elif self.mode == "mi_per_obj":
            for ind, armobj, matr in zip(selind.sv_get()[0], armobjL.sv_get(), R):
                armobj.pose.bones[ind].matrix_basis = matr


def register():
    bpy.utils.register_class(SvArmatureControlNode)


def unregister():
    bpy.utils.unregister_class(SvArmatureControlNode)
