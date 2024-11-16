# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from bpy.props import EnumProperty, BoolProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, map_recursive
from sverchok.utils.math import coordinate_modes
from sverchok.utils.field.vector import SvVectorField
from sverchok.utils.field.vector_operations import (
        SvVectorFieldCartesianFilter,
        SvVectorFieldCylindricalFilter,
        SvVectorFieldSphericalFilter)

class SvVectorFieldFilterNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Filter Vector Field
    Tooltip: Restrict vector field action by cartesian, cylindrical or spherical coordinates
    """
    bl_idname = 'SvVectorFieldFilterNode'
    bl_label = 'Vector Field Filter'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_EX_ATTRACT'

    coordinates : EnumProperty(
            name = "Coordinates",
            items = coordinate_modes,
            default = 'XYZ',
            update = updateNode)

    use_x : BoolProperty(
            name = "X",
            default = True,
            update = updateNode)

    use_y : BoolProperty(
            name = "Y",
            default = True,
            update = updateNode)

    use_z : BoolProperty(
            name = "Z",
            default = True,
            update = updateNode)

    use_rho : BoolProperty(
            name = "Rho",
            default = True,
            update = updateNode)

    use_phi : BoolProperty(
            name = "Phi",
            default = True,
            update = updateNode)

    use_theta : BoolProperty(
            name = "Theta",
            default = True,
            update = updateNode)

    def draw_buttons(self, context, layout):
        layout.label(text="Coordinates:")
        layout.prop(self, 'coordinates', text='')
        layout.label(text="Use:")
        r = layout.row(align=True)
        if self.coordinates == 'XYZ':
            r.prop(self, 'use_x', toggle=True)
            r.prop(self, 'use_y', toggle=True)
            r.prop(self, 'use_z', toggle=True)
        elif self.coordinates == 'CYL':
            r.prop(self, 'use_rho', toggle=True)
            r.prop(self, 'use_phi', toggle=True)
            r.prop(self, 'use_z', toggle=True)
        else:
            r.prop(self, 'use_rho', toggle=True)
            r.prop(self, 'use_phi', toggle=True)
            r.prop(self, 'use_theta', toggle=True)

    def sv_init(self, context):
        self.inputs.new('SvVectorFieldSocket', 'Field')
        self.outputs.new('SvVectorFieldSocket', 'Field')

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        fields_s = self.inputs['Field'].sv_get()

        def do_filter(field):
            if self.coordinates == 'XYZ':
                return SvVectorFieldCartesianFilter(field, self.use_x, self.use_y, self.use_z)
            elif self.coordinates == 'CYL':
                return SvVectorFieldCylindricalFilter(field, self.use_rho, self.use_phi, self.use_z)
            else:
                return SvVectorFieldSphericalFilter(field, self.use_rho, self.use_phi, self.use_theta)

        fields_out = map_recursive(do_filter, fields_s, data_types=(SvVectorField,))
        self.outputs['Field'].sv_set(fields_out)

def register():
    bpy.utils.register_class(SvVectorFieldFilterNode)

def unregister():
    bpy.utils.unregister_class(SvVectorFieldFilterNode)


