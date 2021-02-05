# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import ast

from mathutils import Vector
import numpy as np
import bpy
from bpy.props import BoolProperty, StringProperty, EnumProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode

from sverchok.data_structure import (updateNode, throttle_and_update_node,
                                     list_match_func, numpy_list_match_modes,
                                     enum_item_4)

from sverchok.utils.modules.eval_formula import get_variables, safe_eval
from sverchok.utils.sv_itertools import recurse_f_level_control

def transform_data(data, transform):
    if transform == 'As_is':
        return data
    if transform == 'Vector':
        return Vector(data)
    if transform == 'Array':
        return np.array(data)
    if transform == 'Set':
        return set(data)
    if transform == 'String':
        return str(data)
    return data

def ensure_list(value):
    if isinstance(value, (int, float, str, list)):
        return value
    if isinstance(value, np.ndarray):
        return value.tolist()
    return list(value)

def formula_func(parameters, constant, matching_f):

    formulas, separate, var_names, transformations, as_list = constant

    object_results = []
    for values in zip(*matching_f(parameters)):
        vals = [transform_data(d, tr) for d, tr in zip(values, transformations)]
        variables = dict(zip(var_names, vals))
        vector = []
        for formula in formulas:
            if formula:
                value = safe_eval(formula, variables)
                if as_list:
                    vector.append(ensure_list(value))
                else:
                    vector.append(value)
        if separate:
            object_results.append(vector)
        else:
            object_results.extend(vector)


    return object_results


socket_dict = {
    "Number / Generic": "SvStringsSocket",
    "Vector": "SvVerticesSocket",
    "Color":   "SvColorSocket",
    "Matrix":   "SvMaatrixSocket",
    "Quaternion": "SvQuaternionSocket",
    "Object": "SvObjectSocket",
    "Dictionary": "SvDictionarySocket",
    "Surface": "SvSurfaceSocket",
    "Curve": "SvCurveSocket",
    "Scalar Field": "SvScalarFieldSocket",
    "Vector Field": "SvVectorFieldSocket",
    "Solid": "SvSolidSocket",
    "File Path": "SvFilePathSocket",
    }


