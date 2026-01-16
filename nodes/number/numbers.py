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

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.utils.nodes_mixins.draft_mode import DraftMode
from sverchok.utils.nodes_mixins.show_3d_properties import Show3DProperties


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


class SvNumberNode(Show3DProperties, DraftMode, SverchCustomTreeNode, bpy.types.Node):
    ''' Integer / Float input value. [default]
    mode: [float] / int
    limits float: min / max [-500/+500]
    limits int: min / max [-1024/+1024]
    a float: [0.] - input value
    '''
    bl_idname = 'SvNumberNode'
    bl_label = 'A Number'
    bl_icon = 'DOT'

    def wrapped_update(self, context):
        kind = self.selected_mode
        prop_name = kind + '_'
        self.inputs[0].replace_socket('SvStringsSocket', kind.title()).prop_name = prop_name
        self.outputs[0].replace_socket('SvStringsSocket', kind.title()).custom_draw = 'mode_custom_draw'
        updateNode(self, context)

    int_: IntProperty(
        default=0, name="an int", update=updateNode,
        description = "Integer value",
        get=lambda s: uget(s, 'int_'),
        set=lambda s, val: uset(s, val, 'int_', 'int_min', 'int_max')
    ) # type: ignore
    int_draft_ : IntProperty(
        default=0, name="[D] an int", update=updateNode,
        description = "Integer value (draft mode)",
        get=lambda s: uget(s, 'int_draft_'),
        set=lambda s, val: uset(s, val, 'int_draft_', 'int_min', 'int_max')
    ) # type: ignore
    int_min: IntProperty(
        default=-1024,
        description='minimum'
    ) # type: ignore
    int_max: IntProperty(
        default=1024,
        description='maximum'
    ) # type: ignore

    def update_precision(self, context):
        prop_name = self.get_prop_name()
        self.inputs["Float"].prop_name = prop_name
        # do not need update node
        pass

    precision_high: BoolProperty(default=False, name="Hight precision", description="Show input socket value with high precision and pricise mouse movement", update=update_precision)

    float_: FloatProperty(
        default=0.0, name="a float", update=updateNode,
        description = "Floating-point value",
        get=lambda s: uget(s, 'float_'),
        set=lambda s, val: uset(s, val, 'float_', 'float_min', 'float_max'),
    )
    float_p6: FloatProperty(
        default=0.0, name="a float", update=updateNode, precision=6, 
        description = "Floating-point high precision value",
        get=lambda s: uget(s, 'float_'),
        set=lambda s, val: uset(s, val, 'float_', 'float_min', 'float_max',),
        step=0.01, options={'SKIP_SAVE'},
    )

    float_draft_: FloatProperty(
        default=0.0, name="[D] a float",
        description = "Floating-point value (draft mode)",
        update=updateNode,
        get=lambda s: uget(s, 'float_draft_'),
        set=lambda s, val: uset(s, val, 'float_draft_', 'float_min', 'float_max'),
    )
    float_draft_p6: FloatProperty(
        default=0.0, name="[D] a float",
        description = "Floating-point value high precision value (draft mode)",
        update=updateNode, precision=6, 
        get=lambda s: uget(s, 'float_draft_'),
        set=lambda s, val: uset(s, val, 'float_draft_', 'float_min', 'float_max'),
        step=0.01, options={'SKIP_SAVE'},
    )
    
    float_min: FloatProperty(
        default=-500.0, description='minimum'
    ) # type: ignore
    float_max: FloatProperty(
        default=500.0,
        description='maximum'
    ) # type: ignore

    mode_options = [(k, k, '', i) for i, k in enumerate(["float", "int"])]

    selected_mode: bpy.props.EnumProperty(
        items=mode_options,
        default="float",
        update=wrapped_update
    ) # type: ignore

    show_limits: BoolProperty(
        default=False,
        description = "Show range of value"
    ) # type: ignore

    draft_properties_mapping = dict(float_ = 'float_draft_', int_ = 'int_draft_')

    def sv_init(self, context):
        self['float_'] = 0.0
        self['int_'] = 0
        self['float_draft_'] = 0.0
        self['int_draft_'] = 0
        self.inputs.new('SvStringsSocket', "Float").prop_name = 'float_'
        self.outputs.new('SvStringsSocket', "Float").custom_draw = 'mode_custom_draw'

    def mode_custom_draw(self, socket, context, layout):
        c1 = layout.column()
        r1 = c1.row(align=True)
        r1.prop(self, 'selected_mode', expand=True)
        r1.prop(self, "precision_high", text='', icon='MOD_HUE_SATURATION')
        r1.prop(self, 'show_limits', icon='SETTINGS', text='')
        if self.show_limits:
            c2 = c1.row().column(align=True)
            kind = self.selected_mode
            c2.prop(self, kind + '_min', text='min')
            c2.prop(self, kind + '_max', text='max')

    def get_prop_name(self):
        if self.id_data.sv_draft:
            if self.selected_mode == 'float':
                prop_name = 'float_draft_'
                if self.precision_high==True:
                    prop_name+='p6'
            else:
                prop_name = 'int_draft_'
        else:
            if self.selected_mode == 'float':
                prop_name = 'float_'
                if self.precision_high==True:
                    prop_name+='p6'
            else:
                prop_name = 'int_'
        return prop_name
    
    def draw_buttons(self, context, layout):
        #layout.label(text="1234")
        pass
    
    def draw_buttons_ext(self, context, layout):
        layout.prop(self, "draw_3dpanel", icon="PLUGIN")

        c1 = layout.column()
        r1 = c1.row(align=True)
        r1.prop(self, 'selected_mode', expand=True)
        r1.prop(self, "precision_high", text='', icon='MOD_HUE_SATURATION')
        #r1.prop(self, 'show_limits', icon='SETTINGS', text='')
        #if self.show_limits:
        c2 = c1.row().column(align=True)
        kind = self.selected_mode
        c2.prop(self, kind + '_min', text='min')
        c2.prop(self, kind + '_max', text='max')

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
                    label = f"Float: {value:.3f}"
                else:
                    label = f"Int: {value}"
            else:
                label = kind.title()
        else:
            label = self.label or self.name

        if self.id_data.sv_draft:
            label = f"[D] {label}"

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

    def does_support_draft_mode(self):
        return True


def register():
    bpy.utils.register_class(SvNumberNode)


def unregister():
    bpy.utils.unregister_class(SvNumberNode)

