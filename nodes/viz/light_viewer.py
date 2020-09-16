# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE
from itertools import cycle

import bpy

from sverchok.data_structure import updateNode
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.nodes_mixins.generating_objects import SvViewerNode, SvLightData
from sverchok.utils.handle_blender_data import correct_collection_length


class SvLightViewerNode(SvViewerNode, bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: lamp light sun
    Tooltip: Generate Lamp objects
    """

    bl_idname = "SvLightViewerNode"
    bl_label = "Light viewer"
    bl_icon = 'LIGHT'

    lamp_types = [
        ("POINT", "Point", "Omnidirectional point light source", "LAMP_POINT", 0),
        ("SUN", "Sun", "Constant direction parallel light source", "LAMP_SUN", 1),
        ("SPOT", "Spot", "Direcitonal cone light source", "LAMP_SPOT", 2),
        ("AREA", "Area", "Directional area light source", "LAMP_AREA", 3)
    ]

    shape_types = [
        ("RECTANGLE", "Rectangle", "Rectangular area", 0),
        ("SQUARE", "Square", "Square area", 1),
        ("ELLIPSE", "Ellipse", "Ellipse area", 2),
        ("DISK", "Disk", "Disk area", 3)
    ]

    def update_light_type(self, context):
        is_spot = (self.light_type == 'SPOT')
        self.inputs['Spot Size'].hide_safe = not is_spot
        self.inputs['Spot Blend'].hide_safe = not is_spot
        [setattr(prop.light, 'type', self.light_type) for prop in self.light_data]

        square = (self.light_type != 'AREA' or self.shape_type in ('SQUARE', 'DISK'))
        self.inputs['Size'].hide_safe = not square
        self.inputs['Size X'].hide_safe = square
        self.inputs['Size Y'].hide_safe = square

    def update_shape_type(self, context):
        square = (self.light_type != 'AREA' or self.shape_type in ('SQUARE', 'DISK'))
        self.inputs['Size'].hide_safe = not square
        self.inputs['Size X'].hide_safe = square
        self.inputs['Size Y'].hide_safe = square
        updateNode(self, context)

    light_data: bpy.props.CollectionProperty(type=SvLightData)

    light_type: bpy.props.EnumProperty(
        name="Type", description="Light source type",
        items=lamp_types, default="POINT", update=update_light_type)

    shape_type: bpy.props.EnumProperty(
        name="Shape", description="Area shape type", default="RECTANGLE",
        items=shape_types, update=update_shape_type)

    size: bpy.props.FloatProperty(
        name="Size", description="Light source size", default=0.1, update=updateNode)

    size_x: bpy.props.FloatProperty(
        name="Size X", description="Light source size", default=0.1, update=updateNode)

    size_y: bpy.props.FloatProperty(
        name="Size Y", description="Light source size", default=0.1, update=updateNode)

    spot_size: bpy.props.FloatProperty(
        name="Spot Size", description="Angle of the spotlight beam",
        default=1.57, update=updateNode)

    spot_blend: bpy.props.FloatProperty(
        name="Spot Blend", description="The softness of the spotlight edge",
        default=0.15, min=0.0, max=1.0, update=updateNode)

    strength: bpy.props.FloatProperty(
        name="Strength", description="Lamp power",
        default=100.0, min=0.0, max=1000000, update=updateNode)

    show_cone: bpy.props.BoolProperty(
        name="Show cone", description="Draw transparent cone in the 3D View",
        default=False, update=updateNode)

    cast_shadow: bpy.props.BoolProperty(
        name="Cast shadow", description="Lamp casts shadows",
        default=True, update=updateNode)

    light_color: bpy.props.FloatVectorProperty(
        name="Color", description="Light color", update=updateNode,
        default=(1.0, 1.0, 1.0, 1.0), size=4, min=0.0, max=1.0, subtype='COLOR')

    def sv_init(self, context):
        self.init_viewer()
        self.inputs.new('SvMatrixSocket', 'Origin')
        self.inputs.new('SvStringsSocket', 'Size').prop_name = 'size'

        i = self.inputs.new('SvStringsSocket', 'Size X')
        i.prop_name = 'size_x'
        i.hide_safe = True

        i = self.inputs.new('SvStringsSocket', 'Size Y')
        i.prop_name = 'size_y'
        i.hide_safe = True

        i = self.inputs.new('SvStringsSocket', 'Spot Size')
        i.prop_name = 'spot_size'
        i.hide_safe = True

        i = self.inputs.new('SvStringsSocket', 'Spot Blend')
        i.prop_name = 'spot_blend'
        i.hide_safe = True

        i = self.inputs.new('SvStringsSocket', 'Strength')
        i.prop_name = 'strength'

        color_socket = self.inputs.new('SvColorSocket', "Color")
        color_socket.prop_name = 'light_color'

    def draw_buttons(self, context, layout):
        self.draw_viewer_properties(layout)

        layout.prop(self, 'light_type')
        if self.light_type == 'AREA':
            layout.prop(self, 'shape_type')

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, 'cast_shadow')
        layout.prop(self, 'show_cone')

    def draw_label(self):
        if self.hide:
            return f"LiV {self.base_data_name}"
        else:
            return "Light viewer"

    def process(self):

        if not self.is_active:
            return

        origins = self.inputs['Origin'].sv_get(deepcopy=False, default=[None])
        sizes_sq = self.inputs['Size'].sv_get(deepcopy=False, default=[None])
        sizes_x = self.inputs['Size X'].sv_get(deepcopy=False, default=[None])
        sizes_y = self.inputs['Size Y'].sv_get(deepcopy=False, default=[None])
        spot_sizes = self.inputs['Spot Size'].sv_get(deepcopy=False, default=[None])
        spot_blends = self.inputs['Spot Blend'].sv_get(deepcopy=False, default=[None])
        strengths = self.inputs['Strength'].sv_get(deepcopy=False, default=[None])
        colors = self.inputs['Color'].sv_get(deepcopy=False, default=[None])

        objects_number = 0 if origins == [None] else max(
            [len(i) if i != [None] else 0 for i in
                [origins, sizes_sq, sizes_x, sizes_y, spot_sizes, spot_blends, strengths, colors]])

        correct_collection_length(self.light_data, objects_number)
        [props.regenerate_light(self.base_data_name, self.light_type) for props in self.light_data]

        self.regenerate_objects([self.base_data_name], [prop.light for prop in self.light_data], [self.collection])
        [setattr(prop.obj, 'matrix_local', m) for prop, m in zip(self.object_data, cycle(origins))]

        for prop, size, size_x, size_y, strength, color, spot_size, spot_blend in zip(
                self.light_data, cycle(sizes_sq), cycle(sizes_x), cycle(sizes_y), cycle(strengths), cycle(colors),
                cycle(spot_sizes), cycle(spot_blends)):

            prop.light.energy = strength[0]
            prop.light.color = color[0][:3]

            if self.light_type in ('POINT', 'SUN'):
                prop.light.shadow_soft_size = size[0]

            elif self.light_type == 'SPOT':
                prop.light.shadow_soft_size = size[0]
                prop.light.spot_size = spot_size[0]
                prop.light.spot_blend = spot_blend[0]
                prop.light.show_cone = self.show_cone

            elif self.light_type == 'AREA':
                prop.light.shape = self.shape_type

                if self.shape_type in ('SQUARE', 'DISK'):
                    prop.light.shadow_soft_size = size[0]

                else:
                    prop.light.size = size_x[0]
                    prop.light.size_y = size_y[0]

            if bpy.context.scene.render.engine == 'BLENDER_EEVEE':
                prop.light.use_shadow = self.cast_shadow
            elif bpy.context.scene.render.engine == 'CYCLES':
                prop.light.cycles.cast_shadow = self.cast_shadow

        self.outputs['Objects'].sv_set([obj_data.obj for obj_data in self.object_data])

    def sv_copy(self, other):
        super().sv_copy(other)
        self.light_data.clear()

    @property
    def properties_to_skip_iojson(self):
        return super().properties_to_skip_iojson + ['light_data']

    def storage_get_data(self, storage):
        super().storage_get_data(storage)
        storage["lamp_type"] = self.light_type

    def storage_set_data(self, storage):
        super().storage_get_data(storage)
        self.light_type = storage.get("lamp_type", "POINT")


register, unregister = bpy.utils.register_classes_factory([SvLightViewerNode])
