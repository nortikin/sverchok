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

import numpy as np

import bpy
from bpy.props import EnumProperty, FloatProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.nodes_mixins.recursive_nodes import SvRecursiveNode

from sverchok.data_structure import updateNode, dataCorrect, repeat_last
from sverchok.utils.geom import LinearSpline, CubicSpline


def make_range(number, end_point):
    if number in {0, 1, 2} or number < 0:
        return np.array([0.0])
    return np.linspace(0.0, 1.0, num=number, endpoint=end_point)



class SvInterpolationNodeMK3(bpy.types.Node, SverchCustomTreeNode, SvRecursiveNode):
    """
    Triggers: Interp. Vector List
    Tooltip: Interpolate a list of vertices in a linear or cubic fashion
    """
    bl_idname = 'SvInterpolationNodeMK3'
    bl_label = 'Vector Interpolation'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_INTERPOLATION'

    def wrapped_updateNode(self, context):
        self.inputs['Interval'].prop_name = 'int_in' if self.infer_from_integer_input else 't_in'
        self.process_node(context)

    t_in: FloatProperty(
        name="t",
        default=.5,
        min=0, max=1,
        precision=5,
        update=updateNode)
    int_in: IntProperty(
        name="int in",
        default=10,
        min=3,
        update=updateNode)
    h: FloatProperty(
        default=.001,
        precision=5,
        update=updateNode)

    modes = [('SPL', 'Cubic', "Cubic Spline", 0),
             ('LIN', 'Linear', "Linear Interpolation", 1)]
    mode: EnumProperty(name='Mode', default="LIN", items=modes, update=updateNode)

    knot_modes = [('MANHATTAN', 'Manhattan', "Manhattan distance metric", 0),
                  ('DISTANCE', 'Euclidan', "Eudlcian distance metric", 1),
                  ('POINTS', 'Points', "Points based", 2),
                  ('CHEBYSHEV', 'Chebyshev', "Chebyshev distance", 3)]

    knot_mode: EnumProperty(
        name='Knot Mode',
        default="DISTANCE",
        items=knot_modes,
        update=updateNode)

    is_cyclic: BoolProperty(
        name="Cyclic",
        default=False,
        update=updateNode)

    infer_from_integer_input: BoolProperty(
        name="Int Range",
        default=False,
        update=wrapped_updateNode)

    end_point: BoolProperty(
        name="End Point",
        default=True,
        update=updateNode)

    output_numpy: BoolProperty(
        name='Output NumPy',
        description='Output NumPy arrays',
        default=False, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Vertices')
        self.inputs.new('SvStringsSocket', 'Interval').prop_name = 't_in'
        self.outputs.new('SvVerticesSocket', 'Vertices')
        self.outputs.new('SvVerticesSocket', 'Tanget')
        self.outputs.new('SvVerticesSocket', 'Unit Tanget')

    def draw_buttons(self, context, layout):
        layout.prop(self, 'mode', expand=True)
        row = layout.row(align=True)
        row.prop(self, 'is_cyclic', toggle=True)
        row.prop(self, 'infer_from_integer_input', toggle=True)
        if self.infer_from_integer_input:
            layout.prop(self, 'end_point')

    def rclick_menu(self, context, layout):
        layout.prop_menu_enum(self, "list_match", text="List Match")

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, 'list_match')
        self.draw_buttons(context, layout)
        layout.prop(self, 'h')
        layout.prop(self, 'knot_mode')
        layout.prop(self, 'output_numpy')

    def pre_setup(self):
        self.inputs['Vertices'].is_mandatory = True
        if self.infer_from_integer_input:
            self.inputs['Interval'].nesting_level = 1
            self.inputs['Interval'].pre_processing = 'ONE_ITEM'
        else:
            self.inputs['Interval'].nesting_level = 2
            self.inputs['Interval'].pre_processing = 'NONE'

    def process_data(self, params):
        verts, t_ins = params

        calc_tanget = self.outputs['Tanget'].is_linked or self.outputs['Unit Tanget'].is_linked
        norm_tanget = self.outputs['Unit Tanget'].is_linked
        h = self.h
        verts_out, tanget_out, norm_tanget_out = [], [], []
        for v, t_in in zip(verts, t_ins):
            if self.infer_from_integer_input:
                t_corr = make_range(int(t_in), self.end_point)
            else:
                t_corr = np.array(t_in).clip(0, 1)

            if self.mode == 'LIN':
                spline = LinearSpline(v, metric=self.knot_mode, is_cyclic=self.is_cyclic)
                out = spline.eval(t_corr)
                verts_out.append(out if self.output_numpy else out.tolist())

                if calc_tanget:
                    tanget_out.append(spline.tangent(t_corr) if self.output_numpy else spline.tangent(t_corr).tolist())

            else:  # SPL
                spline = CubicSpline(v, metric=self.knot_mode, is_cyclic=self.is_cyclic)
                out = spline.eval(t_corr)
                verts_out.append(out if self.output_numpy else out.tolist())
                if calc_tanget:
                    tangent = spline.tangent(t_corr, h)
                    if norm_tanget:
                        norm = np.linalg.norm(tangent, axis=1)
                        tangent_norm = tangent / norm[:, np.newaxis]
                        norm_tanget_out.append(tangent_norm if self.output_numpy else tangent_norm.tolist())
                    tanget_out.append(tangent if self.output_numpy else tangent.tolist())

        return verts_out, tanget_out, norm_tanget_out


register, unregister = bpy.utils.register_classes_factory([SvInterpolationNodeMK3])
