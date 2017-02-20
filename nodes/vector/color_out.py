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

import colorsys
import bpy
from bpy.props import FloatProperty, BoolProperty, FloatVectorProperty
from mathutils import Color

from sverchok.node_tree import SverchCustomTreeNode, StringsSocket
from sverchok.data_structure import updateNode, fullList, dataCorrect
from sverchok.utils.sv_itertools import sv_zip_longest

nodule_color = (0.899, 0.8052, 0.0, 1.0)

# pylint: disable=w0141

def fprop_generator(**altprops):
    # min can be overwritten by passing in min=some_value into the altprops dict
    default_dict_vals = dict(update=updateNode, precision=3, min=0.0, max=1.0)
    default_dict_vals.update(**altprops)
    return FloatProperty(**default_dict_vals)


class SvColorsOutNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Generator for Color data , color separate'''
    bl_idname = 'SvColorsOutNode'
    bl_label = 'Color Out'
    bl_icon = 'OUTLINER_OB_EMPTY'

    def psuedo_update(self, context):
        for idx, socket in enumerate(self.selected_mode):
            self.outputs[idx].name = socket
        updateNode(self, context)
  
    unit_color = FloatVectorProperty(
        update=updateNode, name='', default=(.3, .3, .2, 1.0),
        size=4, min=0.0, max=1.0, subtype='COLOR'
    )

    use_alpha = BoolProperty(default=False, update=updateNode)

    def sv_init(self, context):
        self.width = 100
        inew = self.inputs.new
        color_socket = inew('StringsSocket', "Colors")
        color_socket.prop_name = 'unit_color'
        color_socket.nodule_color = nodule_color
        onew = self.outputs.new
        onew('StringsSocket', "R")
        onew('StringsSocket', "G")
        onew('StringsSocket', "B")
        onew('StringsSocket', "A")


    def draw_buttons(self, context, layout):
        layout.prop(self, 'use_alpha')

    
    def process(self):
        """
        colorsys.rgb_to_hls(r, g, b)
        colorsys.hls_to_rgb(h, l, s)
        colorsys.rgb_to_hsv(r, g, b)
        colorsys.hsv_to_rgb(h, s, v)


                      |--------  r
        rgb(a)--------|--------  g
                      |--------  b
                      |-------- (a)
        """        

        color_input = self.inputs['Colors']
        if color_input.is_linked:
            abc = self.inputs['Colors'].sv_get()
            data = dataCorrect(abc)
        else:
            data = [[self.unit_color[:]]]


        values = [[], [], [], []]
        for obj in data:
            vals = (list(x) for x in zip(*obj))
            for idx, v in enumerate(vals):
                values[idx].append(v)
        for i, socket in enumerate(self.outputs):

            if i == 3 and len(values[3]) == 0 or (not self.use_alpha):
                socket.sv_set([[]])
                break
            else:
                socket.sv_set(values[i])

    
    
def register():
    bpy.utils.register_class(SvColorsOutNode)


def unregister():
    bpy.utils.unregister_class(SvColorsOutNode)
