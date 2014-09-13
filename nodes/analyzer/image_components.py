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
from bpy.props import (
    IntProperty, FloatProperty, StringProperty, BoolProperty)

from node_tree import SverchCustomTreeNode
from data_structure import (
    updateNode, fullList, SvSetSocketAnyType, SvGetSocketAnyType)

'''
by dealga mcardle sept 2014

Premise of the node

- make pixel copy of selected image using [:]
- outputs r g b as:
    - rvert (x y r)
    - gvert (x y g)
    - bvert (x y b)

'''


def idx_to_co(idx, width):
    """ helps translate index of pixel into 2d coordinate """
    r = int(idx / width)
    c = idx % width
    return r, c


def co_to_idx(r, c, width):
    return r*width+c


def rgba_from_index(idx, dm):
    """
    idx:    a pixel, idx*4 is its index in the flat dm list
    dm:     a flat sequence of ungrouped floats, every 4 floats is one rgba
    """
    start_raw_index = idx * 4
    return dm[start_raw_index:start_raw_index+4]


class ImageComponentsOps(bpy.types.Operator):

    bl_idname = "node.image_comp_callback"
    bl_label = "Sverchok imagecomp callback"
    bl_options = {'REGISTER', 'UNDO'}

    fn_name = StringProperty(default='')

    def load_image(self, context):
        n = context.node
        node_dict = n.node_dict[hash(n)]['node_image'] = {}

        img = bpy.data.images[n.image_name]
        w = img_width = img.size[0]
        h = img_height = img.size[1]

        # work on copy only
        pxls = img.pixels[:]
        num_pixels = int(len(pxls) / 4)

        node_dict['image'] = {
            'x': [], 'y': [], 'r': [], 'g': [], 'b': [], 'a': []
        }

        add_x = node_dict['image']['x'].append
        add_y = node_dict['image']['y'].append
        add_r = node_dict['image']['r'].append
        add_g = node_dict['image']['g'].append
        add_b = node_dict['image']['b'].append
        add_a = node_dict['image']['a'].append
        xy_spread = n.xy_spread
        z_spread = n.z_spread

        for idx in range(num_pixels):
            x, y = idx_to_co(idx, w)
            r, g, b, a = rgba_from_index(idx, pxls)
            add_x(x*xy_spread)
            add_y(y*xy_spread)
            add_r(r*z_spread)
            add_g(g*z_spread)
            add_b(b*z_spread)
            add_a(a*z_spread)

        n.loaded = True

    def unload_image(self, context):
        n = context.node
        n.node_dict[hash(n)]['node_image']['image'] = {}
        n.loaded = False

    def execute(self, context):
        n = context.node
        fn_name = self.fn_name

        if not n.image_name:
            msg = 'no image picked, or imported'
            self.report({"WARNING"}, msg)
            return {'FINISHED'}

        if fn_name == 'load':
            self.load_image(context)
        elif fn_name == 'unload':
            self.unload_image(context)

        return {'FINISHED'}


class SvImageComponentsNode(bpy.types.Node, SverchCustomTreeNode):

    ''' Image Components'''
    bl_idname = 'SvImageComponentsNode'
    bl_label = 'Image Components'
    bl_icon = 'OUTLINER_OB_EMPTY'

    # node storage, reference by the hash of self.
    node_dict = {}

    image_name = StringProperty(
        default="",
        name='image_name',
        description='name of image to CC',
        update=updateNode)

    loaded = BoolProperty(
        default=0,
        name='loaded',
        description='confirms the state of image loading',
        update=updateNode)

    xy_spread = FloatProperty(
        default=0.01,
        step=0.001,
        name='xy_spread',
        update=updateNode)

    z_spread = FloatProperty(
        default=0.01,
        step=0.001,
        name='z_spread',
        update=updateNode)

    def init(self, context):
        self.node_dict[hash(self)] = {}
        self.node_dict[hash(self)]['node_image'] = {}

        xy, z = 'xy_spread', 'z_spread'
        new_in = self.inputs.new
        new_in('StringsSocket', xy, xy).prop_name = xy
        new_in('StringsSocket', z, z).prop_name = z

        new_out = self.outputs.new
        for i in 'xyrgba':
            new_out('StringsSocket', i, i)

    def draw_buttons(self, context, layout):
        col = layout.column()

        if not self.loaded:
            col.prop_search(
                self, 'image_name', bpy.data, 'images',
                text='', icon='FILE_IMAGE')
            operator_type = 'load'
            operator_icon = 'IMPORT'
        else:
            col.label('loaded: ' + self.image_name)
            operator_type = 'unload'
            operator_icon = 'FILE'

        col.operator(
            'node.image_comp_callback',
            text=operator_type,
            icon=operator_icon).fn_name = operator_type

    def update(self):
        outputs = self.outputs

        if not self.loaded:
            return
        if not len(outputs) == 6:
            return
        if not (outputs['x'].links and outputs['y'].links):
            return

        self.process()

    def process(self):
        outputs = self.outputs

        dict_data = self.node_dict[hash(self)]['node_image']['image']
        for name in 'xyrgba':
            if outputs[name].links:
                SvSetSocketAnyType(self, name, [dict_data[name]])

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(ImageComponentsOps)
    bpy.utils.register_class(SvImageComponentsNode)


def unregister():
    bpy.utils.unregister_class(ImageComponentsOps)
    bpy.utils.unregister_class(SvImageComponentsNode)
