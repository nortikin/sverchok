# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import re
import bpy
from sverchok.utils.logging import debug, info, error


def has_selection(self, text):
    return not (text.select_end_line == text.current_line and
                text.current_character == text.select_end_character)

# maybe fuzzy module?
def fuzzy_compare(named_seeker, named_current):
    """ 
    try to find the stored datablock.name with or without extra chars, 
    if these things fail then there is no compare anyway 
    """
    try:
        if named_seeker == named_current: return True
        elif named_seeker[3:] == named_current: return True
    except Exception as err:
        print(f"Refesh Current Script called but encountered error {err}")


class SvNodeRefreshFromTextEditor(bpy.types.Operator):

    bl_label = "Refesh Current Script"
    bl_idname = "text.noderefresh_from_texteditor"

    def execute(self, context):

        self.report({'INFO'}, "Triggered: text.noderefresh_from_texteditor")

        ngs = bpy.data.node_groups
        if not ngs:
            self.report({'INFO'}, "No NodeGroups")
            return {'FINISHED'}

        edit_text = bpy.context.edit_text
        text_file_name = edit_text.name
        is_sv_tree = lambda ng: ng.bl_idname in {'SverchCustomTreeType', 'SverchGroupTreeType'}
        ngs = list(filter(is_sv_tree, ngs))

        if not ngs:
            self.report({'INFO'}, "No Sverchok NodeGroups")
            return {'FINISHED'}

        node_types = set([
            'SvScriptNodeLite', 'SvTextInNodeMK2', 'SvGenerativeArtNode', 
            'SvSNFunctorB', 'SvVDExperimental', 'SvProfileNodeMK3'])

        for ng in ngs:

            # make sure this tree has nodes that demand updating.
            nodes = [n for n in ng.nodes if n.bl_idname in node_types]
            if not nodes:
                continue

            for n in nodes:

                if n.bl_idname == 'SvSNFunctorB':
                    if n.script_pointer == edit_text:
                        n.handle_reload(context)
                        n.process_node(context)
                        return {'FINISHED'}

                elif n.bl_idname == 'SvScriptNodeLite':
                    if fuzzy_compare(n.script_name, text_file_name):
                        try:
                            n.load()
                            n.process_node(context)
                            return {'FINISHED'}
                        except SyntaxError as err:
                            msg = "SyntaxError : {0}".format(err)
                            self.report({"WARNING"}, msg)
                            return {'CANCELLED'}
                        except Exception as err:
                            self.report({"WARNING"}, f'unspecified error in load()\n{err}^^^^')
                            return {'CANCELLED'}

                elif hasattr(n, "text_file_name") and fuzzy_compare(n.text_file_name, text_file_name):
                    pass  # do nothing for profile node, just update ng, could use break...

                elif hasattr(n, "current_text") and fuzzy_compare(n.current_text, text_file_name):
                    n.reload()

                elif n.bl_idname == 'SvVDExperimental' and n.selected_draw_mode == "fragment":
                    with n.sv_throttle_tree_update():
                        if n.custom_shader_location == text_file_name:
                            n.custom_shader_location = n.custom_shader_location

                elif n.bl_idname == 'SvProfileNodeMK3':
                    print('should trigger!')
                    if n.file_pointer and n.file_pointer.name == text_file_name:
                        print('should trigger!...did it?')
                        n.file_pointer = n.file_pointer

            # update node group with affected nodes
            ng.sv_update()


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
