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
from bpy.props import EnumProperty, FloatProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (enum_item_4, updateNode)
from sverchok.utils.pulga_physics_modular_core import SvCollisionForce
from sverchok.dependencies import scipy, Cython
from sverchok.data_structure import zip_long_repeat
from sverchok.utils.pulga_self_edge_collision import SvSelfEdgeCollisionForce
from sverchok.utils.pulga_collision_domains import SvSelfPolygonCollisionForce, HAS_NUMBA

class SvPulgaCollisionForceNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Collide verts
    Tooltip: Collision forces between vertices, edges and polygons
    """
    bl_idname = 'SvPulgaCollisionForceNode'
    bl_label = 'Pulga Collision Force'
    bl_icon = 'MOD_PHYSICS'
    sv_icon = 'SV_PULGA_COLLISION_FORCE'


    def _ensure_domain_sockets(self):
        if not len(self.inputs):
            return
        for name in ('Edges', 'Polygons', 'Thickness', 'Damping'):
            if name not in self.inputs:
                self.inputs.new('SvStringsSocket', name)
        self.inputs['Thickness'].prop_name = 'thickness'
        self.inputs['Damping'].prop_name = 'damping'
        self.inputs['Edges'].hide_safe = self.collision_domain != 'EDGES'
        self.inputs['Polygons'].hide_safe = self.collision_domain != 'POLYGONS'
        self.inputs['Thickness'].hide_safe = self.collision_domain == 'VERTS'
        self.inputs['Damping'].hide_safe = self.collision_domain == 'VERTS'

    def _update_domain(self, context):
        self._ensure_domain_sockets()
        updateNode(self, context)

    collision_domain: EnumProperty(
        name='Domain', description='Self-collision geometry',
        items=[('VERTS', 'Vertices', 'Preserve the original particle-particle collisions'),
               ('EDGES', 'Edges', 'Particle versus non-incident mesh edge'),
               ('POLYGONS', 'Polygons', 'Two-sided particle versus non-incident face')],
        default='VERTS', update=_update_domain)
    thickness: FloatProperty(name='Thickness', default=0.0, min=0.0,
                             description='Additional collision thickness', update=updateNode)
    damping: FloatProperty(name='Damping', default=0.0, min=0.0,
                           description='Normal contact velocity damping', update=updateNode)
    engine: EnumProperty(name='Engine', default='AUTO', update=updateNode,
        items=[('AUTO','Auto','Use Numba when installed'),
               ('NUMPY','NumPy','Run reference Python/NumPy implementation'),
               ('NUMBA','Numba','Use Numba compiled kernel')])

    strength: FloatProperty(
        name='Strength', description='Collision forces between vertices',
        default=0.01, precision=4, step=1e-2, update=updateNode)
    mode: EnumProperty(
        name='Mode',
        description='Algorithm used for calculation',
        items=enum_item_4(['Brute Force', 'Kd-tree']),
        default='Kd-tree', update=updateNode)


    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "Strength").prop_name = 'strength'

        self.outputs.new('SvPulgaForceSocket', "Force")
        self._ensure_domain_sockets()

    def draw_buttons(self, context, layout):
        layout.prop(self, 'collision_domain', text='')
        if self.collision_domain == 'VERTS' and scipy is not None and Cython is not None:
            layout.prop(self, 'mode')

    def draw_buttons_ext(self, context, layout):
        if self.collision_domain != 'VERTS':
            layout.prop(self, 'engine')
            if not HAS_NUMBA:
                layout.label(text='Numba not available', icon='INFO')

    def process(self):

        if not any(s.is_linked for s in self.outputs):
            return
        self._ensure_domain_sockets()
        if self.collision_domain != 'VERTS':
            topology = 'Edges' if self.collision_domain == 'EDGES' else 'Polygons'
            data = self.inputs[topology].sv_get(deepcopy=False)
            strength_data = self.inputs['Strength'].sv_get(deepcopy=False)
            thickness_data = self.inputs['Thickness'].sv_get(deepcopy=False)
            damping_data = self.inputs['Damping'].sv_get(deepcopy=False)
            forces = []
            for topo, mag, thick, damp in zip_long_repeat(
                    data, strength_data, thickness_data, damping_data):
                if self.collision_domain == 'EDGES':
                    force = SvSelfEdgeCollisionForce(topo, mag, thick, damp, self.engine)
                else:
                    force = SvSelfPolygonCollisionForce(topo, mag, thick, damp, self.engine)
                forces.append(force)
            self.outputs['Force'].sv_set([forces])
            return
        forces_in = self.inputs["Strength"].sv_get(deepcopy=False)

        forces_out = []
        use_kdtree = self.mode in "Kd-tree" and scipy is not None and Cython is not None
        for force in forces_in:
            forces_out.append(SvCollisionForce(force, use_kdtree=use_kdtree))
        self.outputs[0].sv_set([forces_out])




def register():
    bpy.utils.register_class(SvPulgaCollisionForceNode)


def unregister():
    bpy.utils.unregister_class(SvPulgaCollisionForceNode)
