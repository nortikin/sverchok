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

"""
EisenScript node for Sverchok.

Provides access to the EisenScript interpreter. Select a Blender text
block containing an EisenScript program, and the node outputs one
matrix socket per primitive type (box, sphere, grid, line, point,
triangle). Each socket carries a list of 4×4 placement matrices.
"""

from collections import defaultdict

import bpy
from bpy.props import BoolProperty, IntProperty, StringProperty, PointerProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.core.sv_custom_exceptions import SvNoDataError
from sverchok.utils.sv_node_utils import sync_pointer_and_stored_name
from sverchok.data_structure import updateNode, match_long_repeat

from sverchok.utils.modules.eisenscript import parse, Interpreter


# Canonical primitive names (keys in InterpreterResult.matrices)
_PRIMITIVE_NAMES = ("box", "grid", "sphere", "line", "point", "triangle")


class SvEisenscriptNode(SverchCustomTreeNode, bpy.types.Node):
    """EisenScript interpreter node."""
    bl_idname = 'SvEisenscriptNode'
    bl_label = 'EisenScript'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_GENERATIVE_ART'

    # --- bpy properties ---

    filename: StringProperty(
        name="Script",
        description="Blender text block with EisenScript source",
        default="",
        update=updateNode,
    )

    def pointer_update(self, context):
        if self.file_pointer:
            self.filename = self.file_pointer.name
        else:
            self.filename = ""
        self.adjust_sockets()
        updateNode(self, context)

    file_pointer: PointerProperty(
        type=bpy.types.Text, poll=lambda s, o: True, update=pointer_update)

    seed: IntProperty(
        name="Seed",
        description="Random seed for weighted rule selection",
        default=0,
        min=0,
        update=updateNode,
    )

    max_depth: IntProperty(
        name="Max depth",
        description="Global recursion depth limit (overrides set maxdepth)",
        default=8,
        min=1,
        update=updateNode,
    )

    max_objects: IntProperty(
        name="Max objects",
        description="Hard cap on total primitive instances (0 = unlimited)",
        default=1000,
        min=0,
        update=updateNode,
    )

    origin_as_center: BoolProperty(
        name="Origin center",
        description="Use (0,0,0) as transform center (legacy LSystem behavior). "
                    "If off, use (0.5,0.5,0.5) per EisenScript spec",
        default=True,
        update=updateNode,
    )

    # --- UI ---

    def draw_buttons(self, context, layout):
        col = layout.column(align=True)
        col.prop_search(self, 'file_pointer', bpy.data, 'texts', text='', icon='TEXT')
        col.separator()
        col.prop(self, "seed", text="Seed")
        col.prop(self, "max_depth", text="Max depth")
        col.prop(self, "max_objects", text="Max objects")
        #col.prop(self, "origin_as_center", text="Origin center")

    # --- Socket management ---

    def sv_init(self, context):
        # No inputs
        # Fixed outputs — one per primitive type
        for name in _PRIMITIVE_NAMES:
            self.outputs.new('SvMatrixSocket', name.capitalize())

    def load_script(self):
        if not self.filename:
            return None

        # we do not store stripped self.filename, else prop_search will shows it as read
        internal_file = bpy.data.texts[self.filename.strip()]
        source = internal_file.as_string()
        return parse(source)

    def get_variables(self):
        variables = set()
        program = self.load_script()
        if not program:
            return variables

        return list(sorted(program.inputs))

    def get_optional_inputs(self, program):
        result = set()
        if not program:
            return result
        for key, input_def in program.inputs.items():
            if input_def.default_value is not None:
                result.add(key)
        return result

    def adjust_sockets(self):
        variables = self.get_variables()
        #self.debug("adjust_sockets:" + str(variables))
        #self.debug("inputs:" + str(self.inputs.keys()))
        for key in self.inputs.keys():
            if key not in variables:
                self.debug("Input {} not in variables {}, remove it".format(key, str(variables)))
                self.safe_socket_remove('inputs', key)
        for v in variables:
            if v not in self.inputs:
                self.debug("Variable {} not in inputs {}, add it".format(v, str(self.inputs.keys())))
                self.inputs.new('SvStringsSocket', v)

    def sv_update(self):
        '''
        update analyzes the state of the node and returns if the criteria to start processing
        are not met.
        '''

        # keeping the file internal for now.
        if not (self.filename.strip() in bpy.data.texts):
            return

        self.adjust_sockets()

    # --- Processing ---

    def get_input(self):
        variables = self.get_variables()
        result = {}

        for var in variables:
            if var in self.inputs and self.inputs[var].is_linked:
                result[var] = self.inputs[var].sv_get()[0]
        return result

    def process(self):
        if not self.filename or self.filename not in bpy.data.texts:
            for name in _PRIMITIVE_NAMES:
                self.outputs[name.capitalize()].sv_set([[]])
            return

        if not any(out.is_linked for out in self.outputs):
            return

        sync_pointer_and_stored_name(self, "file_pointer", "filename")

        # Build interpreter with user overrides.
        # Node properties take precedence over program settings.
        max_objects_val = self.max_objects if self.max_objects > 0 else None

        program = self.load_script()
        optional_inputs = self.get_optional_inputs(program)
        self.info("Inputs: %s", program.inputs)

        var_names = self.get_variables()
        self.info("Var_names: %s; optional: %s", var_names, optional_inputs)
        inputs = self.get_input()
        outputs = defaultdict(list)

        if var_names:
            input_values = []
            for name in var_names:
                try:
                    input_values.append(inputs[name])
                except KeyError as e:
                    name = e.args[0]
                    if name not in optional_inputs:
                        if name in self.inputs:
                            raise SvNoDataError(self.inputs[name])
                        else:
                            self.adjust_sockets()
                            raise SvNoDataError(self.inputs[name])
                    else:
                        input_values.append([None])
            parameters = match_long_repeat(input_values)
        else:
            parameters = [[[]]]

        for values in zip(*parameters):
            input_values = dict([(name, value) for name, value in zip(var_names, values) if value is not None])
            self.info("Inputs: %s", input_values)

            result = Interpreter.interpret(
                program,
                max_depth=self.max_depth,
                max_objects=max_objects_val,
                seed=self.seed,
                origin_as_center=self.origin_as_center,
                input_values = input_values
            )

            # Output matrices per primitive
            for name in _PRIMITIVE_NAMES:
                mats = result.matrices.get(name, [])
                out_socket_name = name.capitalize()
                outputs[out_socket_name].append(mats)

        for out_socket_name in outputs:
            self.outputs[out_socket_name].sv_set(outputs[out_socket_name])

    def load_from_json(self, node_data: dict, import_version: float):
        if 'program' not in node_data:
            return  # looks like a node was empty when it was exported
        program = node_data['program']

        filename = self.filename

        bpy.data.texts.new(filename)
        bpy.data.texts[filename].clear()
        bpy.data.texts[filename].write(program)
        self.file_pointer = bpy.data.texts[filename]

    def save_to_json(self, node_data: dict):
        if self.filename and self.filename.strip() in bpy.data.texts:
            text = bpy.data.texts[self.filename.strip()].as_string()
            node_data['program'] = text
        else:
            self.warning("save_to_json called with unknown filename")

    def set_filename_to_match_file_pointer(self):
        self.file_pointer = self.file_pointer


def register():
    bpy.utils.register_class(SvEisenscriptNode)


def unregister():
    bpy.utils.unregister_class(SvEisenscriptNode)
