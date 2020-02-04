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
from bpy.props import FloatProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode


def uget(self, origin):
    return self[origin]

def uset(self, value, origin, min_prop, max_prop):
    MAX = getattr(self, max_prop)
    MIN = getattr(self, min_prop)

    # rudimentary min max flipping
    MAX, MIN = (MAX, MIN) if MAX >= MIN else (MIN, MAX)

    if MIN <= value <= MAX:
        self[origin] = value
    elif value > MAX:
        self[origin] = MAX
    else:
        self[origin] = MIN
    return None


class SvNumberNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Integer  / Float '''
    bl_idname = 'SvNumberNode'
    bl_label = 'A Number'
    bl_icon = 'DOT'

    @throttled
    def wrapped_update(self, context):
        kind = self.selected_mode
        prop_name = kind + '_'
        inp = self.inputs[0].replace_socket('SvStringsSocket', kind.title())
        inp.prop_name = prop_name
        inp.prop_name_draft = prop_name + 'draft_'
        self.outputs[0].replace_socket('SvStringsSocket', kind.title()).custom_draw = 'mode_custom_draw'

    int_: IntProperty(
        default=0, name="an int", update=updateNode,
        description = "Integer value",
        get=lambda s: uget(s, 'int_'),
        set=lambda s, val: uset(s, val, 'int_', 'int_min', 'int_max'))
    int_draft_ : IntProperty(
        default=0, name="an int", update=updateNode,
        description = "Integer value (draft mode)",
        get=lambda s: uget(s, 'int_draft_'),
        set=lambda s, val: uset(s, val, 'int_draft_', 'int_min', 'int_max'))
    int_min: IntProperty(default=-1024, description='minimum')
    int_max: IntProperty(default=1024, description='maximum')

    float_: FloatProperty(
        default=0.0, name="a float", update=updateNode,
        description = "Floating-point value",
        get=lambda s: uget(s, 'float_'),
        set=lambda s, val: uset(s, val, 'float_', 'float_min', 'float_max'))
    float_draft_: FloatProperty(
        default=0.0, name="a float",
        description = "Floating-point value (draft mode)",
        update=updateNode,
        get=lambda s: uget(s, 'float_draft_'),
        set=lambda s, val: uset(s, val, 'float_draft_', 'float_min', 'float_max'))
    float_min: FloatProperty(default=-500.0, description='minimum')
    float_max: FloatProperty(default=500.0, description='maximum')

    mode_options = [(k, k, '', i) for i, k in enumerate(["float", "int"])]

    selected_mode: bpy.props.EnumProperty(
        items=mode_options, default="float", update=wrapped_update)

    show_limits: BoolProperty(default=False)
    to3d: BoolProperty(default=False, update=updateNode)

    def sv_init(self, context):
        self['float_'] = 0.0
        self['int_'] = 0
        self['float_draft_'] = 0.0
        self['int_draft_'] = 0
        inp = self.inputs.new('SvStringsSocket', "Float")
        inp.prop_name = 'float_'
        inp.prop_name_draft = 'float_draft_'
        self.outputs.new('SvStringsSocket', "Float").custom_draw = 'mode_custom_draw'

    def mode_custom_draw(self, socket, context, layout):

        if not self.show_limits:
            r = layout.row(align=True)
            r.prop(self, 'selected_mode', expand=True)
            r.prop(self, 'show_limits', icon='SETTINGS', text='')
        else:
            c = layout.column(align=True)
            kind = self.selected_mode
            c.prop(self, kind + '_min', text='min')
            c.prop(self, kind + '_max', text='max')
            c = layout.column()
            c.prop(self, 'show_limits', icon='SETTINGS', text='')

            c.prop(self, 'to3d', icon='PLUGIN', text='')

    def draw_buttons_ext(self, context, layout):
        c = layout.column(align=True)
        c.prop(self, 'to3d', icon='PLUGIN', text='to 3dview')

    @property
    def draw_3dpanel(self):
        return False if self.inputs[0].is_linked or not self.outputs[0].is_linked or not self.to3d else True
    
    def get_prop_name(self):
        if self.id_data.sv_draft:
            if self.selected_mode == 'float':
                prop_name = 'float_draft_'
            else:
                prop_name = 'int_draft_'
        else:
            if self.selected_mode == 'float':
                prop_name = 'float_'
            else:
                prop_name = 'int_'
        return prop_name

    def draw_buttons_3dpanel(self, layout):
        row = layout.row(align=True)
        prop_name = self.get_prop_name()
        row.prop(self, prop_name,
                 text=self.label if self.label else self.name)
        colo = row.row(align=True)
        colo.scale_x = 0.8
        if self.show_limits:
            colo.prop(self, self.selected_mode + '_min', text='', slider=True, emboss=False)
            colo.prop(self, self.selected_mode + '_max', text='', slider=True, emboss=False)
        colo.prop(self, 'show_limits', icon='SETTINGS', text='')

    def draw_label(self):
        prop_name = self.get_prop_name()
        kind = self.selected_mode

        if self.hide:
            if not self.inputs[0].links:
                value = getattr(self, prop_name)
                if kind == 'float':
                    label = 'Float: ' + str(round(value, 3))
                else:
                    label = 'Int: ' + str(value)
            else:
                label = kind.title()
        else:
            label = self.label or self.name

        if self.id_data.sv_draft:
            label = "[D] " + label

        return label


    def process(self):

        if not self.inputs[0].is_linked:
            prop_name = self.get_prop_name()
            self.outputs[0].sv_set([[getattr(self, prop_name)]])
        else:
            # found_data = self.inputs[0].sv_get()

            # if found data contains ints, but the mode is float then auto cast..
            # same for float to int.

            self.outputs[0].sv_set(self.inputs[0].sv_get())


def register():
    bpy.utils.register_class(SvNumberNode)


def unregister():
    bpy.utils.unregister_class(SvNumberNode)

