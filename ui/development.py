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

import os
from os.path import exists, isfile
import subprocess
import webbrowser
import socket

import bpy
from bpy.props import StringProperty, CollectionProperty, BoolProperty, FloatProperty

# global variables in tools
import sverchok
from sverchok.utils.sv_help import remapper
from sverchok.utils.context_managers import sv_preferences
from sverchok.utils import get_node_class_reference
from sverchok.utils.development import get_branch
from sverchok.ui.nodes_replacement import set_inputs_mapping, set_outputs_mapping
from sverchok.ui.presets import get_presets, SverchPresetReplaceOperator, SvSaveSelected, node_supports_presets
from sverchok.nodes.__init__ import nodes_dict
from sverchok.settings import PYPATH

def displaying_sverchok_nodes(context):
    return context.space_data.tree_type in {'SverchCustomTreeType', 'SverchGroupTreeType'}

def node_show_branch(self, context):
    if not displaying_sverchok_nodes(context):
        return
    branch = get_branch()
    if branch:
        layout = self.layout
        layout.label(icon='CON_CHILDOF', text=branch)

class SvCopyIDName(bpy.types.Operator):
    ''' Copy node's ID name to clipboard to use in code '''
    bl_idname = "node.copy_bl_idname"
    bl_label = "copy bl idname to clipboard"
    # bl_options = {'REGISTER', 'UNDO'}

    name: bpy.props.StringProperty(default='')

    def execute(self, context):
        context.window_manager.clipboard = self.name
        return {'FINISHED'}

def is_port_open(host, port):
    try:
        a_socket = socket. socket(socket. AF_INET, socket. SOCK_STREAM)
        location = (host, port)
        #location = ("127.0.0.1", 80)
        result = a_socket. connect_ex(location)
        return (result == 0)
    finally:
        a_socket. close()

class SvRunPydoc(bpy.types.Operator):
    """Open browser with available Python API"""
    bl_idname = "node.sv_run_pydoc"
    bl_label = "Open PyDoc"
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        HOST = "localhost"
        PORT = 8080
        if is_port_open(HOST, PORT):
            webbrowser.open(f"http://{HOST}:{PORT}/")
        else:
            cmd = [PYPATH, '-m', 'pydoc', '-n', HOST, '-p', str(PORT), '-b']
            subprocess.Popen(cmd)
        return {'FINISHED'}

def get_docs_filepath(string_dir, filename):
    filepath = os.path.join(
        os.path.dirname(sverchok.__file__),
        'docs',
        'nodes',
        string_dir.replace(' ', '_'),
        filename + '.rst'
        )
    return filepath

class SvViewHelpForNode(bpy.types.Operator):
    """ Open docs on site, on local PC or on github """
    bl_idname = "node.view_node_help"
    bl_label = "display a browser with compiled html"

    kind: StringProperty(default='online')

    def execute(self, context):
        n = context.active_node

        string_dir = remapper.get(n.bl_idname)
        filename = n.__module__.split('.')[-1]
        if filename in ('mask','mask_convert','mask_join'):
            string_dir = 'list_masks'
        elif filename in ('modifier'):
            string_dir = 'list_mutators'
        elif string_dir == 'analyzers':
            string_dir = 'analyzer'

        help_url = string_dir + '/' + filename
        # first let's find if this is a valid doc file, by inspecting locally for the rst file.
        VALID = False
        try:
            tk = get_docs_filepath(string_dir, filename)
            print(tk)
            VALID = exists(tk) and isfile(tk)
            # if is not valid we check if it is another folder (for nodes in Alpha, Beta, CAD...)
            if not VALID:
                for folder in nodes_dict.keys():
                    tk = get_docs_filepath(folder, filename)
                    VALID = exists(tk) and isfile(tk)
                    if VALID:
                        help_url = folder + '/' + filename
                        break
        except:
            pass

        if not VALID:
            self.throw_404(n)
            return {'CANCELLED'}

        # valid doc link!
        help_url = help_url.replace(' ', '_')
        if self.kind == 'online':
            destination = 'http://nikitron.cc.ua/sverch/html/nodes/' + help_url + '.html'
        elif self.kind == 'offline':
            basepath = os.path.dirname(sverchok.__file__) + '/docs/nodes/'
            destination = r'file:///' + basepath + help_url + '.rst'
        elif self.kind == 'github':
            destination = 'https://github.com/nortikin/sverchok/blob/master/docs/nodes/' + help_url + '.rst'

        webbrowser.open(destination)
        return {'FINISHED'}

    def throw_404(self, n):
        # bl_label of some nodes is edited by us, but those nodes do have docs ..
        _dirname = os.path.dirname(sverchok.__file__)
        path1 = os.path.join(_dirname, 'docs', '404.html')
        path2 = os.path.join(_dirname, 'docs', '404_custom.html')

        with open(path1) as origin:
            with open(path2, 'w') as destination:
                for line in origin:
                    if '{{variable}}' in line:
                        destination.write(line.replace("{{variable}}", n.bl_label))
                    else:
                        destination.write(line)

        webbrowser.open(path2)


