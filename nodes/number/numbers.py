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


def uget(self, origin):
    return self[origin]

def uset(self, value, origin):
    MAX = getattr(self, origin + 'max')
    MIN = getattr(self, origin + 'min')
    if MIN <= value <= MAX:
        self[origin] = value
    elif value > MAX:
        self[origin] = MAX
    else:
        self[origin] = MIN
    return None

class SvNumberNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Float '''
    bl_idname = 'SvNumberNode'
    bl_label = 'A Number'
    bl_icon = 'OUTLINER_OB_EMPTY'

    def wrapped_update(self, context):
        kind = self.selected_mode
        prop = kind + '_'
        self.inputs[0].replace_socket('StringsSocket', kind.title()).prop_name = prop
        self.outputs[0].replace_socket('StringsSocket', kind.title()).custom_draw = 'mode_custom_draw'
        self.process_node(context)

    int_ = IntProperty(
        default=0, name="", update=updateNode,
        get=lambda s: uget(s, 'int_'), set=lambda s, val: uset(s, val, 'int_')) 
    int_min = IntProperty(default=-1024, description='minimum')
    int_max = IntProperty(default=1024, description='maximum')

    float_ = FloatProperty(
        default=0.0, name="", update=updateNode,
        get=lambda s: uget(s, 'float_'), set=lambda s, val: uset(s, val, 'float_'))
    float_min = FloatProperty(default=-500.0, description='minimum')
    float_max = FloatProperty(default=500.0, description='maximum')

    mode_options = [(k, k, '', i) for i, k in enumerate(["float", "int"])]
    
    selected_mode = bpy.props.EnumProperty(
        items=mode_options, default="float", update=wrapped_update)

    show_limits = BoolProperty(default=False)

    def sv_init(self, context):
        self.inputs.new('StringsSocket', "Float").prop_name = 'float_'
        self.outputs.new('StringsSocket', "Float").custom_draw = 'mode_custom_draw'

    # def draw_buttons(self, context, layout):
    #     if self.show_limits:
    #         r2 = layout.row(align=True)
    #         kind = self.selected_mode
    #         r2.prop(self, kind + '_min', text='')
    #         r2.prop(self, kind + '_max', text='')

    def mode_custom_draw(self, context, layout):
        r = layout.row(align=True)
        if not self.show_limits:
            r.prop(self, 'selected_mode', expand=True)
        else:
            kind = self.selected_mode
            r.prop(self, kind + '_min', text='')
            r.prop(self, kind + '_max', text='')
        r.prop(self, 'show_limits', icon='SETTINGS', text='')

    # def draw_label(self):
    #     # if not self.inputs[0].links:
    #     #     return str(round(self.float_, 3))
    #     # else:
    #     #     return self.bl_label
    #     return 'yes'
            
    def process(self):
        # inputs
        # Float = min(max(float(self.inputs[0].sv_get()[0][0]), self.minim), self.maxim)

        if not self.inputs[0].is_linked:
            kind = self.selected_mode + '_'
            self.outputs[0].sv_set([[getattr(self, kind)]])
        else:
            found_data = self.inputs[0].sv_get()

            # if found data contains ints, but the mode is float then auto cast..
            # same for float to int.

            self.outputs[0].sv_set(self.inputs[0].sv_get())




def register():
    bpy.utils.register_class(SvNumberNode)


def unregister():
    bpy.utils.unregister_class(SvNumberNode)



