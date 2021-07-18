# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level, repeat_last_for_length
from sverchok.utils.surface import SvSurface
from sverchok.utils.surface.nurbs import SvNurbsSurface
from sverchok.utils.surface.algorithms import remove_excessive_knots

class SvSurfaceRemoveExcessiveKnotsNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Remove Excessive Knots
    Tooltip: Remove a knot from a NURBS surface
    """
    bl_idname = 'SvSurfaceRemoveExcessiveKnotsNode'
    bl_label = 'Remove Excessive Knots (NURBS Surface)'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_SURFACE_CLEAN_KNOTS'

    directions = [
            ('UV', "U+V", "Both U and V directions", 0),
            ('U', "U", "U direction", 1),
            ('V', "V", "V direction", 2)
        ]

    direction : EnumProperty(
            name = "Parameter",
            description = "From which parameter direction to remove knots",
            items = directions,
            default = 'UV',
            update = updateNode)

    tolerance : FloatProperty(
            name = "Tolerance",
            default = 1e-6,
            precision = 8,
            min = 0,
            update = updateNode)
        
    def sv_init(self, context):
        self.inputs.new('SvSurfaceSocket', "Surface")
        self.outputs.new('SvSurfaceSocket', "Surface")

    def draw_buttons(self, context, layout):
        layout.prop(self, 'direction', expand=True)

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, 'tolerance')

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        surface_s = self.inputs['Surface'].sv_get()

        input_level = get_data_nesting_level(surface_s, data_types=(SvSurface,))
        flat_output = input_level < 2
        surface_s = ensure_nesting_level(surface_s, 2, data_types=(SvSurface,))

        tolerance = self.tolerance

        surfaces_out = []
        for surfaces in surface_s:
            new_surfaces = []
            for surface in surfaces:
                surface = SvNurbsSurface.get(surface)
                if surface is None:
                    raise Exception("One of surfaces is not NURBS")
                surface = remove_excessive_knots(surface, self.direction, tolerance=tolerance)
                new_surfaces.append(surface)
            if flat_output:
                surfaces_out.extend(new_surfaces)
            else:
                surfaces_out.append(new_surfaces)

        self.outputs['Surface'].sv_set(surfaces_out)

def register():
    bpy.utils.register_class(SvSurfaceRemoveExcessiveKnotsNode)

def unregister():
    bpy.utils.unregister_class(SvSurfaceRemoveExcessiveKnotsNode)



