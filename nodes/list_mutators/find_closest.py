# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import repeat_last, fixed_iter


class SvFindClosestValue(SverchCustomTreeNode, bpy.types.Node):
    """Triggers: find search closest
    [[4,0,3,3]] val 5 =>
        values: [[4]]
        indexes: [[0]]
    [[5,0,3,7,8]] val 5, range 2 =>
        values: [[3,5,7]]
        indexes: [[2,0,3]]"""
    bl_idname = 'SvFindClosestValue'
    bl_label = 'Find Closest Value'
    bl_icon = 'VIEWZOOM'

    def update_mode(self, context):
        self.inputs['Range'].hide = False  # old nodes should not use the attr
        self.inputs['Range'].hide_safe = self.mode != 'range'
        self.process_node(context)

    value: FloatProperty(name='Value', update=lambda s, c: s.process_node(c))
    mode: EnumProperty(items=[(m, m, '') for m in ('single', 'range')],
                       update=update_mode)
    range: FloatProperty(default=0.1, update=lambda s, c: s.process_node(c))

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', 'Values').prop_name = 'value'
        self.inputs.new('SvStringsSocket', 'Data')
        s = self.inputs.new('SvStringsSocket', 'Range')
        s.prop_name = 'range'
        s.hide_safe = True
        self.outputs.new('SvStringsSocket', 'Closest values')
        self.outputs.new('SvStringsSocket', 'Closest indexes')

    def draw_buttons(self, context, layout):
        layout.prop(self, 'mode', expand=True)

    def process(self):
        vals = self.inputs['Values'].sv_get(deepcopy=False)
        data = self.inputs['Data'].sv_get(deepcopy=False, default=[])
        _range = self.inputs['Range'].sv_get(deepcopy=False)

        obj_n = max(len(vals), len(data), len(_range))
        out = []
        ind_out = []

        for v, d, r in zip(fixed_iter(vals, obj_n, []), fixed_iter(data, obj_n, []), fixed_iter(_range, obj_n, [])):
            if not all((v, d, r)):
                break

            extended_data = np.array(d + [-np.inf, np.inf])
            sorting_indexes = np.argsort(extended_data)

            if self.mode == 'range':
                len_input = max([len(v), len(r)])
                values = np.fromiter(repeat_last(v), float, count=len_input)
                range_values = np.fromiter(repeat_last(r), float, count=len_input)
                l_values = values - range_values
                l_indexes = np.searchsorted(extended_data, l_values, side='left', sorter=sorting_indexes)
                r_values = values + range_values
                r_indexes = np.searchsorted(extended_data, r_values, side='right', sorter=sorting_indexes)
                closest_indexes = [[sorting_indexes[i] for i in range(l, r)] for l, r in zip(l_indexes, r_indexes)]
                ind_out.append(closest_indexes)
                out.append([extended_data[ci].tolist() for ci in closest_indexes])
            else:
                right_indexes = np.searchsorted(extended_data, v, sorter=sorting_indexes)
                left_indexes = right_indexes - 1
                left_distance = v - extended_data[sorting_indexes[left_indexes]]
                left_distance = np.where(left_distance < 0, -left_distance, left_distance)
                right_distance = extended_data[sorting_indexes[right_indexes]] - v
                right_distance = np.where(right_distance < 0, -right_distance, right_distance)
                result_indexes = np.where(left_distance < right_distance, left_indexes, right_indexes)
                ind_out.append(sorting_indexes[result_indexes].tolist())
                out.append(extended_data[ind_out[-1]].tolist())

        self.outputs['Closest values'].sv_set(out)
        self.outputs['Closest indexes'].sv_set(ind_out)


register, unregister = bpy.utils.register_classes_factory([SvFindClosestValue])
