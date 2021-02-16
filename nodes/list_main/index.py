# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import fixed_iter, repeat_last, throttle_tree_update, updateNode
from typing import Iterator, Iterable


class SvIndexListNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: index find
    Tooltip: Returns index of item position in given data or -1 if item is not in data
    """
    bl_idname = 'SvIndexListNode'
    bl_label = 'List index'
    bl_icon = 'VIEWZOOM'

    def update_mode(self, context):
        with throttle_tree_update(self):
            self.inputs['Start index'].hide_safe = not self.use_range
            self.inputs['End index'].hide_safe = not self.use_range
        updateNode(self, context)

    level: bpy.props.IntProperty(name='Level', default=2, min=1, update=updateNode)
    use_range: bpy.props.BoolProperty(name='Use range', update=update_mode)

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', 'data')
        self.inputs.new('SvStringsSocket', 'Item')
        s = self.inputs.new('SvStringsSocket', 'Start index')
        s.use_prop = True
        s.default_property_type = 'int'
        s.hide_safe = True
        s = self.inputs.new('SvStringsSocket', 'End index')
        s.use_prop = True
        s.default_property_type = 'int'
        s.default_int_property = -1
        s.hide_safe = True
        self.outputs.new('SvStringsSocket', 'Index')

    def draw_buttons(self, context, layout):
        col = layout.column()
        col.prop(self, 'level')
        col.prop(self,'use_range')

    def process(self):
        data = self.inputs['data'].sv_get(deepcopy=False, default=[])
        items = self.inputs['Item'].sv_get(deepcopy=False, default=[])

        if not all((data, items)):
            self.outputs['Index'].sv_set([])
            return

        start_indexes = self.inputs['Start index'].sv_get(deepcopy=False)
        end_indexes = self.inputs['End index'].sv_get(deepcopy=False)

        unpack_data = list(list_level_iter(data, self.level))

        max_len = max(len(unpack_data), len(items), len(start_indexes), len(end_indexes))

        out_indexes = []
        for lst, its, starts, ends in zip(
                repeat_last(unpack_data),
                fixed_iter(items, max_len),
                fixed_iter(start_indexes, max_len),
                fixed_iter(end_indexes, max_len)):

            indexes = []
            for it, s, e in zip(its, repeat_last(starts), repeat_last(ends)):
                try:
                    indexes.append(lst.index(it, *([s, e] if self.use_range else [])))
                except ValueError:
                    indexes.append(-1)
            out_indexes.append(indexes)

        self.outputs['Index'].sv_set(out_indexes)


def list_level_iter(lst: list, level: int, _current_level: int = 1) -> Iterator[list]:
    """
    Iterate over all lists with given nesting
    With level 1 it will return the given list
    With level 2 it will iterate over all nested lists in the main one
    If a level does not have lists on that level it will return empty list
    _current_level - for internal use only
    """
    if _current_level < level:
        try:
            for nested_lst in lst:
                if not isinstance(nested_lst, Iterable):
                    raise TypeError
                yield from list_level_iter(nested_lst, level, _current_level + 1)
        except TypeError:
            yield []
    else:
        yield lst


register, unregister = bpy.utils.register_classes_factory([SvIndexListNode])
