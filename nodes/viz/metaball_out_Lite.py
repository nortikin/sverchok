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
from bpy.props import BoolProperty, FloatProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import match_long_cycle as mlc, updateNode


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
        self.inputs.new('SvObjectSocket', 'Meta Object')
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
        layout.prop(self, "threshold")

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, "view_resolution")
        layout.prop(self, "render_resolution")

    def setup_element(self, elements, origins, radiuss, stiffnesss, negates, meta_types):
        if len(origins) != len(elements):
            elements.clear()
            for i in range(len(origins)):
                elements.new()
        for e,o,r,s,n,mt in zip(elements, origins, radiuss, stiffnesss, negates, meta_types):
            center, rotation, scale = o.decompose()
            e.co = center
            if isinstance(mt, int):
                if mt not in self.meta_type_by_id:
                    raise Exception("`Types' input expects an integer number from 1 to 5")
                mt = self.meta_type_by_id[mt]
            e.type = mt
            e.radius = r
            e.stiffness = s
            e.rotation = rotation
            e.size_x, e.size_y, e.size_z = scale
            e.use_negative = bool(n)

    def process(self):
        Obj, Typ, Origs, Radi, Stiff, Neg = self.inputs
        if not (self.activate and Origs.is_linked):
            return
        meta_objectD = Obj.sv_get()[0].data
        meta_objectD.resolution = self.view_resolution
        meta_objectD.render_resolution = self.render_resolution
        meta_objectD.threshold = self.threshold
        origins = Origs.sv_get()
        radiuses = Radi.sv_get()[0]
        stiffnesses = Stiff.sv_get()[0]
        negation = Neg.sv_get([[0]])[0]
        types = Typ.sv_get()[0]
        mbo = meta_objectD.elements
        self.setup_element(mbo, *mlc([origins, radiuses, stiffnesses, negation, types]))
        if self.outputs['Objects'].is_linked:
            self.outputs['Objects'].sv_set(Obj.sv_get())


def register():
    bpy.utils.register_class(SvMetaballOutLiteNode)


def unregister():
    bpy.utils.unregister_class(SvMetaballOutLiteNode)
