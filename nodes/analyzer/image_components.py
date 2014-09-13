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

    def load_image(self, n):
        node_dict = n.node_dict[hash(n)]['node_image'] = {}

        img = bpy.data.images[n.image_name]
        w = img_width = img.size[0]
        h = img_height = img.size[1]

        # work on copy only
        pxls = img.pixels[:]
        num_pixels = len(pxls)

        node_dict['image'] = {}
        for idx in range(num_pixels):
            r, c = idx_to_co(idx, w)
            color = rgba_from_index(idx, pxls)
            node_dict['image'][(r, c)] = color

    def unload_image(self, n):
        n.node_dict[hash(n)]['node_image']['image'] = {}

    def execute(self, context):
        n = context.node
        fn_name = self.fn_name

        if not n.image_name:
            msg = 'no image picked, or imported'
            self.report({"WARNING"}, msg)
            return {'FINISHED'}

        if fn_name == 'load':
            self.load_image(n)
        elif fn_name == 'unload':
            self.unload_image(n)

        return {'FINISHED'}


class SvImageComponentsNode(bpy.types.Node, SverchCustomTreeNode):

    ''' Image Components'''
    bl_idname = 'SvImageComponentsNode'
    bl_label = 'Image Components'
    bl_icon = 'OUTLINER_OB_EMPTY'

    image_name = StringProperty(
        name='image_name',
        description='name of image to CC',
        default="",
        update=updateNode)

    loaded = BoolProperty(
        name='loaded',
        description='confirms the state of image loading',
        default=0,
        update=updateNode)

    node_dict = {}

    def init(self, context):
        self.node_dict[hash(self)] = {}
        self.node_dict[hash(self)]['node_image'] = {}
        self.outputs.new('VerticesSocket', "vecs", "vecs")

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
        pass

    def process(self):
        pass

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(ImageComponentsOps)
    bpy.utils.register_class(SvImageComponentsNode)


def unregister():
    bpy.utils.unregister_class(ImageComponentsOps)
    bpy.utils.unregister_class(SvImageComponentsNode)
