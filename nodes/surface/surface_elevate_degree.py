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

class SvSurfaceElevateDegreeNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Elevate Surface Degree
    Tooltip: Elevate degree of a NURBS surface
    """
    bl_idname = 'SvSurfaceElevateDegreeNode'
    bl_label = 'Elevate Degree (NURBS Surface)'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_ELEVATE_SURFACE_DEGREE'

    directions = [
            ('U', "U", "U direction", 0),
            ('V', "V", "V direction", 1)
        ]

    direction : EnumProperty(
            name = "Parameter",
            description = "By which parameter to elevate degree",
            items = directions,
            default = 'U',
            update = updateNode)

    modes = [
            ('DELTA', "Elevate by", "Specify difference between current degree and target degree", 0),
            ('TARGET', "Set degree", "Specify target degree", 1)
        ]

    def update_sockets(self, context):
        self.inputs['Degree'].label = "Delta" if self.mode == 'DELTA' else "Degree"
        updateNode(self, context)

    mode : EnumProperty(
            name = "Mode",
            description = "How new curve degree is specified",
            items = modes,
            update = update_sockets)

    degree : IntProperty(
            name = "Degree",
            description = "Target degree or degree delta",
            min = 0,
            default = 1,
            update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'direction', expand=True)
        layout.prop(self, 'mode', text='')

    def sv_init(self, context):
        self.inputs.new('SvSurfaceSocket', "Surface")
        self.inputs.new('SvStringsSocket', 'Degree').prop_name = 'degree'
        self.outputs.new('SvSurfaceSocket', "Surface")
        self.update_sockets(context)

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        surface_s = self.inputs['Surface'].sv_get()
        degree_s = self.inputs['Degree'].sv_get()

        input_level = get_data_nesting_level(surface_s, data_types=(SvSurface,))
        flat_output = input_level < 2
        surface_s = ensure_nesting_level(surface_s, 2, data_types=(SvSurface,))
        degree_s = ensure_nesting_level(degree_s, 2)

        surfaces_out = []
        for params in zip_long_repeat(surface_s, degree_s):
            new_surfaces = []
            for surface, degree in zip_long_repeat(*params):
                surface = SvNurbsSurface.get(surface)
                if surface is None:
                    raise Exception("One of surfaces is not NURBS")
                if self.mode == 'DELTA':
                    kwargs = dict(delta = degree)
                else:
                    kwargs = dict(target = degree)
                surface = surface.elevate_degree(self.direction, **kwargs)
                new_surfaces.append(surface)
            if flat_output:
                surfaces_out.extend(new_surfaces)
            else:
                surfaces_out.append(new_surfaces)

        self.outputs['Surface'].sv_set(surfaces_out)

def register():
    bpy.utils.register_class(SvSurfaceElevateDegreeNode)

def unregister():
    bpy.utils.unregister_class(SvSurfaceElevateDegreeNode)