class SvViewSourceForNode(bpy.types.Operator):
    ''' Open source code of node in OS text editor or as a Blender textblock'''
    bl_idname = "node.sv_view_node_source"
    bl_label = "display the source in your editor or as a Blender textblock"

    kind: StringProperty(default='external')

    def execute(self, context):
        n = context.active_node
        fpath = self.get_filepath_from_node(n)
        string_dir = remapper.get(n.bl_idname)

        with sv_preferences() as prefs:

            if prefs.real_sverchok_path:
                _dst = os.path.dirname(sverchok.__file__)
                _src = prefs.real_sverchok_path
                fpath = fpath.replace(_dst, _src)

            if self.kind == 'internal':
                self.view_source_internal(context.screen.areas, fpath)

            elif self.kind == 'external':
                self.view_source_external(prefs, fpath)

            return {'FINISHED'}

        return {'CANCELLED'}
        
    def view_source_internal(self, areas, fpath):
        block_name = os.path.basename(fpath)
        repeated = False
        for t in bpy.data.texts:
            if t.name == block_name:
                self.report({'INFO'}, "'" + block_name + "' was already opened")
                repeated = True;
                break
        if not repeated:
            text = bpy.ops.text.open(filepath=fpath)
            self.report({'INFO'}, "'" + block_name + "' opened as new text data-block")

        displayed = False
        for area in areas:
            if area.type == "TEXT_EDITOR":
                area.spaces[0].text = bpy.data.texts[block_name]
                displayed = True
                break
        if not displayed:
            bpy.ops.screen.area_split(direction='VERTICAL', factor=0.5)
            areas[-1].type = 'TEXT_EDITOR'
            areas[-1].spaces[0].text = bpy.data.texts[block_name]
            
        return {'FINISHED'}
    
    def view_source_external(self, prefs, fpath):
        app_name = prefs.external_editor
        if not app_name:
            self.report({'INFO'}, "Set first a external editor on Sverchok Preferences (User Preferences -> Add-ons)")
            return {'CANCELLED'}
        subprocess.Popen([app_name, fpath])
        return {'FINISHED'}
    
    def get_filepath_from_node(self, n):
        """ get full filepath on disk for a given node reference """
        import inspect
        return inspect.getfile(n.__class__)

class SV_MT_LoadPresetMenu(bpy.types.Menu):
    bl_label = "Load Node Preset"

    @classmethod
    def poll(cls, context):
        if not displaying_sverchok_nodes(context):
            return False
        if not hasattr(context, 'active_node'):
            return False
        node = context.active_node
        return node_supports_presets(node)

    def draw(self, context):
        node = context.active_node
        if not node:
            return
        layout = self.layout
        ntree = node.id_data
        has_presets = False
        for preset in get_presets(category = node.bl_idname, mkdir=False):
            has_presets = True
            op = layout.operator(SverchPresetReplaceOperator.bl_idname, text=preset.name)
            op.preset_path = preset.path
            op.preset_name = preset.name
            op.node_name = node.name

        if not has_presets:
            layout.label(text="There are no presets for this node")

        # In the N panel, we are showing Save button separately
        if hasattr(context, 'region') and context.region.type == 'WINDOW':
            layout.separator()
            layout.operator_context = 'INVOKE_DEFAULT' # otherwise Blender will not call invoke()
            save = layout.operator(SvSaveSelected.bl_idname, text="Save current settings as node preset", icon='SOLO_ON')
            save.id_tree = ntree.name
            save.category = node.bl_idname
            save.save_defaults = True

