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

from math import radians
import bpy
from mathutils import Matrix
from bpy.props import StringProperty, BoolProperty, EnumProperty, FloatProperty, IntProperty, FloatVectorProperty
from sverchok.data_structure import node_id, Matrix_generate, updateNode, match_long_repeat, get_data_nesting_level, ensure_nesting_level
from sverchok.node_tree import SverchCustomTreeNode


class SvLampOutNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Lamp
    Tooltip: Generate Lamp objects
    """

    bl_idname = "SvLampOutNode"
    bl_label = "Lamp"
    bl_icon = 'LIGHT' #"OUTLINER_OB_LAMP"

    replacement_nodes = [('SvLightViewerNode', None, None)]

    activate: BoolProperty(
        name="Activate", default=True,
        description='When enabled this will process incoming data',
        update=updateNode)

    lamp_name: StringProperty(
        default='Lamp_Alpha',
        description="sets which base name the object will use",
        update=updateNode)

    lamp_types = [
            ("POINT", "Point", "Omnidirectional point light source", "LAMP_POINT", 0),
            ("SUN", "Sun", "Constant direction parallel light source", "LAMP_SUN", 1),
            ("SPOT", "Spot", "Direcitonal cone light source", "LAMP_SPOT", 2),
            ("HEMI", "Hemi", "180 degrees constant light source (not supported in Cycles)", "LAMP_HEMI", 3),
            ("AREA", "Area", "Directional area light source", "LAMP_AREA", 4)
        ]
    
    def update_type(self, context):
        is_spot = (self.type == 'SPOT')
        self.inputs['Spot Size'].hide_safe = not is_spot
        self.inputs['Spot Blend'].hide_safe = not is_spot
        updateNode(self, context)

    type: EnumProperty(
        name="Type", description="Light source type",
        items=lamp_types, default="POINT", update=update_type)

    area_types = [
            ("RECTANGLE", "Rectangle", "Rectangular area", 0),
            ("SQUARE", "Square", "Square area", 1)
        ]

    def update_area_type(self, context):
        square = (self.type != 'AREA' or self.area_type == 'SQUARE')
        self.inputs['Size'].hide_safe = not square
        self.inputs['Size X'].hide_safe = square
        self.inputs['Size Y'].hide_safe = square
        updateNode(self, context)

    area_type: EnumProperty(
        name="Area type", description="Area shape type", default="RECTANGLE",
        items=area_types, update=update_area_type)

    size: FloatProperty(
        name="Size", description="Light source size", default=0.1, update=updateNode)

    size_x: FloatProperty(
        name="Size X", description="Light source size", default=0.1, update=updateNode)
    
    size_y: FloatProperty(
        name="Size Y", description="Light source size", default=0.1, update=updateNode)

    spot_size: FloatProperty(
        name="Spot Size", description="Angle of the spotlight beam (degrees)",
        default=45.0, min=0.0, max=180.0, update=updateNode)

    spot_blend: FloatProperty(
        name="Spot Blend", description="The softness of the spotlight edge",
        default=0.15, min=0.0, max=1.0, update=updateNode)

    strength: FloatProperty(
        name="Strength", description="Lamp power",
        default=100.0, min=0.0, max=1000000, update=updateNode)

    show_cone: BoolProperty(
        name="Show cone", description="Draw transparent cone in the 3D View",
        default=False, update=updateNode)

    max_bounces: IntProperty(
        name="Max Bounces", description="Maximum number of bounces the lamp will contribute to the render",
        min=1, max=1000000, default=1024, update=updateNode)

    cast_shadow: BoolProperty(
        name="Cast shadow", description="Lamp casts shadows",
        default=True, update=updateNode)

    multiple_imporance: BoolProperty(
        name="Multiple importance", description="Use multiple importance sampling for the lamp",
        default=True, update=updateNode)

    use_nodes: BoolProperty(
        name="Use Nodes", description="Use node tree instead of directly specified color",
        default=True, update=updateNode)

    light_color: FloatVectorProperty(
        name="Color", description="Light color", update=updateNode,
        default=(1.0, 1.0, 1.0, 1.0), size=4, min=0.0, max=1.0, subtype='COLOR')

    emission_node_name: StringProperty(
        name="Emission Node", description="Name of Emission node in the lamp shader, that contains Sthrength and Color inputs",
        default="Emission", update=updateNode)

    properties_to_skip_iojson = ['type']

    def sv_init(self, context):
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

        self.outputs.new('SvObjectSocket', 'Objects')

    def draw_buttons(self, context, layout):
        view_icon = 'LIGHT' if self.activate else 'ERROR'
        layout.prop(self, "activate", text="UPD", toggle=True, icon=view_icon)
        layout.prop(self, 'lamp_name')
        layout.prop(self, 'type')
        if self.type == 'AREA':
            layout.prop(self, 'area_type')

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, 'use_nodes')
        layout.prop(self, 'max_bounces')
        layout.prop(self, 'cast_shadow')
        layout.prop(self, 'multiple_imporance')
        if self.type == 'SPOT':
            layout.prop(self, 'show_cone')
        layout.prop(self, 'emission_node_name')

    def get_children(self):
        objects = bpy.data.objects
        objs = [obj for obj in objects if obj.type == 'LIGHT']
        # critera, basename must be in object.keys and the value must be self.basemesh_name
        return [o for o in objs if o.get('basename') == self.lamp_name]

    def make_lamp(self, index, object):
        origin, size, size_x, size_y, strength, spot_size, spot_blend, color = object

        if get_data_nesting_level(color) == 2:
            color = color[0]
        if isinstance(size, (list, tuple)):
            size = size[0]
        if isinstance(size_x, (list, tuple)):
            size_x = size_x[0]
        if isinstance(size_y, (list, tuple)):
            size_y = size_y[0]
        if isinstance(strength, (list, tuple)):
            strength = strength[0]
        if isinstance(spot_size, (list, tuple)):
            spot_size = spot_size[0]
        if isinstance(spot_blend, (list, tuple)):
            spot_blend = spot_blend[0]

        scene = bpy.context.scene

        # ensure we use a collection
        collections = bpy.data.collections
        collection = collections.get(self.lamp_name)
        if not collection:
            collection = collections.new(self.lamp_name)
            bpy.context.scene.collection.children.link(collection)

        lamps_data = bpy.data.lights
        objects = bpy.data.objects
        name = self.lamp_name + "_" + str(index)

        if name in objects:
            lamp_object = objects[name]
            if lamp_object.data.type != self.type:
                lamp_object.data.type = self.type
        else:
            lamp_data = lamps_data.new(name = name, type = self.type)
            lamp_object = objects.new(name = name, object_data = lamp_data)
            collection.objects.link(lamp_object)

        lamp_object['idx'] = index
        lamp_object['madeby'] = self.name
        lamp_object['basename'] = self.lamp_name
        
        lamp_object.matrix_local = origin

        lamp = lamp_object.data

        lamp.type = self.type
        lamp.color = color[:3]
        if self.type in ('POINT', 'SUN', 'SPOT'):
            lamp.shadow_soft_size = size
        elif self.type == 'AREA' and self.area_type == 'SQUARE':
            lamp.shape = 'SQUARE'
            lamp.size = size
        elif self.type == 'AREA' and self.area_type == 'RECTANGLE':
            lamp.shape = 'RECTANGLE'
            lamp.size = size_x
            lamp.size_y = size_y
        
        if self.type == 'SPOT':
            lamp.spot_size = radians(spot_size)
            lamp.spot_blend = spot_blend
            lamp.show_cone = self.show_cone

        if lamp.cycles:
            lamp.cycles.max_bounces = self.max_bounces
            lamp.cycles.cast_shadow = self.cast_shadow
            lamp.cycles.use_multiple_importance_sampling = self.multiple_imporance
            lamp.use_nodes = True

            if self.emission_node_name and self.emission_node_name in lamp.node_tree.nodes:
                node = lamp.node_tree.nodes[self.emission_node_name]
                node.inputs['Strength'].default_value = strength
                if len(color) != 4:
                    raise Exception("Color data must contain 4 floats (RGBA), not {}".format(len(color)))
                node.inputs['Color'].default_value = color

    def process(self):

        if not self.activate:
            return

        origins = self.inputs['Origin'].sv_get()
        sizes_sq = self.inputs['Size'].sv_get()
        sizes_x = self.inputs['Size X'].sv_get()
        sizes_y = self.inputs['Size Y'].sv_get()
        spot_sizes = self.inputs['Spot Size'].sv_get()
        spot_blends = self.inputs['Spot Blend'].sv_get()
        strengths = self.inputs['Strength'].sv_get()
        colors = self.inputs['Color'].sv_get()
        # next is not needed
        # if get_data_nesting_level(colors) == 3:
            # colors = colors[0]

        objects = match_long_repeat([origins, sizes_sq, sizes_x, sizes_y, strengths, spot_sizes, spot_blends, colors])

        with self.sv_throttle_tree_update():
            for index, object in enumerate(zip(*objects)):
                self.make_lamp(index, object)

            self.remove_non_updated_objects(index)

            objs = self.get_children()
            self.outputs['Objects'].sv_set(objs)

    def remove_non_updated_objects(self, obj_index):
        objs = self.get_children()
        objs = [obj.name for obj in objs if obj['idx'] > obj_index]
        if not objs:
            return

        lamps_data = bpy.data.lights
        objects = bpy.data.objects
        collection = bpy.data.collections.get(self.lamp_name)

        # remove excess objects
        for object_name in objs:
            obj = objects[object_name]
            obj.hide_select = False
            collection.objects.unlink(obj)
            objects.remove(obj, do_unlink=True)

        # delete associated lamps data
        for object_name in objs:
            lamps_data.remove(lamps_data[object_name])

    def load_from_json(self, node_data: dict, import_version: float):
        if import_version <= 0.08:
            self.type = node_data.get("lamp_type", "POINT")


def register():
    bpy.utils.register_class(SvLampOutNode)

def unregister():
    bpy.utils.unregister_class(SvLampOutNode)
