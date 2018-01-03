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
from mathutils import Matrix
from bpy.props import StringProperty, BoolProperty, FloatProperty, EnumProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import SvGetSocketAnyType, node_id, Matrix_generate, match_long_repeat, updateNode
from sverchok.utils.sv_viewer_utils import greek_alphabet
from sverchok.utils.sv_obj_helper import SvObjHelper

class SvMetaballOutNode(bpy.types.Node, SverchCustomTreeNode, SvObjHelper):
    '''Create Blender's metaball object'''
    bl_idname = 'SvMetaballOutNode'
    bl_label = 'Metaball'
    bl_icon = 'META_BALL'

    data_kind = StringProperty(default='META')

    meta_types = [
            ("BALL", "Ball", "Ball", "META_BALL", 1),
            ("CAPSULE", "Capsule", "Capsule", "META_CAPSULE", 2),
            ("PLANE", "Plane", "Plane", "META_PLANE", 3),
            ("ELLIPSOID", "Ellipsoid", "Ellipsoid", "META_ELLIPSOID", 4),
            ("CUBE", "Cube", "Cube", "META_CUBE", 5)
        ]

    meta_type_by_id = dict((item[4], item[0]) for item in meta_types)

    meta_type = EnumProperty(name='Meta type',
            description = "Meta object type",
            items = meta_types, update=updateNode)

    radius = FloatProperty(
        name='Radius',
        description='Metaball radius',
        default=1.0, min=0.0, update=updateNode)

    stiffness = FloatProperty(
        name='Stiffness',
        description='Metaball stiffness',
        default=2.0, min=0.0, update=updateNode)

    view_resolution = FloatProperty(
        name='Resolution (viewport)',
        description='Resolution for viewport',
        default=0.2, min=0.0, max=1.0, update=updateNode)

    render_resolution = FloatProperty(
        name='Resolution (render)',
        description='Resolution for rendering',
        default=0.1, min=0.0, max=1.0, update=updateNode)

    threshold = FloatProperty(
        name='Threshold',
        description='Influence of meta elements',
        default=0.6, min=0.0, max=5.0, update=updateNode)

    def get_metaball_name(self, idx):
        if idx == 1:
            return self.basedata_name
        else:
            return self.basedata_name + '.' + str("%04d" % idx)

    def create_metaball(self):
        scene = bpy.context.scene
        objects = bpy.data.objects
        object_name = self.get_metaball_name(1)
        metaball_data = bpy.data.metaballs.new(object_name)
        metaball_object = self.get_or_create_object(object_name, 1, metaball_data)

        return metaball_object

    def find_metaball(self):
        children = self.get_children()
        if children:
            return children[0]
        else:
            return None

    def sv_init(self, context):

        self.inputs.new('StringsSocket', 'Types').prop_name = "meta_type"
        self.inputs.new('MatrixSocket', 'Origins')
        self.inputs.new('StringsSocket', "Radius").prop_name = "radius"
        self.inputs.new('StringsSocket', "Stiffness").prop_name = "stiffness"
        self.inputs.new('StringsSocket', 'Negation')
        self.outputs.new('SvObjectSocket', "Objects")

    def draw_buttons(self, context, layout):
        self.draw_live_and_outliner(context, layout)
        self.draw_object_buttons(context, layout)
        layout.prop(self, "threshold")

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        self.draw_ext_object_buttons(context, layout)
        layout.prop(self, "view_resolution")
        layout.prop(self, "render_resolution")

    def update_material(self):
        if bpy.data.materials.get(self.material):
            metaball_object = self.find_metaball()
            if metaball_object:
                metaball_object.active_material = bpy.data.materials[self.material]

    def process(self):
        if not self.activate:
            return

        if not self.inputs['Origins'].is_linked:
            return

        metaball_object = self.find_metaball()
        if not metaball_object:
            metaball_object = self.create_metaball()
            self.debug("Created new metaball")

        metaball_object.data.resolution = self.view_resolution
        metaball_object.data.render_resolution = self.render_resolution
        metaball_object.data.threshold = self.threshold

        self.label = metaball_object.name

        origins = self.inputs['Origins'].sv_get()
        origins = Matrix_generate(origins)
        radiuses = self.inputs['Radius'].sv_get()[0]
        stiffnesses = self.inputs['Stiffness'].sv_get()[0]
        negation = self.inputs['Negation'].sv_get(default=[[0]])[0]
        types = self.inputs['Types'].sv_get()[0]

        items = match_long_repeat([origins, radiuses, stiffnesses, negation, types])
        items = list(zip(*items))

        def setup_element(element, item):
            (origin, radius, stiffness, negate, meta_type) = item
            center, rotation, scale = origin.decompose()
            element.co = center[:3]
            if isinstance(meta_type, int):
                if meta_type not in self.meta_type_by_id:
                    raise Exception("`Types' input expects an integer number from 1 to 5")
                meta_type = self.meta_type_by_id[meta_type]
            element.type = meta_type
            element.radius = radius
            element.stiffness = stiffness
            element.rotation = rotation
            element.size_x = scale[0]
            element.size_y = scale[1]
            element.size_z = scale[2]
            element.use_negative = bool(negate)

        if len(items) == len(metaball_object.data.elements):
            #self.debug('Updating existing metaball data')

            for (item, element) in zip(items, metaball_object.data.elements):
                setup_element(element, item)
        else:
            #self.debug('Recreating metaball data')
            metaball_object.data.elements.clear()

            for item in items:
                element = metaball_object.data.elements.new()
                setup_element(element, item)
        
        self.set_corresponding_materials()

        if 'Objects' in self.outputs:
            self.outputs['Objects'].sv_set([metaball_object])


def register():
    bpy.utils.register_class(SvMetaballOutNode)

def unregister():
    bpy.utils.unregister_class(SvMetaballOutNode)

