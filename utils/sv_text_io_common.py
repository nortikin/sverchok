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

# pylint: disable=c0326
# pylint: disable=e1101


import bpy
import json

# status colors
FAIL_COLOR = (0.85, 0.85, 0.8)
READY_COLOR = (0.5, 0.7, 1)

text_modes = [
    ("CSV",         "Csv",          "Csv data",           1),
    ("SV",          "Sverchok",     "Python data",        2),
    ("JSON",        "JSON",         "Sverchok JSON",      3)]

name_dict = {'m': 'Matrix', 's': 'Data', 'v': 'Vertices'}

map_to_short = {'SvVerticesSocket': 'v', 'SvStringsSocket': 's', 'SvMatrixSocket': 'm'}
map_from_short = {'v': 'SvVerticesSocket', 's': 'SvStringsSocket', 'm': 'SvMatrixSocket'}


def get_socket_type(node, inputsocketname):
    socket_type = node.inputs[inputsocketname].links[0].from_socket.bl_idname
    return map_to_short.get(socket_type, 's')

def new_output_socket(node, name, _type):
    bl_idname = map_from_short.get(_type, 'SvStringsSocket')
    node.outputs.new(bl_idname, name)


class SvTextIOMK2Op(bpy.types.Operator):
    """ generic callback for TEXT IO nodes """
    bl_idname = "node.sverchok_textio_mk2_callback"
    bl_label = "text IO operator cb"
    bl_options = {'REGISTER', 'UNDO'}

    fn_name: bpy.props.StringProperty(name='tree name')

    def execute(self, context):
        n = context.node
        fn_name = self.fn_name

        f = getattr(n, fn_name, None)
        if not f:
            msg = "{0} has no function named '{1}'".format(n.name, fn_name)
            self.report({"WARNING"}, msg)
            return {'CANCELLED'}
        f()

        return {'FINISHED'}

TEXT_IO_CALLBACK = SvTextIOMK2Op.bl_idname



def register():
    bpy.utils.register_class(SvTextIOMK2Op)


def unregister():
    bpy.utils.unregister_class(SvTextIOMK2Op)