class SvFormulaNodeMk5(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Formula
    Tooltip: Calculate by custom formula.
    """
    bl_idname = 'SvFormulaNodeMk5'
    bl_label = 'Formula'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_FORMULA'

    @throttle_and_update_node
    def on_update(self, context):
        self.adjust_sockets()

    @throttle_and_update_node
    def on_update_dims(self, context):
        if self.output_dimensions < 4:
            self.formula4 = ""
        if self.output_dimensions < 3:
            self.formula3 = ""
        if self.output_dimensions < 2:
            self.formula2 = ""

        self.adjust_sockets()

    output_dimensions: IntProperty(name="Dimensions", default=1, min=1, max=4, update=on_update_dims)

    formula1: StringProperty(default="x+y", update=on_update)
    formula2: StringProperty(update=on_update)
    formula3: StringProperty(update=on_update)
    formula4: StringProperty(update=on_update)

    separate: BoolProperty(name="Separate", default=False, update=updateNode)
    wrapping: bpy.props.EnumProperty(
        items=[(k, k, '', i) for i, k in enumerate(["-1", "0", "+1"])],
        description="+1: adds a set of square brackets around the output\n 0: Keeps result unchanged\n-1: Removes a set of outer square brackets",
        default="0", update=updateNode
    )

    use_ast: BoolProperty(name="AST", description="uses the ast.literal_eval module", update=updateNode)
    as_list: BoolProperty(name="List output", description="Forces a regular list output", update=updateNode)
    ui_message: StringProperty(name="ui message")
    list_match: EnumProperty(
        name="List Match",
        description="Behavior on different list lengths",
        items=numpy_list_match_modes, default="REPEAT",
        update=updateNode)

    def update_output_socket(self, context):
        if self.outputs[0].bl_idname != socket_dict[self.output_type]:
            self.outputs.remove(self.outputs[0])
            self.outputs.new(socket_dict[self.output_type], 'Result')
            updateNode(self, context)

    output_type: EnumProperty(
        name="Output",
        description="Behavior on different list lengths",
        items=enum_item_4(socket_dict.keys()), default="Number_/_Generic",
        update=update_output_socket)

    def formulas(self):
        return [self.formula1, self.formula2, self.formula3, self.formula4]

    def formula(self, k):
        return self.formulas()[k]

    def draw_buttons(self, context, layout):
        if self.ui_message:
            r = layout.row()
            r.alert = True
            r.label(text=self.ui_message, icon='INFO')
        layout.prop(self, "formula1", text="")
        if self.output_dimensions > 1:
            layout.prop(self, "formula2", text="")
        if self.output_dimensions > 2:
            layout.prop(self, "formula3", text="")
        if self.output_dimensions > 3:
            layout.prop(self, "formula4", text="")
        row = layout.row()
        if self.inputs:
            row.prop(self, "separate", text="Split", toggle=True)
        else:
            row.prop(self, "use_ast", text="", icon="SCRIPTPLUGINS")
        row.prop(self, "wrapping", expand=True)

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, "output_dimensions")
        layout.prop(self, "list_match")
        layout.prop(self, "as_list")

        layout.prop(self, "output_type")


        self.draw_buttons(context, layout)

    def sv_init(self, context):
        self.width = 230
        self.inputs.new('SvFormulaSocket', "x")

        self.outputs.new('SvStringsSocket', "Result")


    def get_variables(self):
        variables = set()

        for formula in self.formulas():
            vs = get_variables(formula)
            variables.update(vs)

        return list(sorted(variables))

    def adjust_sockets(self):
        variables = self.get_variables()

        # if current node sockets match the variables sequence, do nothing skip
        # this is the logic path that will be encountered most often.
        if len(self.inputs) == len(variables):
            if variables == [socket.name for socket in self.inputs]:
                # self.info("no UI change: socket inputs same")
                return

        # else to avoid making things complicated we rebuild the UI inputs, even when it is technically sub optimal
        self.hot_reload_sockets()

    def clear_and_repopulate_sockets_from_variables(self):
        with self.sv_throttle_tree_update():
            self.inputs.clear()
            variables = self.get_variables()
            for v in variables:
                self.inputs.new('SvFormulaSocket', v)

    def hot_reload_sockets(self):
        """
        function hoisted from functorb, with deletions and edits

         - store current input socket links by name/origin
         - wipe all inputs
         - recreate new sockets from variables
         - relink former links by name on this socket, but by index from their origin.

        """

        self.info('handling input wipe and relink')
        nodes = self.id_data.nodes
        node_tree = self.id_data

        # if any current connections... gather them
        reconnections = []
        for i in (i for i in self.inputs if i.is_linked):
            for L in i.links:
                link = lambda: None
                link.from_node = L.from_socket.node.name
                link.from_socket = L.from_socket.index   # index used here because these can come from reroute
                link.to_socket = L.to_socket.name        # this node will always have unique socket names
                reconnections.append(link)
        depths = {}
        transform = {}
        for node_input in self.inputs:
            depths[node_input.name] = node_input.depth
            transform[node_input.name] = node_input.transform

        self.clear_and_repopulate_sockets_from_variables()

        for node_input in self.inputs:
            if node_input.name in depths:
                node_input.depth = depths[node_input.name]
                node_input.transform = transform[node_input.name]
        # restore connections where applicable (by socket name), if no links.. this is a no op.
        for link in reconnections:
            try:
                from_part = nodes[link.from_node].outputs[link.from_socket]
                to_part = self.inputs[link.to_socket]
                node_tree.links.new(from_part, to_part)
            except Exception as err:
                str_from = f'nodes[{link.from_node}].outputs[{link.from_socket}]'
                str_to = f'nodes[{self}].inputs[{link.to_socket}]'
                self.exception(f'failed: {str_from} -> {str_to}')
                self.exception(err)

    def sv_update(self):
        '''
        update analyzes the state of the node and returns if the criteria to start processing
        are not met.
        '''
        if not any(len(formula) for formula in self.formulas()):
            return

        self.adjust_sockets()

    def get_input(self):
        variables = self.get_variables()
        inputs = {}

        for var in variables:
            if var in self.inputs and self.inputs[var].is_linked:
                inputs[var] = self.inputs[var].sv_get()

        return inputs


    def all_inputs_connected(self):
        if self.inputs:
            return all([socket.is_linked for socket in self.inputs])
        return True

    def migrate_from(self, old_node):
        self.output_dimensions = old_node.dimensions
    def process(self):

        if not self.outputs[0].is_linked:
            return

        # if the user specifies a variable, they must also link a value into that socket, this will prevent Exception
        self.ui_message = ""
        if not self.all_inputs_connected():
            self.ui_message = "node not fully connected"
            return

        var_names = self.get_variables()
        inputs = self.get_input()
        results = []

        if var_names:
            input_values = [inputs.get(name) for name in var_names]
            matching_f = list_match_func[self.list_match]
            parameters = matching_f(input_values)
            desired_levels = [s.depth for s in self.inputs]
            ops = [self.formulas(), self.separate, var_names, [s.transform for s in self.inputs], self.as_list]

            results = recurse_f_level_control(parameters, ops, formula_func, matching_f, desired_levels)

        else:
            def joined_formulas(f1, f2, f3, f4):
                built_string = ""
                if f1: built_string += f1
                if f2: built_string += f",{f2}"
                if f3: built_string += f",{f3}"
                if f4: built_string += f",{f4}"
                return list(ast.literal_eval(built_string))

            if self.use_ast:
                results = joined_formulas(*self.formulas())
            else:
                vector = []
                for formula in self.formulas():
                    if formula:
                        value = safe_eval(formula, dict())
                        vector.append(value)
                results.extend(vector)

        if self.wrapping == "+1":
            results = [results]
        elif self.wrapping == "-1":
            results = results[0] if len(results) else results


        self.outputs['Result'].sv_set(results)

classes = [SvFormulaNodeMk5]
register, unregister = bpy.utils.register_classes_factory(classes)
