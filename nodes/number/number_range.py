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

import bpy
from bpy.props import IntProperty, EnumProperty, FloatProperty, StringProperty, BoolProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, list_match_func, list_match_modes
import numpy as np


def range_step_stop(start, stop, step, n_type, out_numpy):
    '''Behaves like range but for floats'''
    step = max(1e-5, abs(step))
    if start > stop:
        step = -step
    result = np.arange(start, stop, step, dtype=n_type)
    return result if out_numpy else result.tolist()


def range_stop_count(start, stop, count, n_type, out_numpy):
    ''' Gives count total values in [start,stop] '''
    # we are casting to int here because the input can be floats.
    result = np.linspace(start, stop, num=count, dtype=n_type)
    return result if out_numpy else result.tolist()


def range_step_count(start, step, count, n_type, out_numpy):
    ''' Gives count values with step from start'''
    stop = start + step * count
    result = np.arange(start, stop, step, dtype=n_type)
    return result if out_numpy else result.tolist()


class SvGenNumberRange(bpy.types.Node, SverchCustomTreeNode):
    ''' Generator range list of floats'''
    bl_idname = 'SvGenNumberRange'
    bl_label = 'Number Range'
    bl_icon = 'IPO_LINEAR'

    start_float: FloatProperty(
        name='start', description='start',
        default=0, update=updateNode)

    stop_float: FloatProperty(
        name='stop', description='stop',
        default=10, update=updateNode)

    count_: IntProperty(
        name='count', description='number of items',
        default=10, min=1, update=updateNode)

    step_float: FloatProperty(
        name='step', description='step, difference among items',
        default=1.0, update=updateNode)
    start_int: IntProperty(
        name='start', description='start',
        default=0, update=updateNode)

    stop_int: IntProperty(
        name='stop', description='stop',
        default=10, update=updateNode)

    step_int: IntProperty(
        name='step', description='step, difference among items',
        default=1, min=1, update=updateNode)

    list_match: EnumProperty(
        name="List Match",
        description="Behavior on different list lengths",
        items=list_match_modes, default="REPEAT",
        update=updateNode)

    flat_output: BoolProperty(
        name="Flat output",
        description="Flatten output by list-joining level 1",
        default=True,
        update=updateNode)

    output_numpy: BoolProperty(
        name='Output NumPy',
        description='Output NumPy arrays',
        default=False, update=updateNode)

    current_mode: StringProperty(default="FLOATRANGE")
    main_modes = [
        ("int", "Int", "Integer Series", 1),
        ("float", "Float", "Float Series", 2),
    ]

    range_modes = [
        ("RANGE", "Range", "Define range by setting start, step and stop.", 1),
        ("RANGE_COUNT", "Count", "Define range by setting start, stop and count number (divisions).", 2),
        ("RANGE_STEP", "Step", "Define range by setting start, step and count number", 3),
    ]

    def mode_change(self, context):

        # just because click doesn't mean we need to change mode
        mode = self.number_mode + self.range_mode
        if mode == self.current_mode:
            return

        mode = self.range_mode
        self.inputs[0].prop_name = 'start_' + self.number_mode
        if mode == 'RANGE':

            self.inputs[1].prop_name = 'stop_' + self.number_mode
            self.inputs[2].prop_name = 'step_' + self.number_mode

        elif mode == 'RANGE_COUNT':
            self.inputs[1].prop_name = 'stop_' + self.number_mode
            self.inputs[2].prop_name = 'count_'

        else:
            self.inputs[1].prop_name = 'step_' + self.number_mode
            self.inputs[2].prop_name = 'count_'

        self.current_mode = mode
        updateNode(self, context)

    number_mode: EnumProperty(
        name='Number Type',
        items=main_modes,
        default='float',
        update=mode_change)

    range_mode: EnumProperty(
        name='Range Mode',
        items=range_modes,
        default='RANGE',
        update=mode_change)

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "Start").prop_name = 'start_float'
        self.inputs.new('SvStringsSocket', "Step").prop_name = 'stop_float'
        self.inputs.new('SvStringsSocket', "Stop").prop_name = 'step_float'

        self.outputs.new('SvStringsSocket', "Range")

    def draw_buttons(self, context, layout):
        layout.prop(self, "number_mode", expand=True)
        layout.prop(self, "range_mode", expand=True)
    def draw_buttons_ext(self, ctx, layout):
        layout.prop(self, "number_mode", expand=True)
        layout.prop(self, "range_mode", expand=True)
        layout.prop(self, "list_match", expand=False)
        layout.prop(self, "flat_output", expand=False)
        layout.prop(self, "output_numpy", expand=False)
    def rclick_menu(self, context, layout):
        layout.prop_menu_enum(self, "number_mode")
        layout.prop_menu_enum(self, "range_mode")
        layout.prop_menu_enum(self, "list_match", text="List Match")
        layout.prop(self, "flat_output", expand=False)
        layout.prop(self, "output_numpy", expand=False)

    range_func_dict = {'RANGE': range_step_stop,
                       'RANGE_COUNT': range_stop_count,
                       'RANGE_STEP': range_step_count}

    def migrate_from(self, old_node):
        if old_node.bl_idname == 'SvGenFloatRange':
            self.number_mode = 'float'
            self.start_float = old_node.start_
            self.stop_float = old_node.stop_
            self.step_float = old_node.step_
            self.count_ = old_node.count_
        else:
            self.number_mode = 'int'
            self.start_int = old_node.start_
            self.stop_int = old_node.stop_
            self.step_int = old_node.step_
            self.count_ = old_node.count_
        if old_node.mode in ['FRANGE','LAZYRANGE']:
            self.range_mode = 'RANGE'
        elif  old_node.mode == 'FRANGE_COUNT':
            self.range_mode = 'RANGE_COUNT'
        else:
            self.range_mode = "RANGE_STEP"

    def process(self):
        inputs = self.inputs
        outputs = self.outputs
        if not outputs[0].is_linked:
            return
        matching_f = list_match_func[self.list_match]
        params = [s.sv_get() for s in inputs]
        if self.number_mode == 'int':
            dtype = np.int64
            current_func = self.range_func_dict[self.range_mode]
        else:
            dtype = np.float64
            current_func = self.range_func_dict[self.range_mode]

        result =[]
        add_f = result.extend if self.flat_output else result.append
        out_numpy = self.output_numpy
        for p in zip(*matching_f(params)):

            out = [current_func(*args, dtype, out_numpy) for args in zip(*matching_f(p))]
            add_f(out)

        outputs['Range'].sv_set(result)


def register():
    bpy.utils.register_class(SvGenNumberRange)


def unregister():
    bpy.utils.unregister_class(SvGenNumberRange)
