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
from bpy.props import BoolProperty, FloatVectorProperty, StringProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import dataCorrect, node_id, updateNode
from sverchok.ui import nodeview_bgl_viewer_draw_mk2 as nvBGL
from mathutils import Vector


# status colors
FAIL_COLOR = (0.1, 0.05, 0)
READY_COLOR = (1, 0.3, 0)


def high_contrast_color(c):
    g = 2.2  # gamma
    L = 0.2126 * (c.r**g) + 0.7152 * (c.g**g) + 0.0722 * (c.b**g)
    return [(.1, .1, .1), (.95, .95, .95)][int(L < 0.5)]


class SvStethoscopeNodeMK2(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvStethoscopeNodeMK2'
    bl_label = 'Stethoscope MK2'
    bl_icon = 'OUTLINER_OB_EMPTY'

    # node id
    n_id = StringProperty(default='')

    text_color = FloatVectorProperty(
        name="Color", description='Text color',
        size=3, min=0.0, max=1.0,
        default=(.1, .1, .1), subtype='COLOR',
        update=updateNode)

    activate = BoolProperty(
        name='Show', description='Activate node?',
        default=True,
        update=updateNode)

    view_by_element = BoolProperty(update=updateNode)
    num_elements = IntProperty(default=0)
    element_index = IntProperty(default=0, update=updateNode)
    rounding = IntProperty(min=1, max=5, default=3, update=updateNode)

    def avail_nodes(self, context):
        ng = self.id_data
        return [(n.name, n.name, "") for n in ng.nodes]

    def avail_sockets(self, context):
        if self.node_name:
            node = self.id_data.nodes.get(self.node_name)
            if node:
                return [(s.name, s.name, "") for s in node.inputs if s.links]
        else:
            return [("", "", "")]

    # node_name = EnumProperty(items=avail_nodes, name="Node")
    # socket_name = EnumProperty(items=avail_sockets, name="Sockets",update=updateNode)

    def sv_init(self, context):
        self.inputs.new('StringsSocket', 'Data')
        try:
            current_theme = bpy.context.user_preferences.themes.items()[0][0]
            editor = bpy.context.user_preferences.themes[current_theme].node_editor
            self.text_color = high_contrast_color(editor.space.back)
        except:
            print('-', end='')

    # reset n_id on copy
    def copy(self, node):
        self.n_id = ''

    def draw_buttons(self, context, layout):
        row = layout.row()
        icon = 'RESTRICT_VIEW_OFF' if self.activate else 'RESTRICT_VIEW_ON'
        row.separator()
        row.prop(self, "activate", icon=icon, text='')
        row.prop(self, "text_color", text='')
        layout.prop(self, "rounding")
        # layout.prop(self, "socket_name")
        layout.label('input has {0} elements'.format(self.num_elements))
        layout.prop(self, 'view_by_element', toggle=True)
        if self.num_elements > 0 and self.view_by_element:
            layout.prop(self, 'element_index', text='get index')

    def process(self):
        inputs = self.inputs
        n_id = node_id(self)

        # end early
        nvBGL.callback_disable(n_id)

        if self.activate and inputs[0].is_linked:
            # gather vertices from input
            data = inputs[0].sv_get(deepcopy=False)
            self.num_elements = len(data)

            lines = nvBGL.parse_socket(inputs[0], self.rounding, self.element_index, self.view_by_element)
            draw_data = {
                'tree_name': self.id_data.name[:],
                'content': lines,
                'location': (self.location + Vector((self.width + 20, 0)))[:],
                'color': self.text_color[:],
            }
            nvBGL.callback_enable(n_id, draw_data)

    def free(self):
        nvBGL.callback_disable(node_id(self))


def register():
    bpy.utils.register_class(SvStethoscopeNodeMK2)


def unregister():
    bpy.utils.unregister_class(SvStethoscopeNodeMK2)
