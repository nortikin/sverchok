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
from bpy.props import FloatProperty, EnumProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat, numpy_match_long_repeat
from numpy import array, sin, cos, radians

def numpy_polar_to_cartesian(ps, coordinates, angles_mode, out_numpy):

    u_rho, u_phi, u_z = [array(p) for p in ps]

    if coordinates == 'theta_':
        if angles_mode == 'degrees':
            ang1 = radians(u_phi)
            ang2 = radians(u_z)
        else:
            ang1 = u_phi
            ang2 = u_z
        rho, phi, theta = numpy_match_long_repeat([u_rho, ang1, ang2])

        cartesian = array([
            rho * cos(phi) * sin(theta),
            rho * sin(phi) * sin(theta),
            rho * cos(theta)
            ]).T
    else:
        if angles_mode == 'degrees':
            ang1 = radians(u_phi)
        else:
            ang1 = u_phi
        rho, phi, z = numpy_match_long_repeat([u_rho, ang1, u_z])
        
        cartesian = array([rho * cos(phi), rho * sin(phi), z]).T

    return cartesian if out_numpy else cartesian.tolist()


class VectorPolarInNode(bpy.types.Node, SverchCustomTreeNode):
    '''Generate vectors by spherical or cylindrical coordinates'''
    bl_idname = 'VectorPolarInNode'
    bl_label = 'Vector polar input'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_VECTOR_POLAR_IN'


    rho_: FloatProperty(
        name='rho', description='Rho coordinate', default=0.0, precision=3, update=updateNode)

    phi_: FloatProperty(
        name='phi', description='Phi coordinate', default=0.0, precision=3, update=updateNode)

    theta_: FloatProperty(
        name='theta', description='Theta coordinate', default=0.0, precision=3, update=updateNode)

    z_: FloatProperty(
        name='Z', description='Z coordinate', default=0.0, precision=3, update=updateNode)

    coord_modes = [
        ("z_", "Cylinder", "Use cylindrical coordinates", 1),
        ("theta_", "Sphere", "Use spherical coordinates", 2),
    ]


    output_numpy: BoolProperty(
        name='Output NumPy',
        description='Output NumPy arrays',
        default=False, update=updateNode)

    def coordinate_changed(self, context):
        self.inputs[2].prop_name = self.coordinates
        updateNode(self, context)

    coordinates: EnumProperty(items=coord_modes, default='z_', update=coordinate_changed)



    angle_modes = [
        ("radians", "Radian", "Use angles in radians", 1),
        ("degrees", "Degree", "Use angles in degrees", 2)
        ]

    angles_mode: EnumProperty(items=angle_modes, default="radians", update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "rho").prop_name = 'rho_'
        self.inputs.new('SvStringsSocket', "phi").prop_name = 'phi_'
        self.inputs.new('SvStringsSocket', "Z").prop_name = 'z_'
        self.width = 100
        self.outputs.new('SvVerticesSocket', "Vectors")

    def draw_buttons(self, context, layout):
        layout.prop(self, "coordinates", expand=True)
        layout.prop(self, "angles_mode", expand=True)

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, "coordinates", expand=True)
        layout.prop(self, "angles_mode", expand=True)
        layout.prop(self, "output_numpy", toggle=False)

    def rclick_menu(self, context, layout):
        layout.prop_menu_enum(self, "coordinates", text="Polar system")
        layout.prop_menu_enum(self, "angles_mode", text="Angle Units")
        layout.prop(self, "output_numpy", toggle=True)

    def process(self):
        if not self.outputs['Vectors'].is_linked:
            return
        inputs = self.inputs
        rhoss = inputs['rho'].sv_get()
        phiss = inputs['phi'].sv_get()
        zss = inputs['Z'].sv_get()

        parameters = match_long_repeat([rhoss, phiss, zss])
        result = []

        for ps in zip(*parameters):
            vs = numpy_polar_to_cartesian(ps, self.coordinates, self.angles_mode, self.output_numpy)
            result.append(vs)

        self.outputs['Vectors'].sv_set(result)


def register():
    bpy.utils.register_class(VectorPolarInNode)


def unregister():
    bpy.utils.unregister_class(VectorPolarInNode)
