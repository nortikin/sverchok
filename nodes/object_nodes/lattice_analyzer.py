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

from sverchok.data_structure import updateNode
import sverchok.core.base_nodes as base_nodes


class SvLatticePropsNode(bpy.types.Node, SverchCustomTreeNode, SvAnimatableNode, base_nodes.OutputNode):
    '''Lattice object props'''
    bl_idname = 'SvLatticePropsNode'
    bl_label = 'Lattice Props'
    bl_icon = 'MOD_LATTICE'

    def sv_init(self, context):
        self.inputs.new('SvObjectSocket', 'Lattice Object')
        self.inputs.new('SvVerticesSocket', 'deformed points')
        self.inputs.new('SvStringsSocket', 'point select mask')
        self.outputs.new('SvVerticesSocket', 'init points')
        self.outputs.new('SvVerticesSocket', 'deformed points')
        self.outputs.new('SvObjectSocket', "Lattice Object")

    def draw_buttons(self, context, layout):
        self.draw_animatable_buttons(layout, icon_only=True)

    def process(self):
        lattobj, dep, selm = self.inputs
        Oorp, Odep, obj = self.outputs
        lattpois = [ob.data.points for ob in lattobj.sv_get()]
        if dep.is_linked:
            for la, cop in zip(lattpois, dep.sv_get()):
                for p,c in zip(la, cop):
                    p.co_deform = c
        if selm.is_linked:
            for la, sm in zip(lattpois, selm.sv_get()):
                for p,m in zip(la, sm):
                    p.select = m
        if Oorp.is_linked:
            Oorp.sv_set([[point.co[:] for point in la] for la in lattpois])
        if Odep.is_linked:
            Odep.sv_set([[point.co_deform[:] for point in la] for la in lattpois])
        if obj.is_linked:
            obj.sv_set(lattobj.sv_get())


def register():
    bpy.utils.register_class(SvLatticePropsNode)


def unregister():
    bpy.utils.unregister_class(SvLatticePropsNode)
