# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.core.sockets import setup_new_node_location
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok.core.socket_data import SvNoDataError
from sverchok.utils.field.scalar import SvScalarField
from sverchok.utils.field.probe import field_random_probe

class SvFieldRandomProbeMk3Node(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Scalar Field Random Probe
    Tooltip: Generate random points according to scalar field
    """
    bl_idname = 'SvFieldRandomProbeMk3Node'
    bl_label = 'Field Random Probe'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_FIELD_RANDOM_PROBE'

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

    def update_sockets(self, context):
        self.inputs['FieldMin'].hide_safe = self.proportional != True
        self.inputs['FieldMax'].hide_safe = self.proportional != True
        self.inputs['RadiusField'].hide_safe = self.distance_mode != 'FIELD'
        self.inputs['MinDistance'].hide_safe = self.distance_mode != 'CONST'
        self.outputs['Radius'].hide_safe = self.distance_mode != 'FIELD'
        updateNode(self, context)

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

    min_r : FloatProperty(
            name = "Min.Distance",
            description = "Minimum distance between generated points; set to 0 to disable the check",
            default = 0.0,
            min = 0.0,
            update = updateNode)

    proportional : BoolProperty(
            name = "Proportional",
            description = "Make points density proportional to field value",
            default = False,
            update = update_sockets)

    random_radius : BoolProperty(
            name = "Random radius",
            description = "Make sphere radiuses random, restricted by scalar field values",
            default = False,
            update = updateNode)

    flat_output : BoolProperty(
            name = "Flat output",
            description = "If checked, generate one flat list of vertices for all input fields; otherwise, generate a separate list of vertices for each field",
            default = True,
            update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'distance_mode')
        layout.prop(self, "proportional")
        if self.distance_mode == 'FIELD':
            layout.prop(self, 'random_radius')
        layout.prop(self, "flat_output")

    class BoundsMenuHandler():
        @classmethod
        def get_items(cls, socket, context):
            return [("BOX", "Add Box node", "Add Box node")]

        @classmethod
        def on_selected(cls, tree, node, socket, item, context):
            new_node = tree.nodes.new('SvBoxNodeMk2')
            new_node.label = "Bounds"
            tree.links.new(new_node.outputs[0], node.inputs['Bounds'])
            setup_new_node_location(new_node, node)

    def sv_init(self, context):
        self.inputs.new('SvScalarFieldSocket', "Field")
        self.inputs.new('SvVerticesSocket', "Bounds").link_menu_handler = 'BoundsMenuHandler'
        self.inputs.new('SvStringsSocket', "Count").prop_name = 'count'
        self.inputs.new('SvStringsSocket', "MinDistance").prop_name = 'min_r'
        self.inputs.new('SvScalarFieldSocket', "RadiusField")
        self.inputs.new('SvStringsSocket', "Threshold").prop_name = 'threshold'
        self.inputs.new('SvStringsSocket', "FieldMin").prop_name = 'field_min'
        self.inputs.new('SvStringsSocket', "FieldMax").prop_name = 'field_max'
        self.inputs.new('SvStringsSocket', 'Seed').prop_name = 'seed'
        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket', "Radius")
        self.update_sockets(context)

    def get_bounds(self, vertices):
        vs = np.array(vertices)
        min = vs.min(axis=0)
        max = vs.max(axis=0)
        return min.tolist(), max.tolist()

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        if self.proportional and not self.inputs['Field'].is_linked:
            raise SvNoDataError(socket=self.inputs['Field'], node=self)

        fields_s = self.inputs['Field'].sv_get(default=[[None]])
        if self.distance_mode == 'FIELD':
            radius_s = self.inputs['RadiusField'].sv_get()
        else:
            radius_s = [[None]]
        vertices_s = self.inputs['Bounds'].sv_get()
        count_s = self.inputs['Count'].sv_get()
        min_r_s = self.inputs['MinDistance'].sv_get()
        threshold_s = self.inputs['Threshold'].sv_get()
        field_min_s = self.inputs['FieldMin'].sv_get()
        field_max_s = self.inputs['FieldMax'].sv_get()
        seed_s = self.inputs['Seed'].sv_get()

        if self.inputs['Field'].is_linked:
            fields_s = ensure_nesting_level(fields_s, 2, data_types=(SvScalarField,))
            input_level = get_data_nesting_level(fields_s, data_types=(SvScalarField,))
            nested_field = input_level > 1
        else:
            nested_field = False
        if self.inputs['RadiusField'].is_linked:
            radius_s = ensure_nesting_level(radius_s, 2, data_types=(SvScalarField,))
            input_level = get_data_nesting_level(radius_s, data_types=(SvScalarField,))
            nested_radius = input_level > 1
        else:
            nested_radius = False

        verts_level = get_data_nesting_level(vertices_s)
        nested_verts = verts_level > 3
        vertices_s = ensure_nesting_level(vertices_s, 4)
        count_s = ensure_nesting_level(count_s, 2)
        min_r_s = ensure_nesting_level(min_r_s, 2)
        threshold_s = ensure_nesting_level(threshold_s, 2)
        field_min_s = ensure_nesting_level(field_min_s, 2)
        field_max_s = ensure_nesting_level(field_max_s, 2)
        seed_s = ensure_nesting_level(seed_s, 2)

        nested_output = nested_field or nested_radius or nested_verts

        verts_out = []
        radius_out = []
        inputs = zip_long_repeat(fields_s, radius_s, vertices_s, threshold_s, field_min_s, field_max_s, count_s, min_r_s, seed_s)
        for objects in inputs:
            new_verts = []
            new_radiuses = []
            for field, radius_field, vertices, threshold, field_min, field_max, count, min_r, seed in zip_long_repeat(*objects):

                bbox = self.get_bounds(vertices)
                if self.distance_mode == 'FIELD':
                    min_r = 0
                verts, radiuses = field_random_probe(field, bbox, count,
                                threshold, self.proportional,
                                field_min, field_max,
                                min_r = min_r, min_r_field = radius_field,
                                random_radius = self.random_radius,
                                seed = seed)

                if self.flat_output:
                    new_verts.extend(verts)
                    new_radiuses.extend(radiuses)
                else:
                    new_verts.append(verts)
                    new_radiuses.append(radiuses)

            if nested_output:
                verts_out.append(new_verts)
                radius_out.append(new_radiuses)
            else:
                verts_out.extend(new_verts)
                radius_out.extend(new_radiuses)

        self.outputs['Vertices'].sv_set(verts_out)
        self.outputs['Radius'].sv_set(radius_out)

def register():
    bpy.utils.register_class(SvFieldRandomProbeMk3Node)

def unregister():
    bpy.utils.unregister_class(SvFieldRandomProbeMk3Node)

