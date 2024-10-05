
import numpy as np

import bpy
from bpy.props import FloatProperty, IntProperty, BoolProperty, EnumProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.field.scalar import SvScalarField
from sverchok.utils.manifolds import intersect_line_iso_surface, FAIL, RETURN_NONE, SKIP

class SvExImplSurfaceRaycastNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Implicit Surface Raycast
    Tooltip: Raycast onto implicit surface (defined by scalar field)
    """
    bl_idname = 'SvExImplSurfaceRaycastNode'
    bl_label = 'Implicit Surface Raycast'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_IMPL_SURF_RAYCAST'
    sv_dependencies = {'scipy'}

    max_distance : FloatProperty(
            name = "Max Distance",
            default = 10.0,
            min = 0.0,
            update = updateNode)

    iso_value : FloatProperty(
            name = "Iso Value",
            default = 0.0,
            update = updateNode)

    sections : IntProperty(
            name = "N Sections",
            default = 10,
            min = 2,
            update = updateNode)

    first_only : BoolProperty(
            name = "First solution only",
            default = True,
            update = updateNode)

    fail_modes = [
            (FAIL, "Fail", "Raise an error", 0),
            (SKIP, "Skip", "Do not output anything", 1),
            (RETURN_NONE, "Return None", "Return None", 2)
        ]

    on_fail : EnumProperty(
            name = "On fail",
            items = fail_modes,
            default = FAIL,
            update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvScalarFieldSocket', "Field")
        p = self.inputs.new('SvVerticesSocket', "Vertices")
        p.use_prop = True
        p.default_property = (0.0, 0.0, 0.0)
        p = self.inputs.new('SvVerticesSocket', "Direction")
        p.use_prop = True
        p.default_property = (0.0, 0.0, 1.0)
        self.inputs.new('SvStringsSocket', 'IsoValue').prop_name = 'iso_value'
        self.inputs.new('SvStringsSocket', 'MaxDistance').prop_name = 'max_distance'
        self.outputs.new('SvVerticesSocket', 'Vertices')
        self.outputs.new('SvStringsSocket', 'Distance')

    def draw_buttons(self, context, layout):
        layout.prop(self, 'first_only')
        layout.prop(self, 'sections')

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, 'on_fail')

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        field_s = self.inputs['Field'].sv_get()
        verts_s = self.inputs['Vertices'].sv_get()
        direction_s = self.inputs['Direction'].sv_get()
        iso_value_s = self.inputs['IsoValue'].sv_get()
        max_distance_s = self.inputs['MaxDistance'].sv_get()

        field_s = ensure_nesting_level(field_s, 2, data_types=(SvScalarField,))
        verts_s = ensure_nesting_level(verts_s, 3)
        direction_s = ensure_nesting_level(direction_s, 3)
        iso_value_s = ensure_nesting_level(iso_value_s, 2)
        max_distance_s = ensure_nesting_level(max_distance_s, 2)

        verts_out = []
        distance_out = []

        on_fail = self.on_fail
        if on_fail == SKIP:
            on_fail = RETURN_NONE

        for fields, verts_i, directions, iso_value_i, max_distance_i in zip_long_repeat(field_s, verts_s, direction_s, iso_value_s, max_distance_s):
            new_verts = []
            new_t = []
            for field, vert, direction, iso_value, max_distance in zip_long_repeat(fields, verts_i, directions, iso_value_i, max_distance_i):
                res = intersect_line_iso_surface(field, vert, direction,
                                                     max_distance, iso_value,
                                                     sections = self.sections,
                                                     first_only = self.first_only,
                                                     on_fail = on_fail)
                if res is None:
                    if self.on_fail == SKIP:
                        continue
                    else:
                        ts = [None]
                        pts = [None]
                else:
                    ts, pts = res
                if self.first_only:
                    ts = ts[0]
                    pts = pts[0]
                new_verts.append(pts)
                new_t.append(ts)
            verts_out.append(new_verts)
            distance_out.append(new_t)

        self.outputs['Vertices'].sv_set(verts_out)
        self.outputs['Distance'].sv_set(distance_out)


def register():
    bpy.utils.register_class(SvExImplSurfaceRaycastNode)


def unregister():
    bpy.utils.unregister_class(SvExImplSurfaceRaycastNode)
