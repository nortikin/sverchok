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

from sverchok.utils.logging import debug, info, error

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


class SvNodeRefreshFromTextEditor(bpy.types.Operator):

    bl_label = "Refesh Current Script"
    bl_idname = "text.noderefresh_from_texteditor"

    def execute(self, context):

        ngs = bpy.data.node_groups
        if not ngs:
            self.report({'INFO'}, "No NodeGroups")
            return {'FINISHED'}

        edit_text = bpy.context.edit_text
        text_file_name = edit_text.name
        is_sv_tree = lambda ng: ng.bl_idname in {'SverchCustomTreeType', 'SverchGroupTreeType'}
        ngs = list(filter(is_sv_tree, ngs))

        if not ngs:
            self.report({'INFO'}, "No Sverchok / svrx NodeGroups")
            return {'FINISHED'}

        node_types = set([
            'SvScriptNode', 'SvScriptNodeMK2', 'SvScriptNodeLite',
            'SvProfileNode', 'SvTextInNode', 'SvGenerativeArtNode', 'SvSNFunctorB',
            'SvRxNodeScript', 'SvProfileNodeMK2', 'SvVDExperimental', 'SvProfileNodeMK3'])

        for ng in ngs:

            # make sure this tree has nodes that demand updating.
            nodes = [n for n in ng.nodes if n.bl_idname in node_types]
            if not nodes:
                continue

            for n in nodes:

                if hasattr(n, "script_name") and n.script_name == text_file_name:
                    try:
                        n.load()
                    except SyntaxError as err:
                        msg = "SyntaxError : {0}".format(err)
                        self.report({"WARNING"}, msg)
                        return {'CANCELLED'}
                    except:
                        self.report({"WARNING"}, 'unspecified error in load()')
                        return {'CANCELLED'}

                elif hasattr(n, "text_file_name") and n.text_file_name == text_file_name:
                    pass  # no nothing for profile node, just update ng, could use break...

                elif hasattr(n, "current_text") and n.current_text == text_file_name:
                    n.reload()

                elif n.bl_idname == 'SvVDExperimental' and n.selected_draw_mode == "fragment":
                    with n.sv_throttle_tree_update():
                        if n.custom_shader_location == text_file_name:
                            n.custom_shader_location = n.custom_shader_location

                elif n.bl_idname == 'SvSNFunctorB':
                    if n.script_name.strip() == text_file_name.strip():
                        with n.sv_throttle_tree_update():
                            print('handle the shortcut')
                            n.handle_reload(context)

            # update node group with affected nodes
            ng.update()


        return {'FINISHED'}



# store keymaps here to access after registration
addon_keymaps = []


def add_keymap():

    # handle the keymap
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon

    if not kc:
        debug('no keyconfig path found. that\'s ok')
        return

    km = kc.keymaps.new(name='Text', space_type='TEXT_EDITOR')
    keymaps = km.keymap_items

    if 'noderefresh_from_texteditor' in dir(bpy.ops.text):
        ''' SHORTCUT 1 Node Refresh: Ctrl + Return '''
        ident_str = 'text.noderefresh_from_texteditor'
        if not (ident_str in keymaps):
            new_shortcut = keymaps.new(ident_str, 'RET', 'PRESS', ctrl=1, head=0)
            addon_keymaps.append((km, new_shortcut))

        debug('Sverchok added keyboard items to Text Editor.')


def remove_keymap():

    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()


def register():
    bpy.utils.register_class(SvNodeRefreshFromTextEditor)
    add_keymap()


def unregister():
    remove_keymap()
    bpy.utils.unregister_class(SvNodeRefreshFromTextEditor)
