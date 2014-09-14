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

from math import floor

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
- outputs
    - x, y, r, g, b, a
    - polygons

this would allow one to combine x any y with r to show
a strength table of r over x,y

'''


def idx_to_co(idx, width):
    """ helps translate index of pixel into 2d coordinate """
    r = int(idx / width)
    c = idx % width
    return c, r


def co_to_idx(r, c, width):
    return r * width + c


def rgba_from_index(idx, dm):
    """
    idx:    a pixel, idx*4 is its index in the flat dm list
    dm:     a flat sequence of ungrouped floats, every 4 floats is one rgba
    """
    start_raw_index = idx * 4
    return dm[start_raw_index:start_raw_index + 4]


def generate_polygons(num_x, num_y):
    """
    taken from https://github.com/zeffii/BlenderSciViz/
    """
    faces = []

    for i in range((num_x - 1) * (num_y - 1)):
        x = (i % (num_x - 1))
        y = floor(i / (num_x - 1))
        verts_per_side_x = num_x

        level = x + (y * verts_per_side_x)
        idx1 = level
        idx2 = level + 1
        idx3 = level + verts_per_side_x + 1
        idx4 = level + verts_per_side_x

        faces.append([idx1, idx2, idx3, idx4])

    return faces


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
            'x': [], 'y': [],
            'r': [], 'g': [], 'b': [], 'a': [],
            'polygons': [], 'dimensions': [w, h]
        }

        add_x = node_dict['image']['x'].append
        add_y = node_dict['image']['y'].append
        add_r = node_dict['image']['r'].append
        add_g = node_dict['image']['g'].append
        add_b = node_dict['image']['b'].append
        add_a = node_dict['image']['a'].append

        # generator expression
        gen_obj = (i for i in pxls)

        if n.skip == 0:
            for idx in range(num_pixels):
                x, y = idx_to_co(idx, w)
                add_x(x)
                add_y(y)
                add_r(next(gen_obj))
                add_g(next(gen_obj))
                add_b(next(gen_obj))
                add_a(next(gen_obj))
        else:

            xlookup = [ix for ix in range(w) if ix % (n.skip+1) == 0]
            ylookup = [iy for iy in range(h) if iy % (n.skip+1) == 0]

            for idx in range(num_pixels):
                x, y = idx_to_co(idx, w)
                if not ((x in xlookup) and (y in ylookup)):
                    [next(gen_obj) for i in range(4)]
                    continue

                add_x(x)
                add_y(y)
                add_r(next(gen_obj))
                add_g(next(gen_obj))
                add_b(next(gen_obj))
                add_a(next(gen_obj))

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

    skip = IntProperty(
        default=3,
        step=1, min=0,
        update=updateNode)

    def init(self, context):
        self.node_dict[hash(self)] = {}
        self.node_dict[hash(self)]['node_image'] = {}

        xy, z, p = 'xy_spread', 'z_spread', 'polygons'
        socket = 'StringsSocket'

        new_in = self.inputs.new
        new_in(socket, xy, xy).prop_name = xy
        new_in(socket, z, z).prop_name = z

        new_out = self.outputs.new
        for i in 'xyrgba':
            new_out(socket, i, i)
        new_out(socket, p, p)

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

        col.prop(self, 'skip', text='Skip n pixels')

        if self.loaded:
            image_dict = self.node_dict[hash(self)].get('node_image')
            if image_dict:
                w, h = image_dict['image']['dimensions']
                col.label('dims h={h}, w={w}'.format(w=w, h=h))

    def update(self):
        outputs = self.outputs

        if not self.loaded:
            return
        if not len(outputs) == 7:
            return
        if not (outputs['x'].links and outputs['y'].links):
            return

        if not hash(self) in self.node_dict:
            self.node_dict[hash(self)] = {}
            self.loaded = 0

        self.process()

    def process(self):
        outputs = self.outputs

        node_image = self.node_dict[hash(self)]['node_image']
        dict_data = node_image['image']
        for name in 'xyrgba':
            if outputs[name].links:
                m = self.xy_spread if name in 'xy' else self.z_spread
                data = [v * m for v in dict_data[name]]
                SvSetSocketAnyType(self, name, [data])

        polygons = 'polygons'
        if not outputs[polygons].links:
            return

        polygon_data = dict_data[polygons]
        if not polygon_data:

            w, h = dict_data['dimensions']
            if not self.skip == 0:
                w = len(range(0, w, self.skip+1))
                h = len(range(0, h, self.skip+1))

            dict_data[polygons] = generate_polygons(w, h)

        SvSetSocketAnyType(self, polygons, [polygon_data])

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(ImageComponentsOps)
    bpy.utils.register_class(SvImageComponentsNode)


def unregister():
    bpy.utils.unregister_class(ImageComponentsOps)
    bpy.utils.unregister_class(SvImageComponentsNode)
