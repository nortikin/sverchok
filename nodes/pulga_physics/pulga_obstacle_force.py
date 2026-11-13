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
from bpy.props import FloatProperty, EnumProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (zip_long_repeat, updateNode)
from sverchok.utils.pulga_physics_modular_core import SvObstaclesBVHForce
from sverchok.utils.pulga_collision_domains import SvStaticPointEdgeObstacleForce, HAS_NUMBA
from sverchok.utils.pulga_parametric_obstacles import SvParametricObstacleForce
from sverchok.utils.curve import SvCurve
from sverchok.utils.surface import SvSurface
from sverchok.dependencies import FreeCAD

class SvPulgaObstacleForceNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Colliding Obstacles
    Tooltip: Objects that collide with particles
    """
    bl_idname = 'SvPulgaObstacleForceNode'
    bl_label = 'Pulga Obstacles Force'
    bl_icon = 'MOD_PHYSICS'
    sv_icon = 'SV_PULGA_OBSTACLES_FORCE'


    def _ensure_domain_sockets(self):
        if not len(self.inputs):
            return
        if 'Edges' not in self.inputs:
            self.inputs.new('SvStringsSocket', 'Edges')
        if 'Thickness' not in self.inputs:
            self.inputs.new('SvStringsSocket', 'Thickness')
        self.inputs['Thickness'].prop_name = 'thickness'
        self.inputs['Edges'].hide_safe = self.collision_domain != 'EDGES'
        self.inputs['Pols'].hide_safe = self.collision_domain != 'POLYGONS'
        self.inputs['Thickness'].hide_safe = self.collision_domain == 'POLYGONS'

        # Parametric domains. Create sockets once; hide instead of removing links.
        for name, socket_type, prop in (
                ('Curve', 'SvCurveSocket', None),
                ('Surface', 'SvSurfaceSocket', None),
                ('Solid', 'SvSolidSocket', None),
                ('Resolution', 'SvStringsSocket', 'resolution'),
                ('Resolution U', 'SvStringsSocket', 'resolution_u'),
                ('Resolution V', 'SvStringsSocket', 'resolution_v'),
                ('Initial Samples', 'SvStringsSocket', 'init_samples'),
                ('Initial Samples U', 'SvStringsSocket', 'init_samples_u'),
                ('Initial Samples V', 'SvStringsSocket', 'init_samples_v'),
                ('Deflection', 'SvStringsSocket', 'deflection')):
            if name not in self.inputs:
                s = self.inputs.new(socket_type, name)
                if prop is not None:
                    s.prop_name = prop
        domain = self.collision_domain
        fast = domain in {'CURVE', 'SURFACE', 'SOLID'} and self.method == 'FAST'
        precise = domain in {'CURVE', 'SURFACE'} and self.method == 'PRECISE'
        self.inputs['Vertices'].hide_safe = domain in {'CURVE', 'SURFACE', 'SOLID'}
        self.inputs['Curve'].hide_safe = domain != 'CURVE'
        self.inputs['Surface'].hide_safe = domain != 'SURFACE'
        self.inputs['Solid'].hide_safe = domain != 'SOLID'
        self.inputs['Resolution'].hide_safe = not (domain == 'CURVE' and fast)
        self.inputs['Resolution U'].hide_safe = not (domain == 'SURFACE' and fast)
        self.inputs['Resolution V'].hide_safe = not (domain == 'SURFACE' and fast)
        self.inputs['Initial Samples'].hide_safe = not (precise and domain == 'CURVE')
        self.inputs['Initial Samples U'].hide_safe = not (precise and domain == 'SURFACE')
        self.inputs['Initial Samples V'].hide_safe = not (precise and domain == 'SURFACE')
        self.inputs['Deflection'].hide_safe = not (domain == 'SOLID' and fast)

    def _update_domain(self, context):
        self._ensure_domain_sockets()
        updateNode(self, context)

    collision_domain: EnumProperty(
        name='Domain', description='External stationary obstacle geometry',
        items=[('VERTS','Vertices','Static point obstacles'),
               ('EDGES','Edges','Static segment obstacles'),
               ('POLYGONS','Polygons','Original BVH mesh surface obstacles'),
               ('CURVE','Curve','External parametric curves'),
               ('SURFACE','Surface','External parametric surfaces'),
               ('SOLID','Solid','External FreeCAD solids')],
        default='POLYGONS', update=_update_domain)
    method: EnumProperty(name='Method', default='FAST', update=_update_domain,
        description='Fast discretization or slower parametric nearest point',
        items=[('FAST', 'Fast', 'Cached polyline / tessellated BVH'),
               ('PRECISE', 'Precise', 'Numerical or FreeCAD geometric nearest point')])
    resolution: IntProperty(name='Resolution', default=50, min=2, update=updateNode)
    resolution_u: IntProperty(name='Resolution U', default=25, min=2, update=updateNode)
    resolution_v: IntProperty(name='Resolution V', default=25, min=2, update=updateNode)
    init_samples: IntProperty(name='Initial Samples', default=15, min=3, update=updateNode)
    init_samples_u: IntProperty(name='Initial Samples U', default=15, min=3, update=updateNode)
    init_samples_v: IntProperty(name='Initial Samples V', default=15, min=3, update=updateNode)
    deflection: FloatProperty(name='Deflection', default=0.1, min=0.000001,
                              description='Absolute FreeCAD tessellation deflection', update=updateNode)

    thickness: FloatProperty(name='Thickness', min=0.0, default=0.0,
                             description='Added to particle radius', update=updateNode)
    engine: EnumProperty(name='Engine', default='AUTO', update=updateNode,
        items=[('AUTO','Auto','Prefer SciPy for points and Numba for edges'),
               ('NUMPY','NumPy','Reference numeric implementation'),
               ('NUMBA','Numba','Compiled edge queries when available')])

    magnitude: FloatProperty(
        name='Magnitude', description='Drag Force Constant',
        default=0.0, precision=3, update=updateNode)

    absorption: FloatProperty(
        name='Absorption', description='Obstacles Velocity and acceleration absortion. 0 = hard surface, 1 = soft surface',
        default=0.1, update=updateNode)


    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvStringsSocket', "Pols")
        self.inputs.new('SvStringsSocket', "Absorption").prop_name = 'absorption'

        self.outputs.new('SvPulgaForceSocket', "Force")
        self._ensure_domain_sockets()

    def draw_buttons(self, context, layout):
        layout.prop(self, 'collision_domain', text='')
        if self.collision_domain in {'CURVE','SURFACE','SOLID'}:
            layout.prop(self, 'method', text='')

    def draw_buttons_ext(self, context, layout):
        if self.collision_domain in {'VERTS', 'EDGES', 'CURVE'} and (
        self.collision_domain != 'CURVE' or self.method == 'FAST'):
            layout.prop(self, 'engine')
            if not HAS_NUMBA:
                layout.label(text='Numba not available', icon='INFO')

    def process(self):

        if not any(s.is_linked for s in self.outputs):
            return
        self._ensure_domain_sockets()
        if self.collision_domain in {'CURVE', 'SURFACE', 'SOLID'}:
            domain = self.collision_domain
            if domain == 'SOLID' and FreeCAD is None:
                raise ImportError('Install FreeCAD to use Solid obstacles')
            socket = {'CURVE': 'Curve', 'SURFACE': 'Surface', 'SOLID': 'Solid'}[domain]
            geometry_data = self.inputs[socket].sv_get(deepcopy=False)
            if domain == 'CURVE':
                geometry_type = SvCurve
            elif domain == 'SURFACE':
                geometry_type = SvSurface
            else:
                import Part
                geometry_type = Part.Shape
            # One force per top-level group; one group may contain several obstacles.
            if isinstance(geometry_data, geometry_type):
                geom_groups = [[geometry_data]]
            elif isinstance(geometry_data, (list, tuple)) and all(
                    isinstance(g, geometry_type) for g in geometry_data):
                geom_groups = [list(geometry_data)]
            else:
                geom_groups = [list(g) if isinstance(g, (list, tuple)) else [g]
                               for g in geometry_data]
            strength_data = self.inputs['Absorption'].sv_get(deepcopy=False)
            thickness_data = self.inputs['Thickness'].sv_get(deepcopy=False)
            resolution_data = self.inputs['Resolution'].sv_get(deepcopy=False)
            res_u_data = self.inputs['Resolution U'].sv_get(deepcopy=False)
            res_v_data = self.inputs['Resolution V'].sv_get(deepcopy=False)
            samples_data = self.inputs['Initial Samples'].sv_get(deepcopy=False)
            samples_u_data = self.inputs['Initial Samples U'].sv_get(deepcopy=False)
            samples_v_data = self.inputs['Initial Samples V'].sv_get(deepcopy=False)
            deflection_data = self.inputs['Deflection'].sv_get(deepcopy=False)
            forces = []
            for group, absorption, thick, resolution, ru, rv, samples, deflection, su, sv in zip_long_repeat(
                    geom_groups, strength_data, thickness_data, resolution_data,
                    res_u_data, res_v_data, samples_data, deflection_data,
                    samples_u_data, samples_v_data):
                forces.append(SvParametricObstacleForce(
                    group, domain, self.method, absorption, thick,
                    resolution, ru, rv, samples, deflection, self.engine,
                    init_samples_u=su, init_samples_v=sv))
            self.outputs['Force'].sv_set([forces])
            return
        if self.collision_domain != 'POLYGONS':
            verts_data = self.inputs['Vertices'].sv_get(deepcopy=False)
            edges_data = (self.inputs['Edges'].sv_get(deepcopy=False)
                          if self.collision_domain == 'EDGES' else [[]])
            absorption_data = self.inputs['Absorption'].sv_get(deepcopy=False)
            thickness_data = self.inputs['Thickness'].sv_get(deepcopy=False)
            forces = [SvStaticPointEdgeObstacleForce(v, e, a, t, self.collision_domain, self.engine)
                      for v, e, a, t in zip_long_repeat(
                          verts_data, edges_data, absorption_data, thickness_data)]
            self.outputs['Force'].sv_set([forces])
            return
        magnitude = self.inputs["Vertices"].sv_get(deepcopy=False)
        pols = self.inputs["Pols"].sv_get(deepcopy=False)
        absorption = self.inputs["Absorption"].sv_get(deepcopy=False)

        forces_out = []

        forces_out = []
        for force in zip_long_repeat(magnitude, pols, absorption):
            forces_out.append(SvObstaclesBVHForce(*force))



        self.outputs[0].sv_set([forces_out])




def register():
    bpy.utils.register_class(SvPulgaObstacleForceNode)


def unregister():
    bpy.utils.unregister_class(SvPulgaObstacleForceNode)
