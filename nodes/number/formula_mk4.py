# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from math import *
from collections import defaultdict

import bpy
from bpy.props import BoolProperty, StringProperty, EnumProperty, FloatVectorProperty, IntProperty
import json
import io

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, match_long_repeat, zip_long_repeat
from sverchok.utils import logging
from sverchok.utils.modules.eval_formula import get_variables, safe_eval

class SvFormulaNodeMk4(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Formula
    Tooltip: Calculate by custom formula.
    """
    bl_idname = 'SvFormulaNodeMk4'
    bl_label = 'Formula+'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_FORMULA'

    @throttled
    def on_update(self, context):
        self.adjust_sockets()

    @throttled
    def on_update_dims(self, context):
        if self.dimensions < 4:
            self.formula4 = ""
        if self.dimensions < 3:
            self.formula3 = ""
        if self.dimensions < 2:
            self.formula2 = ""

        self.adjust_sockets()

    dimensions : IntProperty(name="Dimensions", default=1, min=1, max=4, update=on_update_dims)

    formula1 : StringProperty(default="x+y", update=on_update)
    formula2 : StringProperty(update=on_update)
    formula3 : StringProperty(update=on_update)
    formula4 : StringProperty(update=on_update)

    separate : BoolProperty(name="Separate", default=False, update=updateNode)
    wrap : BoolProperty(name="Wrap", default=False, update=updateNode)

    def formulas(self):
        return [self.formula1, self.formula2, self.formula3, self.formula4]

    def formula(self, k):
        return self.formulas()[k]

    def draw_buttons(self, context, layout):
        layout.prop(self, "formula1", text="")
        if self.dimensions > 1:
            layout.prop(self, "formula2", text="")
        if self.dimensions > 2:
            layout.prop(self, "formula3", text="")
        if self.dimensions > 3:
            layout.prop(self, "formula4", text="")
        row = layout.row()
        row.prop(self, "separate")
        row.prop(self, "wrap")

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, "dimensions")
        self.draw_buttons(context, layout)

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "x")

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
        if len(self.inputs) == variables:
            if list(sorted(variables)) == [socket.name for socket in self.inputs]:
                self.info("no UI change: socket inputs same")
                return

        # else to avoid making things complicated we rebuild the UI inputs, even when it is technically sub optimal
        self.hot_reload_sockets(context)

    def clear_and_repopulate_sockets_from_variables(self, context):
        with self.sv_throttle_tree_update():
            self.inputs.clear()
            variables = self.get_variables()
            for v in variables:
                self.inputs.new('SvStringsSocket', v)

    def hot_reload_sockets(self, context):
        """
        function hoisted from functorb, with deletions and edits
        
         - store current input socket links by name/origin
         - wipe all inputs
         - recreate new sockets from variables
         - relink former links by name on this socket, but by index from their origin.
        
        """
        
        self.info('handling input wipe and relink')
        node = self
        nodes = self.id_data.nodes

        # if any current connections... gather them 
        reconnections = []
        for i in (i for i in node.inputs if i.is_linked):
            for L in i.links:
                link = lambda: None
                link.from_node = L.from_socket.node.name
                link.from_socket = L.from_socket.index   # index used here because these can come from reroute
                link.to_node = L.to_socket.node.name
                link.to_socket = L.to_socket.name        # this node will always have unique socket names
                reconnections.append(link)

        self.clear_and_repopulate_sockets_from_variables(context)

        # restore connections where applicable (by socket name), if no links.. this is a no op.
        node_tree = self.id_data
        for link in reconnections:
            try:
                from_part = nodes[link.from_node].outputs[link.from_socket]
                to_part = nodes[link.to_node].inputs[link.to_socket]
                node_tree.links.new(from_part, to_part)
            except Exception as err:
                str_from = f'nodes[{link.from_node}].outputs[{link.from_socket}]'
                str_to = f'nodes[{link.to_node}].inputs[{link.to_socket}]'
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

    def migrate_from(self, old_node):
        if old_node.bl_idname == 'Formula2Node':
            formula = old_node.formula
            # Older formula node allowed only fixed set of
            # variables, with names "x", "n[0]" .. "n[100]".
            # Other names could not be considered valid.
            k = -1
            for socket in old_node.inputs:
                name = socket.name
                if k == -1: # First socket name was "x"
                    new_name = name
                else: # Other names was "n[k]", which is syntactically not
                      # a valid python variable name.
                      # So we replace all occurences of "n[0]" in formula
                      # with "n0", and so on.
                    new_name = "n" + str(k)

                logging.info("Replacing %s with %s", name, new_name)
                formula = formula.replace(name, new_name)
                k += 1

            self.formula1 = formula
            self.wrap = True

    def process(self):

        if not self.outputs[0].is_linked:
            return

        var_names = self.get_variables()
        inputs = self.get_input()

        results = []

        if var_names:
            input_values = [inputs.get(name, [[0]]) for name in var_names]
            parameters = match_long_repeat(input_values)
        else:
            parameters = [[[None]]]
        for objects in zip(*parameters):
            object_results = []
            for values in zip_long_repeat(*objects):
                variables = dict(zip(var_names, values))
                vector = []
                for formula in self.formulas():
                    if formula:
                        value = safe_eval(formula, variables)
                        vector.append(value)
                if self.separate:
                    object_results.append(vector)
                else:
                    object_results.extend(vector)
            results.append(object_results)

        if self.wrap:
            results = [results]

        self.outputs['Result'].sv_set(results)

classes = [SvFormulaNodeMk4]
register, unregister = bpy.utils.register_classes_factory(classes)
