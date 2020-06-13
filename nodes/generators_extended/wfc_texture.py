# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import numpy as np

import bpy

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.utils.wfc_algorithm import WaveFunctionCollapse


def load_image(image_name) -> np.ndarray:
    image = bpy.data.images[image_name]
    width, height = image.size
    pixels = np.array(image.pixels).reshape((height, width, 4))
    return pixels


class SvWFCTextureNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: image

    the node uses wave function collapse algorithm
    some patterns can take long time to calculate
    """
    bl_idname = 'SvWFCTextureNode'
    bl_label = 'WFC Texture'
    bl_icon = 'FORCE_FORCE'

    image_name: bpy.props.StringProperty(name="Image", default="", update=updateNode, description="Sample image")
    height: bpy.props.IntProperty(default=10, min=1, max=100, update=updateNode, description="For output image")
    width: bpy.props.IntProperty(default=10, min=1, max=100, update=updateNode, description="For output image")
    seed: bpy.props.IntProperty(update=updateNode)
    pattern_size: bpy.props.IntProperty(default=3, min=1, max=5, update=updateNode, description="Usually 2 or 3")
    rotate_patterns: bpy.props.BoolProperty(update=updateNode, description="More complex result")
    tiling_output: bpy.props.BoolProperty(update=updateNode,
                                          description="Output would be able to cycle over UV directions")
    periodic_input: bpy.props.BoolProperty(default=True, update=updateNode, description="Impact on creating patterns")
    tries_number: bpy.props.IntProperty(default=1, min=1, max=10, update=updateNode,
                                        description="If contradiction it will try calculate again")

    def sv_init(self, context):
        self.inputs.new("SvStringsSocket", "height").prop_name = 'height'
        self.inputs.new("SvStringsSocket", "width").prop_name = 'width'
        self.inputs.new("SvStringsSocket", "seed").prop_name = 'seed'
        self.inputs.new("SvStringsSocket", "pattern size").prop_name = 'pattern_size'
        self.outputs.new("SvColorSocket", "image")

    def draw_buttons(self, context, layout):
        col = layout.column(align=True)
        col.label(text="Sample image:")
        col.prop_search(self, 'image_name', bpy.data, 'images', text='', icon='IMAGE')
        col = layout.column(align=True)
        col.prop(self, 'rotate_patterns')
        col.prop(self, 'periodic_input')
        col.prop(self, 'tiling_output')

    def draw_buttons_ext(self, context, layout: 'UILayout'):
        layout.prop(self, 'tries_number')

    def process(self):
        if not self.image_name:
            return

        image = load_image(self.image_name)
        wave = WaveFunctionCollapse(
            image,
            patter_size=self.inputs['pattern size'].sv_get()[0][0],
            periodic_input=self.periodic_input,
            rotate_patterns=self.rotate_patterns)

        output = wave.solve(
            output_size=(self.inputs['width'].sv_get()[0][0], self.inputs['height'].sv_get()[0][0]),
            seed=self.inputs['seed'].sv_get()[0][0],
            tiling_output=self.tiling_output,
            max_number_contradiction_tries=self.tries_number)

        self.outputs['image'].sv_set(output)


def register():
    bpy.utils.register_class(SvWFCTextureNode)


def unregister():
    bpy.utils.unregister_class(SvWFCTextureNode)
