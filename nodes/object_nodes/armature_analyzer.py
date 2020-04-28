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
from sverchok.utils.nodes_mixins.sv_animatable_nodes import SvAnimatableNode

from sverchok.data_structure import match_long_cycle as mlc, updateNode


class SvArmaturePropsNode(bpy.types.Node, SverchCustomTreeNode, SvAnimatableNode):
    '''Armature object props'''
    bl_idname = 'SvArmaturePropsNode'
    bl_label = 'Armature Props'
    bl_icon = 'MOD_ARMATURE'

    def sv_init(self, context):
        self.inputs.new('SvObjectSocket', 'Armature Object')
        self.inputs.new('SvStringsSocket', 'bone select mask')
        self.outputs.new('SvVerticesSocket', 'Head')
        self.outputs.new('SvVerticesSocket', 'Middle relative')
        self.outputs.new('SvVerticesSocket', 'Tail')
        self.outputs.new('SvVerticesSocket', 'Direction relative')
        self.outputs.new('SvStringsSocket', 'Length of bone')
        self.outputs.new('SvMatrixSocket', "local bone matrix")
        self.outputs.new('SvObjectSocket', "Armature Object")
        
    def draw_buttons(self, context, layout):
        self.animatable_buttons(layout, icon_only=True)

    def process(self):
        armobj, selm = self.inputs
        head, Cent, tail, Norm, lng, matr, obj = self.outputs
        armat =  [ob.data.bones for ob in armobj.sv_get()]
        if selm.is_linked:
            for ar, sm in zip(armat, selm.sv_get()):
                for b,m in zip(ar, sm):
                    b.select = b.select_head = b.select_tail = m
        if head.is_linked:
            head.sv_set([[bone.head_local[:] for bone in ar] for ar in armat])
        if Cent.is_linked:
            Cent.sv_set([[bone.center[:] for bone in ar] for ar in armat])
        if tail.is_linked:
            tail.sv_set([[bone.tail_local[:] for bone in ar] for ar in armat])
        if Norm.is_linked:
            Norm.sv_set([[bone.vector[:] for bone in ar] for ar in armat])
        if lng.is_linked:
            lng.sv_set([[bone.length for bone in ar] for ar in armat])
        if matr.is_linked:
            if len(armat) > 1:
                matr.sv_set([[bone.matrix_local for bone in ar] for ar in armat])
            else:
                matr.sv_set([bone.matrix_local for bone in armat[0]])
        if obj.is_linked:
            obj.sv_set(armobj.sv_get())


def register():
    bpy.utils.register_class(SvArmaturePropsNode)


def unregister():
    bpy.utils.unregister_class(SvArmaturePropsNode)
