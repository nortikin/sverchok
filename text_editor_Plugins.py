import bpy
import os
from bpy.props import EnumProperty, StringProperty
import re

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
        if not "def sv_main(" in copied_text:
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


class BasicTextMenu(bpy.types.Menu):
    bl_idname = "TEXT_MT_svplug_menu"
    bl_label = "Plugin Menu"

    def draw(self, context):
        layout = self.layout

        text = bpy.context.edit_text
        no_selection = (text.current_character == text.select_end_character)
        if no_selection:
            layout.operator("txt.varname_rewriter", text='generate in_sockets')

# Sets the keymap to Ctrl + I for inside the text editor, will only
# appear if a selection is set.
if True:
    wm = bpy.context.window_manager
    try:
        km = wm.keyconfigs.default.keymaps['Text']
        new_shortcut = km.keymap_items.new('wm.call_menu', 'I', 'PRESS', ctrl=True)
        new_shortcut.properties.name = 'TEXT_MT_svplug_menu'
    except KeyError:
        print("Text key not found in keymap, that's ok")


def register():
    bpy.utils.register_class(SvVarnamesToSockets)
    bpy.utils.register_class(BasicTextMenu)


def unregister():
    bpy.utils.unregister_class(SvVarnamesToSockets)
    bpy.utils.unregister_class(BasicTextMenu)


if __name__ == "__main__":
    register()
