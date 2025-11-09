# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from bpy.props import EnumProperty, FloatVectorProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import ensure_nesting_level, get_data_nesting_level, zip_long_repeat, updateNode
from sverchok.utils.geom import PlaneEquation
from sverchok.utils.solid import symmetrize_solid
from sverchok.dependencies import FreeCAD

if FreeCAD is not None:
    from Part import Shape

class SvSymmetrizeSolidNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Symmetrize Solid
    Tooltip: Make a symmetric Solid object
    """
    bl_idname = 'SvSymmetrizeSolidNode'
    bl_label = "Symmetrize Solid"
    bl_icon = 'MOD_MIRROR'
    sv_category = "Solid Operators"
    sv_dependencies = {'FreeCAD'}

    directions = [
        ('X+', "-X to +X", "-X to +X", 0),
        ('X-', "+X to -X", "+X to -X", 1),
        ('Y+', "-Y to +Y", "-Y to +Y", 2),
        ('Y-', "+Y to -Y", "+Y to -Y", 3),
        ('Z+', "-Z to +Z", "-Z to +Z", 4),
        ('Z-', "+Z to -Z", "+Z to -Z", 5),
        ('CUSTOM', "Custom", "Custom", 6)
    ]

    def update_sockets(self, context):
        self.inputs['Point'].hide_safe = self.direction != 'CUSTOM'
        self.inputs['Normal'].hide_safe = self.direction != 'CUSTOM'

    direction : EnumProperty(
            name = "Direction",
            description = "Which sides to copy from and to",
            items = directions,
            default = "X+",
            update = update_sockets)

    plane_point : FloatVectorProperty(
            name = "Point",
            description = "Point on plane",
            default = (0.0, 0.0, 0.0),
            precision = 3,
            update = updateNode)

    plane_normal : FloatVectorProperty(
            name = "Normal",
            description = "Plane normal",
            default = (0.0, 0.0, 1.0),
            precision = 3,
            update = updateNode)

    def draw_buttons(self, context, layout):
        layout.label(text='Direction:')
        layout.prop(self, "direction", text='')

    def sv_init(self, context):
        self.inputs.new('SvSolidSocket', "Solid")
        self.inputs.new('SvVerticesSocket', "Point").prop_name = 'plane_point'
        self.inputs.new('SvVerticesSocket', "Normal").prop_name = 'plane_normal'
        self.outputs.new('SvSolidSocket', "Solid")
        self.update_sockets(context)

    def _get_plane(self, point, normal):
        if self.direction in ['X+','X-']:
            normal = (1,0,0)
            point = (0,0,0)
        elif self.direction in ['Y+', 'Y-']:
            normal = (0,1,0)
            point = (0,0,0)
        elif self.direction in ['Z+', 'Z-']:
            normal = (0,0,1)
            point = (0,0,0)

        if self.direction in ['X+', 'Y+', 'Z+', 'CUSTOM']:
            sign = -1
        else:
            sign = 1

        plane = PlaneEquation.from_normal_and_point(normal, point)
        return plane, sign

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        solids_s = self.inputs['Solid'].sv_get()
        point_s = self.inputs['Point'].sv_get()
        normal_s = self.inputs['Normal'].sv_get()

        input_level = get_data_nesting_level(solids_s, data_types=(Shape,))
        flat_output = input_level < 2
        solids_s = ensure_nesting_level(solids_s, 2, data_types=(Shape,))
        point_s = ensure_nesting_level(point_s, 3)
        normal_s = ensure_nesting_level(normal_s, 3)

        solids_out = []
        for params in zip_long_repeat(solids_s, point_s, normal_s):
            new_solids = []
            for solid, point, normal in zip_long_repeat(*params):
                plane, sign = self._get_plane(point, normal)
                solids = symmetrize_solid(solid, plane, sign)
                new_solids.append(solids)
            if flat_output:
                solids_out.extend(new_solids)
            else:
                solids_out.append(new_solids)

        self.outputs['Solid'].sv_set(solids_out)

def register():
    bpy.utils.register_class(SvSymmetrizeSolidNode)

def unregister():
    bpy.utils.unregister_class(SvSymmetrizeSolidNode)

