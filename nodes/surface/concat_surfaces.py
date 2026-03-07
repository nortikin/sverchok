# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from bpy.props import EnumProperty, BoolProperty, IntProperty, FloatProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level, zip_long_repeat_recursive
from sverchok.utils.surface.core import SvSurface, UnsupportedSurfaceTypeException, other_direction
from sverchok.utils.surface.nurbs import SvNurbsSurface
from sverchok.utils.surface.algorithms import concatenate_surfaces, unify_nurbs_surfaces, check_surface_edges_coincidence

class SvConcatSurfacesNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Concatenate Surfraces
    Tooltip: Concatenate several surfaces into one
    """
    bl_idname = 'SvConcatSurfacesNode'
    bl_label = 'Concatenate Surfaces'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_CONCAT_CURVES'

    all_nurbs : BoolProperty(
        name = "All NURBS",
        description = "Convert all input curves to NURBS, and output NURBS - or fail if it is not possible",
        default = False,
        update = updateNode)

    input_modes = [
        ('TWO', "Two surfaces", "Process two curves", 0),
        ('N', "List of surfaces", "Process several curves", 1)
    ]

    nurbs_modes = [
        ('GENERIC', "Generic", "Create a generic Surface object", 0),
        ('NURBS', "Always NURBS", "Create a NURBS surface from NURBS curves. Fail if it is not possible to generate a NURBS surface", 1),
        ('NURBS_IF_POSSIBLE', "NURBS if possible",  "Try to create a NURBS surface from NURBS curves. If it is not possible, create a generic Surface object", 2)
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

    use_nurbs : EnumProperty(
        name = "NURBS option",
        description = "Whether to generate a NURBS or generic surface",
        items = nurbs_modes,
        default = 'NURBS_IF_POSSIBLE',
        update = updateNode)

    unify : BoolProperty(
            name = "Unify surfaces",
            default = True,
            update = updateNode)

    knotvector_accuracy : IntProperty(
        name = "Knotvector accuracy",
        default = 4,
        min = 1, max = 10,
        update = updateNode)

    check_edges : BoolProperty(
        name = "Check edges coincidence",
        default = False,
        update = updateNode)

    check_edges_pts : IntProperty(
        name = "Number of points to check",
        default = 10,
        update = updateNode)

    check_edges_tolerance : FloatProperty(
        name = "Tolerance",
        default = 1e-6,
        min = 0,
        precision = 8,
        update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvSurfaceSocket', "Surfaces")
        self.inputs.new('SvSurfaceSocket', "Surface1")
        self.inputs.new('SvSurfaceSocket', "Surface2")
        self.outputs.new('SvSurfaceSocket', "Surface")
        self.update_sockets(context)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'input_mode', text='')
        layout.prop(self, 'direction', expand=True)
        layout.prop(self, 'use_nurbs', text='')
        layout.prop(self, 'check_edges')
        if self.check_edges:
            layout.prop(self, 'check_edges_pts')
            layout.prop(self, 'check_edges_tolerance')

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        if self.use_nurbs != 'GENERIC':
            layout.prop(self, 'unify')
            layout.prop(self, 'knotvector_accuracy')

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
        surfaces_out = []
        for params in surfaces_in:
            new_surfaces = []
            for surfaces in params:
                all_nurbs = False
                if self.use_nurbs != 'GENERIC':
                    nurbs_surfaces = [SvNurbsSurface.get(s) for s in surfaces]
                    if any(s is None for s in nurbs_surfaces):
                        if self.use_nurbs == 'NURBS':
                            raise UnsupportedSurfaceTypeException("Some of surfaces are not NURBS")
                    else:
                        surfaces = nurbs_surfaces
                        all_nurbs = True
                    if self.unify and all_nurbs:
                        surfaces = unify_nurbs_surfaces(surfaces, directions={other_direction(self.direction)},
                                                        knotvector_accuracy = self.knotvector_accuracy)
                if self.check_edges:
                    check_surface_edges_coincidence(surfaces, direction = self.direction,
                                                    n_pts = self.check_edges_pts,
                                                    tolerance = self.check_edges_tolerance)
                new_surface = concatenate_surfaces(direction = self.direction, surfaces = surfaces, native_only = self.use_nurbs == 'NURBS')
                new_surfaces.append(new_surface)
            if nested_input:
                surfaces_out.append(new_surfaces)
            else:
                surfaces_out.extend(new_surfaces)

        self.outputs['Surface'].sv_set(surfaces_out)

def register():
    bpy.utils.register_class(SvConcatSurfacesNode)

def unregister():
    bpy.utils.unregister_class(SvConcatSurfacesNode)

