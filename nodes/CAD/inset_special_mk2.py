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
from bpy.props import BoolProperty, FloatProperty, IntProperty, EnumProperty
from mathutils import Vector

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (
    updateNode, zip_long_repeat, make_repeaters)
from sverchok.utils.mesh.inset_faces import inset_special_np, inset_special_mathutils
from sverchok.utils.nodes_mixins.recursive_nodes import SvRecursiveNode
from sverchok.utils.nodes_mixins.sockets_config import ModifierLiteNode


class SvInsetSpecialMk2(
        ModifierLiteNode, SverchCustomTreeNode, bpy.types.Node, SvRecursiveNode):
    """
    Triggers: or Extrude (Fast)
    Tooltip: Fast Inset or extrude geometry

    """

    bl_idname = 'SvInsetSpecialMk2'
    bl_label = 'Inset Special'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_INSET'

    implentation_items = [
        ('mathutils', 'Mathutils (Legacy)', 'Slower (Legacy. Face order may differ with new implementation)', 0),
        ('numpy', 'Numpy', 'Faster (Face order may differ of Mathutils mode implementation)', 1)]
    implementation: bpy.props.EnumProperty(
        name='Implementation',
        items=implentation_items,
        default='numpy',
        update=updateNode
    )
    inset: FloatProperty(
        name='Inset',
        description='Inset amount',
        min=0.0,
        default=0.1, update=updateNode)
    distance: FloatProperty(
        name='Distance',
        description='Offset distance along normal',
        default=0.0, update=updateNode)

    ignore: IntProperty(name='Ignore', description='Skip polygons (mask of affected polygons)', default=0, update=updateNode)
    make_inner: IntProperty(name='Make Inner', description='Determine if inner face should be created (0-do not create, 1-create)', default=1, update=updateNode)

    zero_modes = [
        ("SKIP", "Skip", "Do not process such faces", 0),
        ("FAN", "Fan", "Make a fan-like structure from such faces", 1)
        ]

    zero_mode: EnumProperty(
        name="Zero inset faces",
        description="What to do with faces when inset is equal to zero",
        default="SKIP",
        items=zero_modes,
        update=updateNode)
    offset_modes = [
        ("CENTER", "Center", "Inset is measured as a proportion between the corners and the center of the polygon", 0),
        ("SIDES", "Sides", "Inset is measured as a constant distance to the sides of the polygon", 1),
        ("MATRIX", "Matrix", "Inset controlled by offset matrix", 2)
        ]
    def update_sockets(self, context):
        self.inputs['Inset'].hide_safe = self.offset_mode == 'MATRIX'
        self.inputs['Distance'].hide_safe = self.offset_mode == 'MATRIX'
        self.inputs['Offset Matrix'].hide_safe = self.offset_mode != 'MATRIX'
        updateNode(self, context)

    offset_mode: EnumProperty(
        name="Mode",
        description="How to interpret inset distance",
        default="CENTER",
        items=offset_modes,
        update=update_sockets)
    proportional: BoolProperty(
        name='Proportional',
        description='Multiply Inset by face perimeter',
        default=False,
        update=updateNode
    )
    concave_support: BoolProperty(
        name='Concave Support',
        description='Support concave polygons',
        default=False,
        update=updateNode
    )

    replacement_nodes = [
        ('SvExtrudeSeparateNode',
            dict(Vertices='Vertices', Polygons='Polygons', Distance='Height'),
            dict(Vertices='Vertices', Polygons='Polygons')),
        ('SvExtrudeSeparateLiteNode',
            dict(Vertices='Vertices', Polygons='Polygons'),
            dict(vertices='Vertices', Polygons='Polygons')),
        ('SvInsetFaces',
            dict(Vertices='Verts', Polygons='Faces', Distance='Depth'),
            dict(Vertices='Verts', Polygons='Faces'))
    ]

    def sv_init(self, context):
        i = self.inputs
        self.sv_new_input('SvVerticesSocket', "Vertices", is_mandatory=True, nesting_level=3)
        self.sv_new_input('SvStringsSocket', "Polygons", is_mandatory=True, nesting_level=3)
        i.new('SvStringsSocket', 'Inset').prop_name = 'inset'
        i.new('SvStringsSocket', 'Distance').prop_name = 'distance'
        i.new('SvStringsSocket', 'Ignore').prop_name = 'ignore'
        i.new('SvStringsSocket', 'Make Inner').prop_name = 'make_inner'
        i.new('SvVerticesSocket', 'Custom normal')
        self.sv_new_input('SvMatrixSocket', 'Offset Matrix',
                          nesting_level=2,
                          default_mode='MATRIX',
                          hide_safe=True)

        o = self.outputs
        o.new('SvVerticesSocket', 'Vertices')
        o.new('SvStringsSocket', 'Polygons')
        o.new('SvStringsSocket', 'Ignored')
        o.new('SvStringsSocket', 'Inset')
        o.new('SvStringsSocket', 'Original verts idx')
        o.new('SvStringsSocket', 'Original face idx')
        o.new('SvStringsSocket', 'Pols group')
        o.new('SvStringsSocket', 'New verts mask')

    def draw_buttons(self, context, layout):
        layout.prop(self, 'offset_mode')
        if self.offset_mode == 'SIDES':
            layout.prop(self, 'proportional')
    def draw_buttons_ext(self, context, layout):

        layout.prop(self, "list_match")
        layout.prop(self, "zero_mode")
        layout.prop(self, "implementation")
        layout.prop(self, "concave_support")

    def process_data(self, params):

        o = self.outputs

        output = [[] for s in self.outputs]
        output_old_face_id = o['Original face idx'].is_linked
        output_old_vert_id = o['Original verts idx'].is_linked
        output_pols_groups = o['Pols group'].is_linked
        output_new_verts_mask = o['New verts mask'].is_linked
        for verts, pols, inset_rates_s, distance_vals_s, ignores_s, make_inners_s, custom_normals, matrices in zip_long_repeat(*params):
            if self.implementation == 'mathutils':

                inset_rates, distance_vals, ignores, make_inners = make_repeaters([inset_rates_s, distance_vals_s, ignores_s, make_inners_s])

                func_args = {
                    'vertices': [Vector(vec) for vec in verts],
                    'faces': pols,
                    'inset_rates': inset_rates,
                    'distances': distance_vals,
                    'ignores': ignores,
                    'make_inners': make_inners,
                    'zero_mode': self.zero_mode
                }
                res = inset_special_mathutils(**func_args)
            else:
                func_args = {
                    'vertices': verts,
                    'faces': pols,
                    'inset_rates': inset_rates_s,
                    'distances': distance_vals_s,
                    'ignores': ignores_s,
                    'make_inners': make_inners_s,
                    'custom_normals': custom_normals,
                    'matrices': matrices,
                    'zero_mode': self.zero_mode,
                    'offset_mode': self.offset_mode,
                    'proportional':self.proportional,
                    'concave_support':self.concave_support,
                    'output_old_face_id':output_old_face_id,
                    'output_old_v_id':output_old_vert_id,
                    'output_pols_groups':output_pols_groups,
                    'output_new_verts_mask':output_new_verts_mask
                }
                res = inset_special_np(**func_args)
            if not res:
                res = verts, pols, [], [], [], [], [], []

            for sub_res, socket in zip(res, output):
                socket.append(sub_res)

        return output




def register():
    bpy.utils.register_class(SvInsetSpecialMk2)


def unregister():
    bpy.utils.unregister_class(SvInsetSpecialMk2)
