# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.utils.nodes_mixins.show_3d_properties import Show3DProperties


class SvCustomSwitcherMK2(Show3DProperties, SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: custom switcher
    Convert input to buttons

    Output shows selected items
    """
    bl_idname = 'SvCustomSwitcherMK2'
    bl_label = 'Switcher'
    bl_icon = 'HAND'

    def update_mode(self, context):
        # Select only one item in non multiple selection mode
        if not self.multiple_selection:
            self['previous_user_list'] = [False for _ in range(32)]
            self.user_list = [False for _ in range(32)]

    def get_user_list(self):
        return self['user_list']

    def set_user_list(self, values):
        # Implementation of single selection mode
        if not self.multiple_selection:
            values = [True if not old and new or old and not new else False
                      for old, new in zip(self['previous_user_list'], values)]
            self['previous_user_list'] = values
        self['user_list'] = values

    multiple_selection: bpy.props.BoolProperty(
        name='Multiple selection', default=True, update=update_mode,
        description='Selection several items simultaneously')

    masked: bpy.props.BoolProperty(
        name='Masked', default=False, update=updateNode,
        description='To use masks or not to use masks')

    ui_scale: bpy.props.FloatProperty(
        name='Size of buttons', default=1.0, min=0.5, max=5)

    string_values: bpy.props.CollectionProperty(
        type=bpy.types.PropertyGroup, description='Storage of items names')

    user_list: bpy.props.BoolVectorProperty(
        name="User selection", size=32, update=updateNode, set=set_user_list,
        get=get_user_list, description='Selection status of items')

    def sv_init(self, context):
        self['user_list'] = [False for _ in range(32)]
        self['previous_user_list'] = [False for _ in range(32)]
        self.inputs.new('SvStringsSocket', 'Data')
        self.inputs.new('SvStringsSocket', 'Mask')

        self.outputs.new('SvStringsSocket', 'Item')

    def draw_buttons(self, context, layout):
        col = layout.column(align=True)
        col.scale_y = self.ui_scale
        for i, val in enumerate(self.string_values):
            col.prop(self, "user_list", toggle=True, index=i, text=val.name)
        if self.inputs['Mask'].is_linked:
            row = layout.row(align=True)
            row.prop(self, "masked", text='Use mask')

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, "draw_3dpanel", icon="PLUGIN")
        row = layout.row()
        row.scale_y = 2
        row.prop(self, 'multiple_selection', toggle=True)
        layout.prop(self, 'ui_scale', text='Size of buttons')

    def draw_buttons_3dpanel(self, layout, in_menu=None):
        # I think it is more appropriate place for coding layout of 3d panel
        if not in_menu:
            row = layout.row(align=True)

            menu = row.operator('node.popup_3d_menu', text=f'Show "{self.label or self.name}"', icon=self.bl_icon)
            menu.tree_name = self.id_data.name
            menu.node_name = self.name
        else:
            col = layout.column(align=True)
            row = col.row(align=True)
            row.label(text=self.label or self.name)
            row.prop(self, 'multiple_selection', toggle=True, text='multiselect',
                     icon='SNAP_ON' if self.multiple_selection else 'SNAP_OFF')
            row.prop(self, 'masked', toggle=True, text='use mask',
                     icon='VIEW_PAN' if self.masked else 'SPREADSHEET')
            if not self.masked:
                for i, val in enumerate(self.string_values):
                    col.prop(self, "user_list", toggle=True, index=i, text=val.name)

    def process(self):
        # Storing names of items
        if self.inputs['Data'].is_linked:
            data = self.inputs['Data'].sv_get()
            if isinstance(data[0], (list, tuple)):
                data = [i for l in data for i in l]
            if len(data) != len(self.string_values):
                self.string_values.clear()
                for i, val in enumerate(data):
                    if i == 32:
                        break
                    self.string_values.add().name = str(val)
            else:
                for val, str_val in zip(data, self.string_values):
                    str_val.name = str(val)
        else:
            self.string_values.clear()

        # --- Modification 2026.01.06: Update user_list based on Mask input ---
        if self.inputs['Mask'].is_linked and self.inputs['Data'].is_linked and self.masked:
            mask_data = self.inputs['Mask'].sv_get()
            # Check if mask_data is not empty to allow manual override when [] is passed
            if mask_data and mask_data[0]:
                # Handle standard Sverchok nested list structure
                flat_mask = mask_data[0] if isinstance(mask_data[0], (list, tuple)) else mask_data
                new_values = [False] * 32
                for i, val in enumerate(flat_mask):
                    if i < 32:
                        new_values[i] = bool(val)
                
                # Enforce single selection logic if multiple_selection is False
                if not self.multiple_selection:
                    found = False
                    for i in range(32):
                        if new_values[i] and not found:
                            found = True
                        else:
                            new_values[i] = False

                # Update ID-properties directly to bypass the toggle logic in the setter
                if list(self['user_list']) != new_values:
                    self['user_list'] = new_values
                    self['previous_user_list'] = new_values
        # --- Modification end ---

        self.outputs['Item'].sv_set([[i for i, b in enumerate(self.user_list[:len(self.string_values)]) if b]])


def register():
    bpy.utils.register_class(SvCustomSwitcherMK2)


def unregister():
    bpy.utils.unregister_class(SvCustomSwitcherMK2)
if __name__ == '__main__': register()