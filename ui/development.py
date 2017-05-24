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

import bpy
from bpy.props import StringProperty, CollectionProperty, BoolProperty, FloatProperty

# global variables in tools
import sverchok
from sverchok.utils.sv_help import remapper

BRANCH = ""

def get_branch():
    global BRANCH

    # first use git to find branch
    try:
        res = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"],
                              stdout=subprocess.PIPE,
                              cwd=os.path.dirname(sverchok.__file__),
                              timeout=2)

        branch = str(res.stdout.decode("utf-8"))
        BRANCH = branch.rstrip()
    except: # if does not work ignore it
        BRANCH = ""
    if BRANCH:
        return

    # if the above failed we can dig deeper, if this failed we concede victory.
    try:
        head = os.path.join(os.path.dirname(sverchok.__file__), '.git', 'HEAD')
        branch = ""
        with open(head) as headfile:
            branch = headfile.readlines()[0].split("/")[-1]
        BRANCH = branch.rstrip()
    except:
        BRANCH = ""

def displaying_sverchok_nodes(context):
    return context.space_data.tree_type in {'SverchCustomTreeType', 'SverchGroupTreeType'}

def node_show_branch(self, context):
    if not displaying_sverchok_nodes(context):
        return
    if BRANCH:
        layout = self.layout
        layout.label("GIT: {}".format(BRANCH))


class SvCopyIDName(bpy.types.Operator):

    bl_idname = "node.copy_bl_idname"
    bl_label = "copy bl idname to clipboard"
    # bl_options = {'REGISTER', 'UNDO'}

    name = bpy.props.StringProperty(default='')

    def execute(self, context):
        context.window_manager.clipboard = self.name
        return {'FINISHED'}


class SvViewHelpForNode(bpy.types.Operator):

    bl_idname = "node.view_node_help"
    bl_label = "display a browser with compiled html"
    kind = StringProperty(default='online')
    
    def execute(self, context):
        n = context.active_node

        string_dir = remapper.get(n.bl_idname)
        filename = n.__module__.split('.')[-1]
        help_url = string_dir + '/' + filename

        # first let's find if this is a valid doc file, by inspecting locally for the rst file.
        VALID = False
        try:
            tk = os.path.join(os.path.dirname(sverchok.__file__), 'docs', 'nodes', string_dir.replace(' ', '_'), filename + '.rst')
            print(tk)
            VALID = exists(tk) and isfile(tk)
        except:
            pass

        if not VALID:
            self.throw_404(n)
            return {'CANCELLED'}

        # valid doc link!
        help_url = help_url.replace(' ', '_')
        if self.kind == 'online':
            destination = 'http://nikitron.cc.ua/sverch/html/nodes/' + help_url + '.html'
        else:
            basepath = os.path.dirname(sverchok.__file__) + '/docs/nodes/'
            destination = r'file:///' + basepath + help_url + '.rst'

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


def idname_draw(self, context):
    if not displaying_sverchok_nodes(context):
        return
    layout = self.layout
    node = context.active_node
    if not node:
        return
    bl_idname = node.bl_idname
    layout.operator('node.copy_bl_idname', text=bl_idname + ' (copy)').name = bl_idname

    # show these anyway, can fail and let us know..
    row = layout.row(align=True)
    row.label('help')
    row.operator('node.view_node_help', text='online').kind = 'online'
    row.operator('node.view_node_help', text='offline').kind = 'offline'



def register():
    get_branch()
    if BRANCH:
        bpy.types.NODE_HT_header.append(node_show_branch)

    bpy.utils.register_class(SvCopyIDName)
    bpy.utils.register_class(SvViewHelpForNode)
    bpy.types.NODE_PT_active_node_generic.append(idname_draw)


def unregister():
    if BRANCH:
        bpy.types.NODE_HT_header.remove(node_show_branch)
    bpy.types.NODE_PT_active_node_generic.remove(idname_draw)

    bpy.utils.unregister_class(SvCopyIDName)
    bpy.utils.unregister_class(SvViewHelpForNode)
