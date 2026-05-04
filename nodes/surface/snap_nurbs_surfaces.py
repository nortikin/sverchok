# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from bpy.props import EnumProperty, BoolProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level, zip_long_repeat_recursive
from sverchok.utils.surface.core import SvSurface, UnsupportedSurfaceTypeException
from sverchok.utils.surface.nurbs import SvNurbsSurface
from sverchok.utils.surface.nurbs_solver import snap_nurbs_surfaces, SnapSurfaceBias, SnapSurfaceTangents

class SvSnapSurfacesNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Snap NURBS Surfraces
    Tooltip: Snap borders of NURBS surfaces to common curve, optionally controlling surface tangents
    """
    bl_idname = 'SvSnapSurfacesNode'
    bl_label = 'Snap NURBS Surfaces'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_SNAP_CURVES'

    bias_modes = [
            (SnapSurfaceBias.MID.name, "Middle line", "Snap to middle line between border of first surface and border of second surface", 0),
            (SnapSurfaceBias.SURFACE1.name, "Surface 1", "Snap border of the second surface to the border of the first surface", 1),
            (SnapSurfaceBias.SURFACE2.name, "Surface 2", "Snap border of the first surface to the border of the second surface", 2)
        ]

    tangent_modes = [
            (SnapSurfaceTangents.ANY.name, "No matter", "Tangents will probably change", 0),
            (SnapSurfaceTangents.PRESERVE.name, "Preserve", "Preserve tangent vectors of both surfaces", 1),
            (SnapSurfaceTangents.MATCH.name, "Medium", "Adjust tangent vectors of surfaces so that they will be average between end tangent of the first surface and start tangent of the second surface", 2),
            (SnapSurfaceTangents.SURFACE1.name, "Surface 1", "Preserve tangent vector of the first surface at it's end, and adjust the tangent vector of the second surface to match", 3),
            (SnapSurfaceTangents.SURFACE2.name, "Surface 2", "Preserve tangent vector of the second surface at it's end, and adjust the tangent vector of the first surface to match", 4)
        ]

    input_modes = [
        ('TWO', "Two surfaces", "Process two surfaces", 0),
        ('N', "List of surfaces", "Process several surfaces", 1)
    ]

    def update_sockets(self, context):
        self.inputs['Surface1'].hide_safe = self.input_mode != 'TWO'
        self.inputs['Surface2'].hide_safe = self.input_mode != 'TWO'
        self.inputs['Surfaces'].hide_safe = self.input_mode != 'N'
        updateNode(self, context)

    input_mode : EnumProperty(
        name = "Input mode",
        items = input_modes,
        default = 'TWO',
        update = update_sockets)

    directions = [
            (SvNurbsSurface.U, "U", "U direction", 0),
            (SvNurbsSurface.V, "V", "V direction", 1)
        ]

    direction : EnumProperty(
            name = "Direction",
            description = "Direction of concatenation",
            items = directions,
            update = updateNode)

    bias : EnumProperty(
            name = "Bias",
            items = bias_modes,
            update = updateNode)

    tangent : EnumProperty(
            name = "Tangents",
            items = tangent_modes,
            update = updateNode)

    is_cyclic : BoolProperty(
            name = "Cyclic",
            default = False,
            update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvSurfaceSocket', "Surface1")
        self.inputs.new('SvSurfaceSocket', "Surface2")
        self.inputs.new('SvSurfaceSocket', "Surfaces")
        self.outputs.new('SvSurfaceSocket', "Surfaces")
        self.update_sockets(context)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'input_mode', text='')
        layout.prop(self, 'direction', expand=True)
        layout.label(text="Bias:")
        layout.prop(self, 'bias', text='')
        layout.label(text="Tangents:")
        layout.prop(self, 'tangent', text='')
        layout.prop(self, 'is_cyclic')

    def _process(self, surfaces):
        surfaces = [SvNurbsSurface.get(s) for s in surfaces]
        if any(s is None for s in surfaces):
            raise UnsupportedSurfaceTypeException("Surface is not NURBS")
        return snap_nurbs_surfaces(surfaces,
                                   direction = self.direction,
                                   bias = SnapSurfaceBias[self.bias],
                                   tangents = SnapSurfaceTangents[self.tangent],
                                   cyclic = self.is_cyclic,
                                   logger = self.sv_logger)

    def get_inputs(self):
        surfaces_s = []
        if self.input_mode == 'TWO':
            surface1_s = self.inputs['Surface1'].sv_get()
            surface2_s = self.inputs['Surface2'].sv_get()
            level1 = get_data_nesting_level(surface1_s, data_types=(SvSurface,))
            level2 = get_data_nesting_level(surface2_s, data_types=(SvSurface,))
            nested_input = level1 > 2 or level2 > 2
            surface1_s = ensure_nesting_level(surface1_s, 3, data_types=(SvSurface,))
            surface2_s = ensure_nesting_level(surface2_s, 3, data_types=(SvSurface,))
            surfaces_s = zip_long_repeat_recursive(3, surface1_s, surface2_s)
        else:
            surfaces_s = self.inputs['Surfaces'].sv_get()
            level = get_data_nesting_level(surfaces_s, data_types=(SvSurface,))
            nested_input = level > 2
            surfaces_s = ensure_nesting_level(surfaces_s, 3, data_types=(SvSurface,))
        return nested_input, surfaces_s

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        nested_input, surfaces_in = self.get_inputs()
        flat_output = not nested_input

        surfaces_out = []
        for params in surfaces_in:
            new_surfaces = []
            for surfaces in params:
                r_surfaces = self._process(surfaces)
                new_surfaces.append(r_surfaces)
            if flat_output:
                surfaces_out.extend(new_surfaces)
            else:
                surfaces_out.append(new_surfaces)

        self.outputs['Surfaces'].sv_set(surfaces_out)

def register():
    bpy.utils.register_class(SvSnapSurfacesNode)

def unregister():
    bpy.utils.unregister_class(SvSnapSurfacesNode)

