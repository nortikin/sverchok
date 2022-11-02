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
import numpy as np
from bpy.props import BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, cycle_for_length


class SvParticlesMK2Node(SverchCustomTreeNode, bpy.types.Node):
    ''' Particles input node new '''
    bl_idname = 'SvParticlesMK2Node'
    bl_label = 'Particles MK2'
    bl_icon = 'PARTICLES'
    is_animation_dependent = True
    is_scene_dependent = True

    Filt_D: BoolProperty(default=True, update=updateNode)

    def sv_draw_buttons_ext(self, context, layout):
        layout.prop(self, "Filt_D", text="filter death")

    def sv_init(self, context):
        self.inputs.new('SvObjectSocket', "Object")
        self.inputs.new('SvVerticesSocket', "Velocity")
        self.inputs.new('SvVerticesSocket', "Location")
        self.inputs.new('SvStringsSocket', "Size")
        self.outputs.new('SvVerticesSocket', "outLocation")
        self.outputs.new('SvVerticesSocket', "outVelocity")

    def process(self):
        O, V, L, S = self.inputs
        outL, outV = self.outputs

        # this may not work in render mode.
        sv_depsgraph = bpy.context.evaluated_depsgraph_get()

        # listobj = [i.particle_systems.active.particles for i in O.sv_get() if i.particle_systems]
        listobj = []
        for obj in O.sv_get():
            if not obj.particle_systems:
                continue
            obj = sv_depsgraph.objects[obj.name]
            particle_systems = obj.evaluated_get(sv_depsgraph).particle_systems
            particles = particle_systems[0].particles
            listobj.append(particles)

        if V.is_linked:
            for i, i2 in zip(listobj, V.sv_get(deepcopy=False)):
                i.foreach_set('velocity', np.array(cycle_for_length(i2, len(i))).flatten())
        if S.is_linked:
            for i, i2 in zip(listobj, S.sv_get(deepcopy=False)):
                i.foreach_set('size', cycle_for_length(i2, len(i)))
        if L.is_linked:
            for i, i2 in zip(listobj, L.sv_get(deepcopy=False)):
                i.foreach_set('location', np.array(cycle_for_length(i2, len(i))).flatten())
        if outL.is_linked:
            if self.Filt_D:
                outL.sv_set([[i.location[:] for i in Plist if i.alive_state == 'ALIVE'] for Plist in listobj])
            else:
                outL.sv_set([[i.location[:] for i in Plist] for Plist in listobj])
        if outV.is_linked:
            outV.sv_set([[i.velocity[:] for i in Plist] for Plist in listobj])


def register():
    bpy.utils.register_class(SvParticlesMK2Node)


def unregister():
    bpy.utils.unregister_class(SvParticlesMK2Node)
