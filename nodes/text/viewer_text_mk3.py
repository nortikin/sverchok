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
from bpy.props import StringProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import levelsOflist, throttle_tree_update, multi_socket, updateNode

socket_types = {
    "SvVerticesSocket": "VERTICES",
    "SvStringsSocket": "EDGES/POLYGONS/OTHERS",
    "SvMatrixSocket": "MATRICES",
    "SvObjectSocket": "OBJECTS"
}

footer = """

**************************************************
                     The End                      """

def makeframe(nTree):
    '''
    Making frame to show text to user. appears in left corner
    Todo - make more organized layout with button making
    lines in up and between Frame and nodes and text of user and layout name
    '''
    # labls = [n.label for n in nTree.nodes]
    if any('Sverchok_viewer' == n.label for n in nTree.nodes):
        return
    else:
        a = nTree.nodes.new('NodeFrame')
        a.width = 800
        a.height = 1500
        locx = [n.location[0] for n in nTree.nodes]
        locy = [n.location[1] for n in nTree.nodes]
        mx, my = min(locx), max(locy)
        a.location[0] = mx - a.width - 10
        a.location[1] = my
        a.text = bpy.data.texts['Sverchok_viewer']
        a.label = 'Sverchok_viewer'
        a.shrink = False
        a.use_custom_color = True
        # this trick allows us to negative color, so user accept it as grey!!!
        color = [1 - i for i in bpy.context.preferences.themes['Default'].node_editor.space.back[:]]
        a.color[:] = color

def readFORviewer_sockets_data(data, dept, le, num_lines):
    cache = ''
    output = ''
    deptl = dept - 1
    if le:
        cache += ('(' + str(le) + ') object(s)')
        del(le)
    if deptl > 1:
        for i, object in enumerate(data):
            cache += ('\n' + '=' + str(i) + '=   (' + str(len(object)) + ')')
            cache += str(readFORviewer_sockets_data(object, deptl, False, num_lines))
    else:
        for k, val in enumerate(data):
            output += ('\n' + str(val))
            if k >= num_lines-1: break
    return cache + output

def readFORviewer_sockets_data_small(data, dept, le):
    cache = ''
    output = ''
    deptl = dept - 1
    if le:
        cache += ('(' + str(le) + ') object(s)')
        del(le)
    if deptl > 0:
        for i, object in enumerate(data):
            cache += ('\n' + '=' + str(i) + '=   (' + str(len(object)) + ')')
            cache += str(readFORviewer_sockets_data_small(object, deptl, False))
    else:
        for k, val in enumerate(data):
            output += ('\n' + str(val))
    return cache + output

def do_text(node, out_string):

    if not 'Sverchok_viewer' in bpy.data.texts:
        bpy.data.texts.new('Sverchok_viewer')

    string_to_write = 'node name: ' + node.name + out_string + footer
    datablock = bpy.data.texts['Sverchok_viewer']
    datablock.clear()
    datablock.from_string(string_to_write)
    
    if node.frame:
        # adding a frame if it doesn't exist, will create a depsgraph update
        with throttle_tree_update(node):
            makeframe(node.id_data)

def prep_text(node, num_lines):
    """ main preparation function for text """
    
    outs  = ''
    inputs = node.inputs
    for socket in inputs:
        if socket.is_linked and socket.other:
            label = socket.other.node.label
            if label:
                label = '; node ' + label.upper()
            
            name = socket.name.upper()
            data_type = socket_types.get(socket.other.bl_idname, "DATA")    
            itype = f'\n\nSocket {name}{label}; type {data_type}: \n'

            eva = socket.sv_get()
            deptl = levelsOflist(eva)
            if deptl and deptl > 2:
                a = readFORviewer_sockets_data(eva, deptl, len(eva), num_lines)
            elif deptl:
                a = readFORviewer_sockets_data_small(eva, deptl, len(eva))
            else:
                a = 'None'
            outs += itype+str(a)+'\n'
    
    do_text(node, outs)



class SverchokViewerMK1(bpy.types.Operator):
    """Sverchok viewerMK1"""
    bl_idname = "node.sverchok_viewer_buttonmk1"
    bl_label = "Sverchok viewer.mk1"
    bl_icon = 'TEXT'
    # bl_options = {'INTERNAL', 'UNDO'}

    nodename: StringProperty(name='nodename')
    treename: StringProperty(name='treename')
    lines: IntProperty(name='lines', description='lines count for operate on',default=1000)

    def execute(self, context):
        node = bpy.data.node_groups[self.treename].nodes[self.nodename]
        num_lines = self.lines
        
        prep_text(node, num_lines)
        return {'FINISHED'}


class ViewerNodeTextMK3(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Viewer Node text MK3
    Tooltip: Inspecting data from sockets in terms
    of levels and structure by types
    multisocket lets you insert many outputs
    """
    bl_idname = 'ViewerNodeTextMK3'
    bl_label = 'Viewer text mk3'
    bl_icon = 'FILE_TEXT'

    autoupdate: BoolProperty(name='update', default=False)
    frame: BoolProperty(name='frame', default=True)
    lines: IntProperty(name='lines', description='lines count to show', default=1000, min=1, max=2000)

    # multi sockets veriables
    newsock: BoolProperty(name='newsock', default=False)
    base_name = 'data'
    multi_socket_type = 'SvStringsSocket'

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', 'data0')

    def draw_buttons_ext(self, context, layout):
        row = layout.row()
        row.prop(self,'lines',text='lines')

    def draw_buttons(self, context, layout):
        row = layout.row()
        row.scale_y = 4.0
        do_text = row.operator('node.sverchok_viewer_buttonmk1', text='V I E W')
        do_text.nodename = self.name
        do_text.treename = self.id_data.name
        do_text.lines = self.lines

        col = layout.column(align=True)
        col.prop(self, "autoupdate", text="autoupdate")
        col.prop(self, "frame", text="frame")


    def sv_update(self):
        # this function auto extends the number of input sockets once a socket is linked.
        multi_socket(self, min=1)

        # we want socket types to match the input
        for socket in self.inputs:
            if socket.is_linked and socket.links:
                if socket.other: 
                    if not socket.bl_idname == socket.other.bl_idname:
                        socket.replace_socket(socket.other.bl_idname)

    def process(self):
        if not self.autoupdate:
            pass
        else:
            prep_text(self, self.lines)


def register():
    bpy.utils.register_class(SverchokViewerMK1)
    bpy.utils.register_class(ViewerNodeTextMK3)


def unregister():
    bpy.utils.unregister_class(ViewerNodeTextMK3)
    bpy.utils.unregister_class(SverchokViewerMK1)
