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
from sverchok.data_structure import updateNode, ensure_nesting_level, zip_long_repeat, throttle_and_update_node, repeat_last_for_length, get_data_nesting_level
from sverchok.utils.field.scalar import SvScalarField
from sverchok.utils.field.probe import field_random_probe
from sverchok.utils.surface.populate import populate_surface
from sverchok.utils.surface.freecad import SvSolidFaceSurface
from sverchok.dependencies import FreeCAD
from sverchok.utils.dummy_nodes import add_dummy

if FreeCAD is None:
    add_dummy('SvPopulateSolidMk2Node', 'Populate Solid', 'FreeCAD')
else:
    from FreeCAD import Base
    import Part

class SvPopulateSolidMk2Node(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Populate Solid
    Tooltip: Generate random points within solid body
    """
    bl_idname = 'SvPopulateSolidMk2Node'
    bl_label = 'Populate Solid'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_POPULATE_SOLID'

    @throttle_and_update_node
    def update_sockets(self, context):
        self.inputs['FieldMin'].hide_safe = self.proportional != True
        self.inputs['FieldMax'].hide_safe = self.proportional != True
        self.inputs['FaceMask'].hide_safe = self.gen_mode != 'SURFACE'
        self.inputs['RadiusField'].hide_safe = self.distance_mode != 'FIELD'
        self.inputs['MinDistance'].hide_safe = self.distance_mode != 'CONST'
        self.outputs['Radiuses'].hide_safe = self.distance_mode != 'FIELD'

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

    distance_modes = [
            ('CONST', "Min. Distance", "Specify minimum distance between points", 0),
            ('FIELD', "Radius Field", "Specify radius of empty sphere around each point by scalar field", 1)
        ]

    distance_mode : EnumProperty(
            name = "Distance",
            description = "How minimum distance between points is restricted",
            items = distance_modes,
            default = 'CONST',
            update = update_sockets)

    random_radius : BoolProperty(
            name = "Random radius",
            description = "Make sphere radiuses random, restricted by scalar field values",
            default = False,
            update = updateNode)

#     flat_output : BoolProperty(
#             name = "Flat output",
#             description = "If checked, generate one flat list of vertices for all input solids; otherwise, generate a separate list of vertices for each solid",
#             default = False,
#             update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, "gen_mode", text='Mode')
        layout.prop(self, 'distance_mode')
        layout.prop(self, "proportional")
        if self.gen_mode == 'VOLUME':
            layout.prop(self, "in_surface")
        if self.distance_mode == 'FIELD':
            layout.prop(self, 'random_radius')
#         layout.prop(self, "flat_output")

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, "accuracy")

    def sv_init(self, context):
        self.inputs.new('SvSolidSocket', "Solid")
        self.inputs.new('SvScalarFieldSocket', "Field").enable_input_link_menu = False
        self.inputs.new('SvStringsSocket', "Count").prop_name = 'count'
        self.inputs.new('SvStringsSocket', "MinDistance").prop_name = 'min_r'
        self.inputs.new('SvScalarFieldSocket', "RadiusField")
        self.inputs.new('SvStringsSocket', "Threshold").prop_name = 'threshold'
        self.inputs.new('SvStringsSocket', "FieldMin").prop_name = 'field_min'
        self.inputs.new('SvStringsSocket', "FieldMax").prop_name = 'field_max'
        self.inputs.new('SvStringsSocket', 'FaceMask')
        self.inputs.new('SvStringsSocket', 'Seed').prop_name = 'seed'
        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket', "Radiuses")
        self.update_sockets(context)

    def get_tolerance(self):
        return 10**(-self.accuracy)

    def generate_volume(self, solid, field, count, min_r, radius_field, threshold, field_min, field_max):
        def check(vert):
            point = Base.Vector(vert)
            return solid.isInside(point, self.get_tolerance(), self.in_surface)

        box = solid.BoundBox
        bbox = ((box.XMin, box.YMin, box.ZMin), (box.XMax, box.YMax, box.ZMax))
        
        return field_random_probe(field, bbox, count, threshold,
                    self.proportional, field_min, field_max,
                    min_r = min_r, min_r_field = radius_field,
                    random_radius = self.random_radius,
                    seed = None, predicate=check)

    def distribute_faces(self, faces, total_count):
        points_per_face = [0 for _ in range(len(faces))]
        areas = [face.Area for face in faces]
        chosen_faces = random.choices(range(len(faces)), weights=areas, k=total_count)
        for i in chosen_faces:
            points_per_face[i] += 1
        return points_per_face

    def generate_surface(self, solid, field, count, min_r, radius_field, threshold, field_min, field_max, mask):
        counts = self.distribute_faces(solid.Faces, count)
        new_verts = []
        new_radiuses = []
        mask = repeat_last_for_length(mask, len(solid.Faces))
        counts = repeat_last_for_length(counts, len(solid.Faces))
        done_spheres = []
        for face, ok, cnt in zip(solid.Faces, mask, counts):
            if not ok:
                continue

            def check(uv, vert):
                point = Base.Vector(vert)
                return face.isInside(point, self.get_tolerance(), True)

            surface = SvSolidFaceSurface(face)

            _, face_verts, radiuses = populate_surface(surface, field, cnt, threshold,
                    self.proportional, field_min, field_max,
                    min_r = min_r, min_r_field = radius_field,
                    random_radius = self.random_radius,
                    avoid_spheres = done_spheres,
                    seed = None, predicate=check)
            done_spheres.extend(list(zip(face_verts, radiuses)))
            new_verts.extend(face_verts)
            new_radiuses.extend(radiuses)
        return new_verts, new_radiuses

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
        if self.distance_mode == 'FIELD':
            radius_s = self.inputs['RadiusField'].sv_get()
        else:
            radius_s = [[None]]

        input_level = get_data_nesting_level(solid_s, data_types=(Part.Shape,))
        nested_solid = input_level > 1
        solid_s = ensure_nesting_level(solid_s, 2, data_types=(Part.Shape,))
        if self.inputs['Field'].is_linked:
            input_level = get_data_nesting_level(fields_s, data_types=(SvScalarField,))
            nested_field = input_level > 1
            fields_s = ensure_nesting_level(fields_s, 2, data_types=(SvScalarField,))
        else:
            nested_field = False
        if self.distance_mode == 'FIELD':
            input_level = get_data_nesting_level(radius_s, data_types=(SvScalarField,))
            nested_radius = input_level > 1
            radius_s = ensure_nesting_level(radius_s, 2, data_types=(SvScalarField,))
        else:
            nested_radius = False
        count_s = ensure_nesting_level(count_s, 2)
        min_r_s = ensure_nesting_level(min_r_s, 2)
        threshold_s = ensure_nesting_level(threshold_s, 2)
        field_min_s = ensure_nesting_level(field_min_s, 2)
        field_max_s = ensure_nesting_level(field_max_s, 2)
        mask_s = ensure_nesting_level(mask_s, 3)
        seed_s = ensure_nesting_level(seed_s, 2)

        nested_output = nested_solid or nested_field or nested_radius

        verts_out = []
        radius_out = []
        inputs = zip_long_repeat(solid_s, fields_s, count_s, min_r_s, radius_s, threshold_s, field_min_s, field_max_s, mask_s, seed_s)
        for objects in inputs:
            new_verts = []
            new_radius = []
            for solid, field, count, min_r, radius, threshold, field_min, field_max, mask, seed in zip_long_repeat(*objects):
                if seed == 0:
                    seed = 12345
                random.seed(seed)
                if self.distance_mode == 'FIELD':
                    min_r = 0
                if self.gen_mode == 'VOLUME':
                    verts, radiuses = self.generate_volume(solid, field, count, min_r, radius, threshold, field_min, field_max)
                else:
                    verts, radiuses = self.generate_surface(solid, field, count, min_r, radius, threshold, field_min, field_max, mask)

                new_verts.append(verts)
                new_radius.append(radiuses)

            if nested_output:
                verts_out.append(new_verts)
                radius_out.append(new_radius)
            else:
                verts_out.extend(new_verts)
                radius_out.extend(new_radius)

        self.outputs['Vertices'].sv_set(verts_out)
        self.outputs['Radiuses'].sv_set(radius_out)

def register():
    if FreeCAD is not None:
        bpy.utils.register_class(SvPopulateSolidMk2Node)

def unregister():
    if FreeCAD is not None:
        bpy.utils.unregister_class(SvPopulateSolidMk2Node)

