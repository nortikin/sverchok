# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import bpy

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, fixed_iter, throttle_and_update_node
from sverchok.utils.handling_nodes import vectorize


def set_attribute_node(*, obj=None, values=None, attr_name=None, domain='POINT', value_type='FLOAT'):
    if not obj:
        return {'obj': None}
    out = {'obj': obj}
    if not all([values, attr_name]):
        return out

    attr = obj.data.attributes.get(attr_name)
    if attr is None:
        attr = obj.data.attributes.new(attr_name, value_type, domain)
    elif attr.data_type != value_type or attr.domain != domain:
        obj.data.attributes.remove(attr)
        attr = obj.data.attributes.new(attr_name, value_type, domain)

    if domain == 'POINT':
        amount = len(obj.data.vertices)
    elif domain == 'EDGE':
        amount = len(obj.data.edges)
    elif domain == 'CORNER':
        amount = len(obj.data.loops)
    elif domain == 'POLYGON':
        amount = len(obj.data.polygons)
    else:
        raise TypeError(f'Unsupported domain {domain}')

    if value_type in ['FLOAT', 'INT', 'BOOLEAN']:
        data = list(fixed_iter(values, amount))
    elif value_type in ['FLOAT_VECTOR', 'FLOAT_COLOR']:
        data = [co for v in fixed_iter(values, amount) for co in v]
    else:
        raise TypeError(f'Unsupported type {value_type}')

    if value_type in ["FLOAT", "INT", "BOOLEAN"]:
        attr.data.foreach_set("value", data)
    elif value_type == "FLOAT_VECTOR":
        attr.data.foreach_set("vector", data)
    else:
        attr.data.foreach_set("color", data)

    attr.data.update()
    return out


def flat_iter(data):  # todo move to data structure
    """[1, [2, 3, [4]], 5] -> 1, 2, 3, 4, 5 """
    if isinstance(data, str):
        yield data
        return
    try:
        for v in data:
            yield from flat_iter(v)
    except TypeError:
        yield data


class SvSetAttributeNode(SverchCustomTreeNode, bpy.types.Node):  # todo MESH attribute
    """
    Triggers: todo
    """
    bl_idname = 'SvSetAttributeNode'
    bl_label = 'Set attribute'
    bl_icon = 'SORTALPHA'

    @throttle_and_update_node
    def update_type(self, context):
        self.inputs['Value'].hide_safe = self.value_type not in ['FLOAT', 'INT', 'BOOLEAN']
        self.inputs['Value'].default_property_type = 'float' if self.value_type == 'FLOAT' else 'int'
        self.inputs['Vector'].hide_safe = self.value_type != 'FLOAT_VECTOR'
        self.inputs['Color'].hide_safe = self.value_type != 'FLOAT_COLOR'
        updateNode(self, context)

    domains = ['POINT', 'EDGE', 'CORNER', 'POLYGON']
    value_types = ['FLOAT', 'INT', 'FLOAT_VECTOR', 'FLOAT_COLOR', 'BOOLEAN']

    domain: bpy.props.EnumProperty(items=[(i, i.capitalize(), '') for i in domains], update=updateNode)
    value_type: bpy.props.EnumProperty(items=[(i, i.capitalize(), '') for i in value_types], update=update_type)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'domain', text='Domain')
        layout.prop(self, 'value_type', text='Type')

    def sv_init(self, context):
        self.inputs.new('SvObjectSocket', 'Object')
        self.inputs.new('SvTextSocket', 'Attr name').use_prop = True
        self.inputs.new('SvStringsSocket', 'Value').use_prop = True
        s = self.inputs.new('SvVerticesSocket', 'Vector')
        s.hide_safe = True
        s.use_prop = True
        s = self.inputs.new('SvColorSocket', 'Color')
        s.hide_safe = True
        s.use_prop = True
        self.outputs.new('SvObjectSocket', "Object")

    def process(self):
        obj = self.inputs['Object'].sv_get(deepcopy=False, default=[])
        attr_name = self.inputs['Attr name'].sv_get(deepcopy=False, default=[])
        sock_name = 'Value' if self.value_type in ['FLOAT', 'INT', 'BOOLEAN'] else \
            'Vector' if self.value_type == 'FLOAT_VECTOR' else 'Color'
        values = self.inputs[sock_name].sv_get(deepcopy=False, default=[])

        attr_name = flat_iter(attr_name)

        result = vectorize(set_attribute_node, iter_number=len(obj))(obj=obj, values=values, attr_name=attr_name,
                                                                     domain=[self.domain], value_type=[self.value_type])

        self.outputs['Object'].sv_set(result['obj'])


register, unregister = bpy.utils.register_classes_factory([SvSetAttributeNode])
