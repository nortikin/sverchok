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
from sverchok.data_structure import updateNode, dataCorrect, repeat_last
from sverchok.utils.geom import LinearSpline, CubicSpline


def make_range(number):
    if number in {0, 1, 2} or number < 0:
        return [0.0]
    return np.linspace(0.0, 1.0, num=number, endpoint=True).tolist()



class SvInterpolationNodeMK3(bpy.types.Node, SverchCustomTreeNode):
    '''Advanced Vect. Interpolation'''
    bl_idname = 'SvInterpolationNodeMK3'
    bl_label = 'Vector Interpolation mk3'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_INTERPOLATION'

    def wrapped_updateNode(self, context):
        self.inputs['Interval'].prop_name = 'int_in' if self.infer_from_integer_input else 't_in'
        self.process_node(context)

    t_in: FloatProperty(name="t", default=.5, min=0, max=1, precision=5, update=updateNode)
    int_in: IntProperty(name="int in", default=10, min=3, update=updateNode)
    h: FloatProperty(default=.001, precision=5, update=updateNode)

    modes = [('SPL', 'Cubic', "Cubic Spline", 0),
             ('LIN', 'Linear', "Linear Interpolation", 1)]
    mode: EnumProperty(name='Mode', default="LIN", items=modes, update=updateNode)

    knot_modes = [('MANHATTAN', 'Manhattan', "Manhattan distance metric", 0),
                  ('DISTANCE', 'Euclidan', "Eudlcian distance metric", 1),
                  ('POINTS', 'Points', "Points based", 2),
                  ('CHEBYSHEV', 'Chebyshev', "Chebyshev distance", 3)]

    knot_mode: EnumProperty(
        name='Knot Mode', default="DISTANCE", items=knot_modes, update=updateNode)

    is_cyclic: BoolProperty(name="Cyclic", default=False, update=updateNode)
    infer_from_integer_input: BoolProperty(name="IntRange", default=False, update=wrapped_updateNode)

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
        row.prop(self, 'infer_from_integer_input',toggle=True)


    def draw_buttons_ext(self, context, layout):
        layout.prop(self, 'h')
        layout.prop(self, 'knot_mode')

    def process(self):

        if not any((s.is_linked for s in self.outputs)):
            return

        calc_tanget = self.outputs['Tanget'].is_linked or self.outputs['Unit Tanget'].is_linked
        norm_tanget = self.outputs['Unit Tanget'].is_linked

        h = self.h

        if self.inputs['Vertices'].is_linked:
            verts = self.inputs['Vertices'].sv_get()
            verts = dataCorrect(verts)
            t_ins = self.inputs['Interval'].sv_get()

            if self.infer_from_integer_input:
                t_ins = [make_range(int(value)) for value in t_ins[0]]

                if len(t_ins) > len(verts):
                    new_verts = verts[:]
                    for i in range(len(t_ins) - len(verts)):
                        new_verts.append(verts[-1])
                    verts = new_verts

            verts_out = []
            tanget_out = []
            norm_tanget_out = []
            for v, t_in in zip(verts, repeat_last(t_ins)):

                t_corr = np.array(t_in).clip(0, 1)

                if self.mode == 'LIN':
                    spline = LinearSpline(v, metric = self.knot_mode, is_cyclic = self.is_cyclic)
                    out = spline.eval(t_corr)
                    verts_out.append(out.tolist())

                    if calc_tanget:
                        tanget_out.append(spline.tangent(t_corr).tolist())

                else:  # SPL
                    spline = CubicSpline(v, metric = self.knot_mode, is_cyclic = self.is_cyclic)
                    out = spline.eval(t_corr)
                    verts_out.append(out.tolist())
                    if calc_tanget:
                        tangent = spline.tangent(t_corr, h)
                        if norm_tanget:
                            norm = np.linalg.norm(tangent, axis=1)
                            norm_tanget_out.append((tangent / norm[:, np.newaxis]).tolist())
                        tanget_out.append(tangent.tolist())

            outputs = self.outputs
            if outputs['Vertices'].is_linked:
                outputs['Vertices'].sv_set(verts_out)
            if outputs['Tanget'].is_linked:
                outputs['Tanget'].sv_set(tanget_out)
            if outputs['Unit Tanget'].is_linked:
                outputs['Unit Tanget'].sv_set(norm_tanget_out)


def register():
    bpy.utils.register_class(SvInterpolationNodeMK3)


def unregister():
    bpy.utils.unregister_class(SvInterpolationNodeMK3)
