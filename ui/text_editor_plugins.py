# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from sverchok.utils.sv_logging import get_logger
from sverchok.settings import get_params


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
        print(f"Refresh Current Script called but encountered error {err}")

def get_first_sverchok_nodetree():

    AREA = 'NODE_EDITOR'
    for window in bpy.context.window_manager.windows:
        screen = window.screen
        for area in screen.areas:
            if not area.type == AREA: continue

            for space in area.spaces:
                if hasattr(space, "edit_tree"):
                    if space.tree_type in {'SverchCustomTreeType', 'SvGroupTree'}:
                        ng = space.edit_tree
                        for region in area.regions:
                            if region.type == 'WINDOW': 
                                override = {
                                    'window': window,
                                    'screen': screen,
                                    'area': area,
                                    'region': region
                                }
                                return ng, override, space



class SvSNLiteAddFromTextEditor(bpy.types.Operator):
    """
    you want to create an snlite from the current edit_text in TextEditor
    this will create the node, load it with the text, and center the nodeview on that node.
    """
    bl_label = "Make SNlite from Current Script"
    bl_idname = "text.nodenew_from_texteditor"

    def execute(self, context):
        self.report({'INFO'}, f"Triggered: {self.bl_idname}")

        ngs = bpy.data.node_groups
        if not ngs:
            self.report({'INFO'}, "No NodeGroups")
            return {'FINISHED'}

        edit_text = bpy.context.edit_text
        text_file_name = edit_text.name
        is_sv_tree = lambda ng: ng.bl_idname in {'SverchCustomTreeType', }
        ngs = list(filter(is_sv_tree, ngs))

        if not ngs:
            self.report({'INFO'}, "No Sverchok NodeGroups")
            return {'CANCELLED'}

        if (result := get_first_sverchok_nodetree()):
            ng, override, space = result

            for n in ng.nodes:
                if n.bl_idname == "SvScriptNodeLite":
                    if fuzzy_compare(n.script_name, text_file_name):
                        n.load()
                        return {'CANCELLED'}

            snlite = ng.nodes.new('SvScriptNodeLite')
            
            # middle of view, translated to nodetree location
            dpi_fac = get_params({'render_location_xy_multiplier': 1.0}, direct=True)[0]
            region = override['region']
            mid_x = region.width / 2
            mid_y = region.height / 2
            print("mid==", mid_x, mid_y)
            x, y  = region.view2d.region_to_view(mid_x, mid_y)
            snlite.location = x * 1 / dpi_fac, y *1 / dpi_fac

            snlite.script_name = text_file_name
            snlite.load()

            #ng.nodes.active = snlite
            #snlite.select = True
            #bpy.ops.node.view_selected(override)

        return {'FINISHED'}


class SvNodeRefreshFromTextEditor(bpy.types.Operator):

    bl_label = "Refresh Current Script"
    bl_idname = "text.noderefresh_from_texteditor"

    def execute(self, context):

        self.report({'INFO'}, f"Triggered: {self.bl_idname}")

        ngs = bpy.data.node_groups
        if not ngs:
            self.report({'INFO'}, "No NodeGroups")
            return {'FINISHED'}

        edit_text = bpy.context.edit_text
        text_file_name = edit_text.name
        is_sv_tree = lambda ng: ng.bl_idname in {'SverchCustomTreeType', }
        ngs = list(filter(is_sv_tree, ngs))

        if not ngs:
            self.report({'INFO'}, "No Sverchok NodeGroups")
            return {'FINISHED'}

        node_types = set([
            'SvScriptNodeLite', 'SvTextInNodeMK2', 'SvGenerativeArtNode',
            'SvSNFunctorB', 'SvViewerDrawMk4', 'SvProfileNodeMK3'])

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
                            # n.process_node(context)
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

                elif n.bl_idname == 'SvViewerDrawMk4' and n.selected_draw_mode == "fragment":
                    if n.custom_shader_location == text_file_name:
                        n.custom_shader_location = n.custom_shader_location

                elif n.bl_idname == 'SvProfileNodeMK3':
                    print('should trigger!')
                    if n.file_pointer and n.file_pointer.name == text_file_name:
                        print('should trigger!...did it?')
                        n.file_pointer = n.file_pointer

        return {'FINISHED'}

# store keymaps here to access after registration
addon_keymaps = []


def add_keymap():

    # handle the keymap
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon

    if not kc:
        logger.debug('no keyconfig path found. that\'s ok')
        return

    km = kc.keymaps.new(name='Text', space_type='TEXT_EDITOR')
    keymaps = km.keymap_items

    if 'noderefresh_from_texteditor' in dir(bpy.ops.text):
        ''' SHORTCUT 1 Node Refresh: Ctrl + Return '''
        ident_str = SvNodeRefreshFromTextEditor.bl_idname
        if not (ident_str in keymaps):
            new_shortcut = keymaps.new(ident_str, 'RET', 'PRESS', ctrl=1, head=0)
            addon_keymaps.append((km, new_shortcut))

        ident_str = SvSNLiteAddFromTextEditor.bl_idname 
        if not (ident_str in keymaps):
            new_shortcut = keymaps.new(ident_str, 'RET', 'PRESS', ctrl=1, shift=1, head=0)
            addon_keymaps.append((km, new_shortcut))

        logger.debug('Sverchok added keyboard items to Text Editor.')


def remove_keymap():

    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()


def register():
    global logger
    bpy.utils.register_class(SvSNLiteAddFromTextEditor)
    bpy.utils.register_class(SvNodeRefreshFromTextEditor)
    logger = get_logger()
    add_keymap()

def unregister():
    remove_keymap()
    bpy.utils.unregister_class(SvNodeRefreshFromTextEditor)
    bpy.utils.unregister_class(SvSNLiteAddFromTextEditor)
