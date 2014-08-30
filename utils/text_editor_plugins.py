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

import re

import bpy

sv_error_message = '''\
______________Sverchok Script Generator Node rules_______________

For this operation to work the current line must contain the text:
:   'def sv_main(**variables**):'

Where '**variables**' is something like:
:   'verts=[], petal_size=2.3, num_petals=1'

There are three types of input streams that this node can interpret:
- 'v' (vertices, 3-tuple coordinates)
- 's' (data: float, integer),
- 'm' (matrices: nested lists 4*4)

        For more information see the wiki
        see also the bundled templates for clarification
'''


def has_selection(self, text):
    return not (text.select_end_line == text.current_line and
                text.current_character == text.select_end_character)


def converted(test_str):

    r = re.compile('(?P<name>\w+)=(?P<defval>.*?|\[\])[,\)]')
    k = [m.groupdict() for m in r.finditer(test_str)]
    # print(k)

    # convert dict
    socket_mapping = {
        '[]': 'v'
        # assume more will follow
    }

    indent = "    "
    socket_members = []
    for variable in k:
        stype = variable['defval']
        sname = variable['name']
        shorttype = socket_mapping.get(stype, 's')
        list_item = str([shorttype, sname, {0}])
        l = list_item.format(sname)
        socket_members.append(indent*2 + l)
    socket_items = ",\n".join(socket_members)
    declaration = "\n" + indent + 'in_sockets = [\n'
    declaration += socket_items
    declaration += "]"
    return declaration


class SvVarnamesToSockets(bpy.types.Operator):

    bl_label = ""
    bl_idname = "txt.varname_rewriter"

    def execute(self, context):
        bpy.ops.text.select_line()
        bpy.ops.text.copy()
        copied_text = bpy.data.window_managers[0].clipboard
        if "def sv_main(" not in copied_text:
            self.report({'INFO'}, "ERROR - LOOK CONSOLE")
            print(sv_error_message)
            return {'CANCELLED'}
        answer = converted(copied_text)

        if answer:
            print(answer)
            bpy.data.window_managers[0].clipboard = answer
            bpy.ops.text.move(type='LINE_BEGIN')
            bpy.ops.text.move(type='NEXT_LINE')
            bpy.ops.text.paste()
        return {'FINISHED'}


class SvNodeRefreshFromTextEditor(bpy.types.Operator):

    bl_label = ""
    bl_idname = "txt.noderefresh_from_texteditor"

    def execute(self, context):
        ngs = bpy.data.node_groups
        if not ngs:
            self.report({'INFO'}, "No NodeGroups")
            return {'FINISHED'}

        edit_text = bpy.context.edit_text
        text_file_name = edit_text.name
        is_sv_tree = lambda ng: ng.bl_idname == 'SverchCustomTreeType'
        ngs = list(filter(is_sv_tree, ngs))

        if not ngs:
            self.report({'INFO'}, "No Sverchok NodeGroups")
            return {'FINISHED'}

        looking_for_script_node = self.has_sv_main(edit_text)

        for ng in ngs:
            node_types = [node.bl_idname for node in ng.nodes]

            if looking_for_script_node:
                SN = 'SvScriptNode'
                if SN in node_types:
                    nodes = [n for n in ng.nodes if n.bl_idname == SN]
                    for n in nodes:
                        if n.script_name == text_file_name:
                            n.load()
                            ng.update()
                            break

            else:
                PN = 'SvProfileNode'
                if PN in node_types:
                    nodes = [n for n in ng.nodes if n.bl_idname == PN]
                    for n in nodes:
                        if n.filename == text_file_name:
                            ng.update()
                            break

        return {'FINISHED'}

    def has_sv_main(self, txt):
        return 'def sv_main(' in txt.as_string()


class BasicTextMenu(bpy.types.Menu):
    bl_idname = "TEXT_MT_svplug_menu"
    bl_label = "Plugin Menu"

    def draw(self, context):
        layout = self.layout

        text = bpy.context.edit_text
        no_selection = (text.current_character == text.select_end_character)
        if no_selection:
            layout.operator("txt.varname_rewriter", text='generate in_sockets')


def register():
    bpy.utils.register_class(SvVarnamesToSockets)
    bpy.utils.register_class(BasicTextMenu)
    bpy.utils.register_class(SvNodeRefreshFromTextEditor)

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    try:
        shortcut_name = "Text"
        if not (shortcut_name in kc.keymaps):
            km = kc.keymaps.new(name=shortcut_name, space_type="TEXT_EDITOR")

            # Sets the keymap to Ctrl + I for inside the text editor, will only
            # appear if no selection is set.
            new_shortcut = km.keymap_items.new(
                'wm.call_menu', 'I', 'PRESS', ctrl=True)
            new_shortcut.properties.name = 'TEXT_MT_svplug_menu'

            # ctrl Enter for profile node
            new_shortcut2 = km.keymap_items.new(
                'txt.noderefresh_from_texteditor',
                'RET', 'PRESS', ctrl=True)

    except KeyError:
        print("Text key not found in keymap, that's ok")


def unregister():
    bpy.utils.unregister_class(SvVarnamesToSockets)
    bpy.utils.unregister_class(BasicTextMenu)
    bpy.utils.unregister_class(SvNodeRefreshFromTextEditor)
