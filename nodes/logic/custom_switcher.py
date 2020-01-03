# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode


class SvCustomSwitcher(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: custom switcher
    Convert input to buttons

    Output shows selected items
    """
    bl_idname = 'SvCustomSwitcher'
    bl_label = 'Switcher'
    bl_icon = 'HAND'

    def update_mode(self, context):
        # Select only one item in non multiple selection mode
        if not self.multiple_selection:
            self['previous_user_list'] = [False for _ in range(32)]
            self.user_list = [True] + [False for _ in range(31)]

    def get_user_list(self):
        return self['user_list']

    def set_user_list(self, values):
        # Implementation of single selection mode
        if not self.multiple_selection:
            values = [True if not old and new or old and not new else False
                      for old, new in zip(self['previous_user_list'], values)]
            self['previous_user_list'] = values
        self['user_list'] = values

    to3d: bpy.props.BoolProperty(name='Show in 3d panel', default=True,
                                  description='Show items of this node in 3d panel of 3d view screen')
    multiple_selection: bpy.props.BoolProperty(name='Multiple selection', default=True, update=update_mode,
                                                description='Selection several items simultaneously')
    ui_scale: bpy.props.FloatProperty(name='Size of buttons', default=1.0, min=0.5, max=5)
    string_values: bpy.props.CollectionProperty(type=bpy.types.PropertyGroup, description='Storage of items names')
    user_list: bpy.props.BoolVectorProperty(name="User selection", size=32, update=updateNode, set=set_user_list,
                                             get=get_user_list, description='Selection status of items')
    show_in_3d: bpy.props.BoolProperty(name='show in panel', default=True,
                                        description='Show properties in 3d panel or not')

    def sv_init(self, context):
        self['user_list'] = [False for _ in range(32)]
        self['previous_user_list'] = [False for _ in range(32)]
        self.inputs.new('SvStringsSocket', 'Data')
        self.outputs.new('SvStringsSocket', 'Item')

    def draw_buttons(self, context, layout):
        col = layout.column(align=True)
        col.scale_y = self.ui_scale
        for i, val in enumerate(self.string_values):
            col.prop(self, "user_list", toggle=True, index=i, text=val.name)

    def draw_buttons_ext(self, context, layout):
        row = layout.row()
        row.scale_y = 2
        row.prop(self, 'multiple_selection', toggle=True)
        layout.prop(self, 'to3d', toggle=True)
        layout.prop(self, 'ui_scale', text='Size of buttons')

    @property
    def draw_3dpanel(self):
        return True if self.to3d and self.inputs[0].is_linked else False

    def draw_buttons_3dpanel(self, layout):
        # I think it is moore appropriate place for coding layout of 3d panel
        col = layout.column()
        row = col.row(align=True)
        name = self.label if self.label else self.name
        switch_icon = 'DOWNARROW_HLT' if self.show_in_3d else 'RIGHTARROW'
        row.prop(self, 'show_in_3d', text=name, icon=switch_icon)
        mode_icon = 'SNAP_ON' if self.multiple_selection else 'SNAP_OFF'
        row.prop(self, 'multiple_selection', toggle=True, text='', icon=mode_icon)
        if self.show_in_3d:
            col = layout.column(align=True)
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

        self.outputs['Item'].sv_set([[i for i, b in enumerate(self.user_list) if b]])


def register():
    bpy.utils.register_class(SvCustomSwitcher)


def unregister():
    bpy.utils.unregister_class(SvCustomSwitcher)
