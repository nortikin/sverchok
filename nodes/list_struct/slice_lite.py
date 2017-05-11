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
from bpy.props import BoolProperty, IntProperty, StringProperty, EnumProperty

import itertools
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, changable_sockets, repeat_last, match_long_repeat

# from python 3.5 docs https://docs.python.org/3.5/library/itertools.html recipes
def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


def list_split(sublist, num_slices):
    #for i in range(0, len(sublist), num_slices):
    #    yield l[i:i + num_slices]
    return grouper(sublist, num_slices, fillvalue=sublist[-1])


def list_slices(data, slice_sizes):
    out_data = []
    for slices, sub_list in zip(data, slice_sizes):
        out_data.append(...)



class SvListSliceLiteNode(bpy.types.Node, SverchCustomTreeNode):
    ''' ls slice incoming data /// yep'''
    bl_idname = 'SvListSliceLiteNode'
    bl_label = 'List Slice Lite '
    bl_icon = 'SEQ_LUMA_WAVEFORM'

    num_slices = IntProperty(default=1, min=0, name='Slice Count', update=updateNode)

    def sv_init(self, context):
        new_in = self.inputs.new
        new_out = self.outputs.new
        new_in('StringsSocket', 'Data')
        new_in('StringsSocket', 'Slice Lengths').prop_name = 'num_slices'
        new_out('StringsSocket', 'Sliced Data')

    def draw_buttons(self, context, layout):
        ...

    def change_socket_if_needed(self):
        input_bl_idname = self.inputs[0].other.bl_idname
        if not self.inputs[0].bl_idname == input_bl_idname:
            # keep current name, but change socket type to reflect the incoming data
            self.inputs[0].replace_socket(input_bl_idname)
            self.outputs[0].replace_socket(input_bl_idname)

    @property
    def end_early(self):
        # end early
        if self.inputs[0].is_linked:
            self.change_socket_if_needed()
            if not self.outputs[0].is_linked:
                return True
        else:
            return True        

    def process(self):
        if self.end_early:
            return

        # do the work, but if num_slices == 0, pass data thru unchanged
        data = self.inputs[0].sv_get()
        out_data = data

        if not self.inputs[1].is_linked:
            num_slices = self.num_slices
            if num_slices > 0:
                # divide the incoming sublists, by n times, and additionally output remainder / degenerate
                out_data = [list_split(sublist, num_slices) for sublist in data]
        else:
            out_data = list_slices(data, self.inputs[1].sv_get)

        self.outputs[0].sv_set(out_data)



def register():
    bpy.utils.register_class(SvListSliceLiteNode)


def unregister():
    bpy.utils.unregister_class(SvListSliceLiteNode)