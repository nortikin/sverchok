# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from bpy.props import EnumProperty, BoolProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok.utils.nurbs_common import SvNurbsMaths
from sverchok.utils.surface.core import SvSurface, UnsupportedSurfaceTypeException, SurfaceSide
from sverchok.utils.surface.nurbs import SvNurbsSurface
from sverchok.utils.surface.nurbs_solver import snap_nurbs_surfaces, SnapSurfaceBias, SnapSurfaceTangents, SnapSurfaceInput

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

    directions = [
            (SvNurbsSurface.U, "U", "U direction", 0),
            (SvNurbsSurface.V, "V", "V direction", 1)
        ]

    sides = [
            (SurfaceSide.MIN.name, "Minimum", "Minimum value of surface parameter", 0),
            (SurfaceSide.MAX.name, "Maximum", "Maximum value of surface parameter", 1)
        ]

    direction1 : EnumProperty(
            name = "Direction",
            description = "Direction of the first surface",
            items = directions,
            update = updateNode)

    direction2 : EnumProperty(
            name = "Direction",
            description = "Direction of the second surface",
            items = directions,
            update = updateNode)

    side1 : EnumProperty(
            name = "Side",
            items = sides,
            update = updateNode)

    side2 : EnumProperty(
            name = "Side",
            items = sides,
            update = updateNode)

    invert1 : BoolProperty(
            name = "Invert tangents",
            default = False,
            update = updateNode)

    invert2 : BoolProperty(
            name = "Invert tangents",
            default = False,
            update = updateNode)

    bias : EnumProperty(
            name = "Bias",
            items = bias_modes,
            update = updateNode)

    tangent : EnumProperty(
            name = "Tangents",
            items = tangent_modes,
            update = updateNode)

    def draw_surface_in_socket(self, socket, context, layout):
        if socket.name == 'Surface1':
            direction_name = 'direction1'
            side_name = 'side1'
            invert_name = 'invert1'
        else:
            direction_name = 'direction2'
            side_name = 'side2'
            invert_name = 'invert2'
        row = layout.row()
        row.prop(self, direction_name, text='')
        row.prop(self, side_name, text='')
        row.prop(self, invert_name, text='')

    def sv_init(self, context):
        self.inputs.new('SvSurfaceSocket', "Surface1").custom_draw = 'draw_surface_in_socket'
        self.inputs.new('SvSurfaceSocket', "Surface2").custom_draw = 'draw_surface_in_socket'
        self.outputs.new('SvSurfaceSocket', "Surface1")
        self.outputs.new('SvSurfaceSocket', "Surface2")
        #self.update_sockets(context)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'bias')
        layout.prop(self, 'tangent')

    def _process(self, surface1, surface2):
        surface1 = SvNurbsMaths.to_nurbs_surface(surface1)
        if surface1 is None:
            raise UnsupportedSurfaceTypeException("First surface is not NURBS")
        surface2 = SvNurbsMaths.to_nurbs_surface(surface2)
        if surface2 is None:
            raise UnsupportedSurfaceTypeException("Second surface is not NURBS")
        input1 = SnapSurfaceInput(surface1, self.direction1, SurfaceSide[self.side1], invert_tangents = self.invert1)
        input2 = SnapSurfaceInput(surface2, self.direction2, SurfaceSide[self.side2], invert_tangents = self.invert2)
        return snap_nurbs_surfaces(input1, input2,
                                   SnapSurfaceBias[self.bias],
                                   SnapSurfaceTangents[self.tangent],
                                   logger = self.sv_logger)

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        surface1_in = self.inputs['Surface1'].sv_get()
        surface2_in = self.inputs['Surface2'].sv_get()

        level1 = get_data_nesting_level(surface1_in, data_types=(SvSurface,))
        level2 = get_data_nesting_level(surface2_in, data_types=(SvSurface,))
        flat_output = max(level1, level2) < 2

        surface1_in = ensure_nesting_level(surface1_in, 2, data_types=(SvSurface,))
        surface2_in = ensure_nesting_level(surface2_in, 2, data_types=(SvSurface,))

        surface1_out = []
        surface2_out = []
        for params in zip_long_repeat(surface1_in, surface2_in):
            new_surface1 = []
            new_surface2 = []
            for surface1, surface2 in zip_long_repeat(*params):
                r_surface1, r_surface2 = self._process(surface1, surface2)
                new_surface1.append(r_surface1)
                new_surface2.append(r_surface2)
            if flat_output:
                surface1_out.extend(new_surface1)
                surface2_out.extend(new_surface2)
            else:
                surface1_out.append(new_surface1)
                surface2_out.append(new_surface2)

        self.outputs['Surface1'].sv_set(surface1_out)
        self.outputs['Surface2'].sv_set(surface2_out)

def register():
    bpy.utils.register_class(SvSnapSurfacesNode)

def unregister():
    bpy.utils.unregister_class(SvSnapSurfacesNode)