def idname_draw(self, context):
    if not displaying_sverchok_nodes(context):
        return
    layout = self.layout
    node = context.active_node
    ntree = node.id_data
    if not node:
        return
    bl_idname = node.bl_idname
    box = layout.box()
    col = box.column(align=False)
    col.scale_y = 0.9
    row = col.row(align=True)
    colom = row.column(align=True)
    colom.scale_x = 3
    colom.label(text=bl_idname+':')
    colom = row.column(align=True)
    colom.operator('node.copy_bl_idname', text='', icon='COPY_ID').name = bl_idname

    if node_supports_presets(node):
        box = col.box()
        box.label(text="Presets:")
        box.menu("SV_MT_LoadPresetMenu")
        save_row = box.row()
        save = save_row.operator(SvSaveSelected.bl_idname, text="Save Node Preset", icon='SOLO_ON')
        save.id_tree = ntree.name
        save.category = node.bl_idname
        save.save_defaults = True
        selected_nodes = [node for node in ntree.nodes if node.select]
        save_row.enabled = len(selected_nodes) == 1

    # show these anyway, can fail and let us know..
    row = col.row(align=True)
    row.label(text='Help & Docs:')
    row = col.row(align=True)
    row.operator('node.view_node_help', text='Online').kind = 'online'
    row.operator('node.view_node_help', text='Offline').kind = 'offline'
    row.operator('node.view_node_help', text='Github').kind = 'github' #, icon='GHOST'
    col.separator()
    # view the source of the current node ( warning, some nodes rely on more than one file )
    row = col.row(align=True)
    row.label(text='Edit Source:')
    row = col.row(align=True)
    row.operator('node.sv_view_node_source', text='Externally').kind = 'external'
    row.operator('node.sv_view_node_source', text='Internally').kind = 'internal'

    if hasattr(node, 'replacement_nodes'):
        box = col.box()
        box.label(text="Replace with:")
        for new_bl_idname, inputs_mapping, outputs_mapping in node.replacement_nodes:
            node_class = get_node_class_reference(new_bl_idname)
            text = node_class.bl_label
            op = box.operator("node.sv_replace_node", text=text)
            op.old_node_name = node.name
            op.new_bl_idname = new_bl_idname
            set_inputs_mapping(op, inputs_mapping)
            set_outputs_mapping(op, outputs_mapping)

    row = col.row(align=True)
    op = row.operator('node.sv_replace_node', text='Re-Create Node')
    op.old_node_name = node.name
    op.new_bl_idname = bl_idname


def register():
    branch = get_branch()
    if branch:
        bpy.types.NODE_HT_header.append(node_show_branch)

    bpy.utils.register_class(SvCopyIDName)
    bpy.utils.register_class(SvViewHelpForNode)
    bpy.utils.register_class(SvViewSourceForNode)
    bpy.utils.register_class(SV_MT_LoadPresetMenu)
    bpy.utils.register_class(SvRunPydoc)
    bpy.types.NODE_PT_active_node_generic.append(idname_draw)


def unregister():
    branch = get_branch()
    if branch:
        bpy.types.NODE_HT_header.remove(node_show_branch)
    bpy.utils.unregister_class(SV_MT_LoadPresetMenu)
    bpy.types.NODE_PT_active_node_generic.remove(idname_draw)
    bpy.utils.unregister_class(SvRunPydoc)
    bpy.utils.unregister_class(SvCopyIDName)
    bpy.utils.unregister_class(SvViewHelpForNode)
    bpy.utils.unregister_class(SvViewSourceForNode)

