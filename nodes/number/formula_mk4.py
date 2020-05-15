# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

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

        return list(sorted(list(variables)))

    def adjust_sockets(self):
        variables = self.get_variables()

        # [ ] if current node sockets match the variables sequence, do nothing skip
        #     - this is the logic path that will be encountered most often.
        # [ ] else to avoid making things complicated we rebuild the UI inputs, even when it is 
        #     - technically sub optimal
        #     [ ] store current input socket links by name/origin
        #     [ ] wipe all inputs
        #     [ ] recreate new sockets from variables
        #     [ ] relink former links by name

        for key in self.inputs.keys():
            if (key not in variables) and (key in self.inputs):
                self.debug("Input {} not in variables {}, remove it".format(key, str(variables)))
                self.inputs.remove(self.inputs[key])
        for v in variables:
            if v not in self.inputs:
                self.debug("Variable {} not in inputs {}, add it".format(v, str(self.inputs.keys())))
                self.inputs.new('SvStringsSocket', v)

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


def register():
    bpy.utils.register_class(SvFormulaNodeMk4)


def unregister():
    bpy.utils.unregister_class(SvFormulaNodeMk4)
