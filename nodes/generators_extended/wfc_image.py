# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import random
import math
from enum import Enum

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

    ...
    ...
    """
    bl_idname = 'SvWFCTextureNode'
    bl_label = 'WFC Texture'
    bl_icon = 'AUTOMERGE_ON'

    image_name: bpy.props.StringProperty(name="Image", default="", update=updateNode)
    height: bpy.props.IntProperty(default=10, update=updateNode)
    width: bpy.props.IntProperty(default=10, update=updateNode)
    seed: bpy.props.IntProperty(update=updateNode)
    pattern_size: bpy.props.IntProperty(default=3, min=1, max=5, update=updateNode)
    rotate_patterns: bpy.props.BoolProperty(update=updateNode)
    tiling_output: bpy.props.BoolProperty(update=updateNode)
    periodic_input: bpy.props.BoolProperty(default=True, update=updateNode)

    def sv_init(self, context):
        self.inputs.new("SvStringsSocket", "height").prop_name = 'height'
        self.inputs.new("SvStringsSocket", "width").prop_name = 'width'
        self.inputs.new("SvStringsSocket", "seed").prop_name = 'seed'
        self.inputs.new("SvStringsSocket", "pattern size").prop_name = 'pattern_size'
        self.outputs.new("SvColorSocket", "image")

    def draw_buttons(self, context, layout):
        layout.prop_search(self, 'image_name', bpy.data, 'images', text='', icon='IMAGE')
        layout.prop(self, 'rotate_patterns')
        layout.prop(self, 'periodic_input')
        layout.prop(self, 'tiling_output')

    def process(self):
        if not self.image_name:
            return

        image = load_image(self.image_name)
        wave = WaveFunctionCollapse(
            image,
            patter_size=self.pattern_size,
            periodic_input=self.periodic_input,
            rotate_patterns=self.rotate_patterns)

        output = wave.solve(
            output_size=(self.width, self.height),
            seed=self.seed,
            tiling_output=self.tiling_output,
            max_number_contradiction_tries=1)

        self.outputs['image'].sv_set(output)


def register():
    bpy.utils.register_class(SvWFCTextureNode)


def unregister():
    bpy.utils.unregister_class(SvWFCTextureNode)
