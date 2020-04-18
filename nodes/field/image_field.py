
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, StringProperty
from mathutils import kdtree
from mathutils import bvhtree

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat
from sverchok.utils.logging import info, exception

from sverchok.utils.field.image import load_image, SvImageScalarField, SvImageVectorField

class SvImageFieldNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Image Field
    Tooltip: Generate vector or scalar field from an Image data block
    """
    bl_idname = 'SvExImageFieldNode'
    bl_label = 'Image Field'
    bl_icon = 'IMAGE'

    planes = [
        ('XY', "XY", "XOY plane", 0),
        ('YZ', "YZ", "YOZ plane", 1),
        ('XZ', "XZ", "XOZ plane", 2)
    ]

    plane : EnumProperty(
        name = "Plane",
        items = planes,
        default = 'XY',
        update = updateNode)

    image_name : StringProperty(
        name = "Image",
        default = "image.png",
        update = updateNode)

    def draw_buttons(self, context, layout):
        layout.label(text="Image plane:")
        layout.prop(self, 'plane', expand=True)
        layout.prop_search(self, 'image_name', bpy.data, 'images', text='', icon='IMAGE')

    def sv_init(self, context):
        self.outputs.new('SvVectorFieldSocket', "RGB")
        self.outputs.new('SvVectorFieldSocket', "HSV")
        self.outputs.new('SvScalarFieldSocket', "Red")
        self.outputs.new('SvScalarFieldSocket', "Green")
        self.outputs.new('SvScalarFieldSocket', "Blue")
        self.outputs.new('SvScalarFieldSocket', "Hue")
        self.outputs.new('SvScalarFieldSocket', "Saturation")
        self.outputs.new('SvScalarFieldSocket', "Value")
        self.outputs.new('SvScalarFieldSocket', "Alpha")
        self.outputs.new('SvScalarFieldSocket', "RGB Average")
        self.outputs.new('SvScalarFieldSocket', "Luminosity")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return
        
        pixels = load_image(self.image_name)

        vfields_out = dict()
        if self.outputs['RGB'].is_linked:
            rgb = SvImageVectorField(pixels, 'RGB', plane=self.plane)
            vfields_out['RGB'] = [rgb]
        if self.outputs['HSV'].is_linked:
            hsv = SvImageVectorField(pixels, 'HSV', plane=self.plane)
            vfields_out['HSV'] = [hsv]

        sfields_out = dict()
        for channel in ['Red', 'Green', 'Blue', 'Hue', 'Saturation', 'Value', 'Alpha', 'RGB Average', 'Luminosity']:
            if self.outputs[channel].is_linked:
                field = SvImageScalarField(pixels, channel, plane=self.plane)
                sfields_out[channel] = [field]

        for space in vfields_out:
            self.outputs[space].sv_set(vfields_out[space])

        for channel in sfields_out:
            self.outputs[channel].sv_set(sfields_out[channel])

def register():
    bpy.utils.register_class(SvImageFieldNode)

def unregister():
    bpy.utils.unregister_class(SvImageFieldNode)

