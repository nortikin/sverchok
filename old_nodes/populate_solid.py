# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import random

import bpy
from bpy.props import FloatProperty, StringProperty, BoolProperty, EnumProperty, IntProperty

from sverchok.core.socket_data import SvNoDataError
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, ensure_nesting_level, zip_long_repeat, throttle_and_update_node, repeat_last_for_length
from sverchok.utils.field.scalar import SvScalarField
from sverchok.utils.field.probe import field_random_probe
from sverchok.utils.surface.populate import populate_surface
from sverchok.utils.surface.freecad import SvSolidFaceSurface
from sverchok.dependencies import FreeCAD
from sverchok.utils.dummy_nodes import add_dummy

if FreeCAD is None:
    add_dummy('SvPopulateSolidNode', 'Populate Solid', 'FreeCAD')
else:
    from FreeCAD import Base
    import Part

class SvPopulateSolidNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Populate Solid
    Tooltip: Generate random points within solid body
    """
    bl_idname = 'SvPopulateSolidNode'
    bl_label = 'Populate Solid'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_POPULATE_SOLID'

    @throttle_and_update_node
    def update_sockets(self, context):
        self.inputs['FieldMin'].hide_safe = self.proportional != True
        self.inputs['FieldMax'].hide_safe = self.proportional != True
        self.inputs['FaceMask'].hide_safe = self.gen_mode != 'SURFACE'

    modes = [
            ('VOLUME', "Volume", "Generate points inside solid body", 0),
            ('SURFACE', "Surface", "Generate points on the surface of the body", 1)
        ]

    gen_mode : EnumProperty(
            name = "Generation mode",
            items = modes,
            default = 'VOLUME',
            update = update_sockets)

    threshold : FloatProperty(
            name = "Threshold",
            default = 0.5,
            update = updateNode)

    field_min : FloatProperty(
            name = "Field Minimum",
            default = 0.0,
            update = updateNode)

    field_max : FloatProperty(
            name = "Field Maximum",
            default = 1.0,
            update = updateNode)

    seed: IntProperty(default=0, name='Seed', update=updateNode)

    count : IntProperty(
            name = "Count",
            default = 50,
            min = 1,
            update = updateNode)

    proportional : BoolProperty(
            name = "Proportional",
            default = False,
            update = update_sockets)

    min_r : FloatProperty(
            name = "Min.Distance",
            description = "Minimum distance between generated points; set to 0 to disable the check",
            default = 0.0,
            min = 0.0,
            update = updateNode)

    accuracy: IntProperty(
        name="Accuracy",
        default=5,
        min=1,
        update=updateNode)

    in_surface: BoolProperty(
        name="Accept in surface",
        description="Accept point if it is over solid surface",
        default=True,
        update=updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, "gen_mode", text='Mode')
        layout.prop(self, "proportional")
        if self.gen_mode == 'VOLUME':
            layout.prop(self, "in_surface")

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, "accuracy")

    def sv_init(self, context):
        self.inputs.new('SvSolidSocket', "Solid")
        self.inputs.new('SvScalarFieldSocket', "Field").enable_input_link_menu = False
        self.inputs.new('SvStringsSocket', "Count").prop_name = 'count'
        self.inputs.new('SvStringsSocket', "MinDistance").prop_name = 'min_r'
        self.inputs.new('SvStringsSocket', "Threshold").prop_name = 'threshold'
        self.inputs.new('SvStringsSocket', "FieldMin").prop_name = 'field_min'
        self.inputs.new('SvStringsSocket', "FieldMax").prop_name = 'field_max'
        self.inputs.new('SvStringsSocket', 'FaceMask')
        self.inputs.new('SvStringsSocket', 'Seed').prop_name = 'seed'
        self.outputs.new('SvVerticesSocket', "Vertices")

    def get_tolerance(self):
        return 10**(-self.accuracy)

    def generate_volume(self, solid, field, count, min_r, threshold, field_min, field_max, seed):
        def check(vert):
            point = Base.Vector(vert)
            return solid.isInside(point, self.get_tolerance(), self.in_surface)

        box = solid.BoundBox
        bbox = ((box.XMin, box.YMin, box.ZMin), (box.XMax, box.YMax, box.ZMax))
        
        return field_random_probe(field, bbox, count, threshold, self.proportional, field_min, field_max, min_r, seed, predicate=check)

    def distribute_faces(self, faces, total_count):
        points_per_face = [0 for _ in range(len(faces))]
        areas = [face.Area for face in faces]
        chosen_faces = random.choices(range(len(faces)), weights=areas, k=total_count)
        for i in chosen_faces:
            points_per_face[i] += 1
        return points_per_face

    def generate_surface(self, solid, field, count, min_r, threshold, field_min, field_max, mask, seed):
        counts = self.distribute_faces(solid.Faces, count)
        new_verts = []
        mask = repeat_last_for_length(mask, len(solid.Faces))
        counts = repeat_last_for_length(counts, len(solid.Faces))
        for face, ok, cnt in zip(solid.Faces, mask, counts):
            if not ok:
                continue

            def check(uv, vert):
                point = Base.Vector(vert)
                return face.isInside(point, self.get_tolerance(), True)

            surface = SvSolidFaceSurface(face)

            _, face_verts = populate_surface(surface, field, cnt, threshold, self.proportional, field_min, field_max, min_r, seed, predicate=check)
            new_verts.extend(face_verts)
        return new_verts

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        if self.proportional and not self.inputs['Field'].is_linked:
            raise SvNoDataError(socket=self.inputs['Field'], node=self)

        solid_s = self.inputs['Solid'].sv_get()
        fields_s = self.inputs['Field'].sv_get(default=[[None]])
        count_s = self.inputs['Count'].sv_get()
        min_r_s = self.inputs['MinDistance'].sv_get()
        threshold_s = self.inputs['Threshold'].sv_get()
        field_min_s = self.inputs['FieldMin'].sv_get()
        field_max_s = self.inputs['FieldMax'].sv_get()
        mask_s = self.inputs['FaceMask'].sv_get(default=[[[True]]])
        seed_s = self.inputs['Seed'].sv_get()

        solid_s = ensure_nesting_level(solid_s, 2, data_types=(Part.Shape,))
        if self.inputs['Field'].is_linked:
            fields_s = ensure_nesting_level(fields_s, 2, data_types=(SvScalarField,))
        count_s = ensure_nesting_level(count_s, 2)
        min_r_s = ensure_nesting_level(min_r_s, 2)
        threshold_s = ensure_nesting_level(threshold_s, 2)
        field_min_s = ensure_nesting_level(field_min_s, 2)
        field_max_s = ensure_nesting_level(field_max_s, 2)
        mask_s = ensure_nesting_level(mask_s, 3)
        seed_s = ensure_nesting_level(seed_s, 2)

        verts_out = []
        inputs = zip_long_repeat(solid_s, fields_s, count_s, min_r_s, threshold_s, field_min_s, field_max_s, mask_s, seed_s)
        for objects in inputs:
            for solid, field, count, min_r, threshold, field_min, field_max, mask, seed in zip_long_repeat(*objects):
                if self.gen_mode == 'VOLUME':
                    new_verts = self.generate_volume(solid, field, count, min_r, threshold, field_min, field_max, seed)
                else:
                    new_verts = self.generate_surface(solid, field, count, min_r, threshold, field_min, field_max, mask, seed)
                verts_out.append(new_verts)

        self.outputs['Vertices'].sv_set(verts_out)

def register():
    if FreeCAD is not None:
        bpy.utils.register_class(SvPopulateSolidNode)

def unregister():
    if FreeCAD is not None:
        bpy.utils.unregister_class(SvPopulateSolidNode)

