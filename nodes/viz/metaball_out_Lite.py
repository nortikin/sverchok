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
from sverchok.data_structure import match_long_cycle, updateNode


class SvMetaballOutLiteNode(bpy.types.Node, SverchCustomTreeNode):
    '''Create Blender's metaball object Lite'''
    bl_idname = 'SvMetaballOutLiteNode'
    bl_label = 'Metaball Lite'
    bl_icon = 'META_BALL'

    activate = BoolProperty(
        name='Activate',
        default=True,
        description='When enabled this will process incoming data',
        update=updateNode)

    meta_name = StringProperty(default='SvMetaBall', name="Base name", update=updateNode)

    meta_types = [
            ("BALL", "Ball(1)", "Ball", "META_BALL", 1),
            ("CAPSULE", "Capsule(2)", "Capsule", "META_CAPSULE", 2),
            ("PLANE", "Plane(3)", "Plane", "META_PLANE", 3),
            ("ELLIPSOID", "Ellipsoid(4)", "Ellipsoid", "META_ELLIPSOID", 4),
            ("CUBE", "Cube(5)", "Cube", "META_CUBE", 5)
        ]

    meta_type_by_id = dict((item[4], item[0]) for item in meta_types)

    meta_type = EnumProperty(name='Meta type', items=meta_types, update=updateNode)

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

    def sv_init(self, context):
        self.inputs.new('StringsSocket', 'Types').prop_name = "meta_type"
        self.inputs.new('MatrixSocket', 'Origins')
        self.inputs.new('StringsSocket', "Radius").prop_name = "radius"
        self.inputs.new('StringsSocket', "Stiffness").prop_name = "stiffness"
        self.inputs.new('StringsSocket', 'Negation')
        self.outputs.new('SvObjectSocket', "Objects")

    def draw_buttons(self, context, layout):
        view_icon = 'BLENDER' if self.activate else 'ERROR'
        row = layout.row(align=True)
        row.column().prop(self, "activate", text="UPD", toggle=True, icon=view_icon)
        row.separator()
        col = layout.column(align=True)
        col.prop(self, "meta_name", text='', icon='OUTLINER_OB_META')
        layout.prop(self, "threshold")

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, "view_resolution")
        layout.prop(self, "render_resolution")

    def setup_element(self, element, item):
        (origin, radius, stiffness, negate, meta_type) = item
        center, rotation, scale = origin.decompose()
        element.co = center
        if isinstance(meta_type, int):
            if meta_type not in self.meta_type_by_id:
                raise Exception("`Types' input expects an integer number from 1 to 5")
            meta_type = self.meta_type_by_id[meta_type]
        element.type = meta_type
        element.radius = radius
        element.stiffness = stiffness
        element.rotation = rotation
        element.size_x, element.size_y, element.size_z = scale
        element.use_negative = bool(negate)

    def process(self):
        Typ, Origs, Radi, Stiff, Neg = self.inputs
        if not (self.activate and Origs.is_linked):
            return
        if not self.meta_name in bpy.data.objects:
            scene = bpy.context.scene
            objects = bpy.data.objects
            metaball_data = bpy.data.metaballs.new("MetaBall")
            metaball_object = bpy.data.objects.new(self.meta_name, metaball_data)
            scene.objects.link(metaball_object)
            scene.update()
        metaball_object = bpy.data.objects[self.meta_name]
        metaball_object.data.resolution = self.view_resolution
        metaball_object.data.render_resolution = self.render_resolution
        metaball_object.data.threshold = self.threshold
        self.label = metaball_object.name
        origins = [Matrix(m) for m in Origs.sv_get()]
        radiuses = Radi.sv_get()[0]
        stiffnesses = Stiff.sv_get()[0]
        negation = Neg.sv_get([[0]])[0]
        types = Typ.sv_get()[0]
        items = match_long_cycle([origins, radiuses, stiffnesses, negation, types])
        items = list(zip(*items))
        if len(items) == len(metaball_object.data.elements):
            # Updating existing metaball data
            for (item, element) in zip(items, metaball_object.data.elements):
                self.setup_element(element, item)
        else:
            # Recreating metaball data
            metaball_object.data.elements.clear()
            for item in items:
                element = metaball_object.data.elements.new()
                self.setup_element(element, item)
        self.outputs['Objects'].sv_set([metaball_object])


def register():
    bpy.utils.register_class(SvMetaballOutLiteNode)


def unregister():
    bpy.utils.unregister_class(SvMetaballOutLiteNode)
