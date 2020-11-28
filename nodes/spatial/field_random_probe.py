# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import random
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from mathutils.kdtree import KDTree

import sverchok
from sverchok.core.sockets import setup_new_node_location
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, throttle_and_update_node, ensure_nesting_level, get_data_nesting_level
from sverchok.core.socket_data import SvNoDataError
from sverchok.utils.field.scalar import SvScalarField
from sverchok.utils.field.probe import field_random_probe

class SvFieldRandomProbeMk2Node(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Scalar Field Random Probe
    Tooltip: Generate random points according to scalar field
    """
    bl_idname = 'SvFieldRandomProbeMk2Node'
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

    min_r : FloatProperty(
            name = "Min.Distance",
            description = "Minimum distance between generated points; set to 0 to disable the check",
            default = 0.0,
            min = 0.0,
            update = updateNode)

    @throttle_and_update_node
    def update_sockets(self, context):
        self.inputs['FieldMin'].hide_safe = self.proportional != True
        self.inputs['FieldMax'].hide_safe = self.proportional != True

    proportional : BoolProperty(
            name = "Proportional",
            default = False,
            update = update_sockets)

    def draw_buttons(self, context, layout):
        layout.prop(self, "proportional", toggle=True)

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
        self.inputs.new('SvStringsSocket', "Threshold").prop_name = 'threshold'
        self.inputs.new('SvStringsSocket', "FieldMin").prop_name = 'field_min'
        self.inputs.new('SvStringsSocket', "FieldMax").prop_name = 'field_max'
        self.inputs.new('SvStringsSocket', 'Seed').prop_name = 'seed'
        self.outputs.new('SvVerticesSocket', "Vertices")
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
        vertices_s = self.inputs['Bounds'].sv_get()
        count_s = self.inputs['Count'].sv_get()
        min_r_s = self.inputs['MinDistance'].sv_get()
        threshold_s = self.inputs['Threshold'].sv_get()
        field_min_s = self.inputs['FieldMin'].sv_get()
        field_max_s = self.inputs['FieldMax'].sv_get()
        seed_s = self.inputs['Seed'].sv_get()

        if self.inputs['Field'].is_linked:
            fields_s = ensure_nesting_level(fields_s, 2, data_types=(SvScalarField,))
        vertices_s = ensure_nesting_level(vertices_s, 4)
        count_s = ensure_nesting_level(count_s, 2)
        min_r_s = ensure_nesting_level(min_r_s, 2)
        threshold_s = ensure_nesting_level(threshold_s, 2)
        field_min_s = ensure_nesting_level(field_min_s, 2)
        field_max_s = ensure_nesting_level(field_max_s, 2)
        seed_s = ensure_nesting_level(seed_s, 2)

        verts_out = []
        inputs = zip_long_repeat(fields_s, vertices_s, threshold_s, field_min_s, field_max_s, count_s, min_r_s, seed_s)
        for objects in inputs:
            for field, vertices, threshold, field_min, field_max, count, min_r, seed in zip_long_repeat(*objects):

                bbox = self.get_bounds(vertices)
                new_verts = field_random_probe(field, bbox, count, threshold, self.proportional, field_min, field_max, min_r, seed)

                verts_out.append(new_verts)

        self.outputs['Vertices'].sv_set(verts_out)

def register():
    bpy.utils.register_class(SvFieldRandomProbeMk2Node)

def unregister():
    bpy.utils.unregister_class(SvFieldRandomProbeMk2Node)

