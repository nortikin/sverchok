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
from bpy.props import EnumProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from numpy import array, degrees, sqrt, arctan2, linalg
from sverchok.utils.modules.vector_math_utils import angle_between


def numpy_cartesian_to_polar(vs, coordinates, angles_mode, out_numpy):
    vecs = array(vs)
    x = vecs[:, 0]
    y = vecs[:, 1]
    z = vecs[:, 2]
    if coordinates == 'z':
        rho = sqrt(x*x + y*y)
        if angles_mode == "degrees":
            phi = degrees(arctan2(y, x))
        else:
            phi = arctan2(y, x)

    else:
        rho = linalg.norm(vecs, axis=1)
        if angles_mode == "degrees":
            phi = degrees(arctan2(y, x))
            z = degrees(angle_between(vecs, [[0, 0, 1]]))
        else:
            phi = arctan2(y, x)
            z = angle_between(vecs, [[0, 0, 1]])

    return [rho, phi, z] if out_numpy else [rho.tolist(), phi.tolist(), z.tolist()]

class VectorPolarOutNode(bpy.types.Node, SverchCustomTreeNode):
    '''Get cylindrical or spherical coordinates from vectors'''
    bl_idname = 'VectorPolarOutNode'
    bl_label = 'Vector polar output'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_VECTOR_POLAR_OUT'



    coord_modes = [
        ("z", "Cylinder", "Use cylindrical coordinates", 1),
        ("theta", "Sphere", "Use spherical coordinates", 2),
    ]

    angle_modes = [
        ("radians", "Radian", "Use angles in radians", 1),
        ("degrees", "Degree", "Use angles in degrees", 2)
    ]

    def coordinate_changed(self, context):
        # changing name of third output socket
        replaceable_socket = self.outputs[2]
        mode_name = self.coordinates

        if mode_name in ['z', 'theta']:
            replaceable_socket.replace_socket('SvStringsSocket', new_name=mode_name)
        else:
            raise Exception("Unexpected mode - {}".format(mode_name))

    coordinates: EnumProperty(items=coord_modes, default='z', update=coordinate_changed)
    angles_mode: EnumProperty(items=angle_modes, default="radians", update=updateNode)

    implementation_modes = [
        ("NumPy", "NumPy", "NumPy", 0),
        ("Python", "Python", "Python", 1)]

    output_numpy: BoolProperty(
        name='Output NumPy',
        description='Output NumPy arrays',
        default=False, update=updateNode)

    def sv_init(self, context):
        self.inputs.new("SvVerticesSocket", "Vectors")
        self.width = 100
        self.outputs.new('SvStringsSocket', "rho")
        self.outputs.new('SvStringsSocket', "phi")
        self.outputs.new('SvStringsSocket', "z")

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

        if not self.inputs[0].is_linked and (any(s.is_linked for s in self.outputs)):
            return
        vss = self.inputs['Vectors'].sv_get(deepcopy=False)

        result_rhos = []
        result_phis = []
        result_zs = []
        for vs in vss:
            rhos, phis, zs = numpy_cartesian_to_polar(vs, self.coordinates, self.angles_mode, self.output_numpy)

            result_rhos.append(rhos)
            result_phis.append(phis)
            result_zs.append(zs)

        if self.outputs['rho'].is_linked:
            self.outputs['rho'].sv_set(result_rhos)
        if self.outputs['phi'].is_linked:
            self.outputs['phi'].sv_set(result_phis)
        if self.outputs[self.coordinates].is_linked:
            self.outputs[self.coordinates].sv_set(result_zs)

def register():
    bpy.utils.register_class(VectorPolarOutNode)


def unregister():
    bpy.utils.unregister_class(VectorPolarOutNode)
