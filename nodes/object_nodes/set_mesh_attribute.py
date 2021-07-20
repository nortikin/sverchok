# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE
from itertools import chain, cycle

import bpy

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, fixed_iter, flat_iter
from sverchok.utils.handle_blender_data import correct_collection_length


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
    elif domain == 'FACE':
        amount = len(obj.data.polygons)
    else:
        raise TypeError(f'Unsupported domain {domain}')

    if value_type in ['FLOAT', 'INT', 'BOOLEAN']:
        data = list(fixed_iter(values, amount))
    elif value_type in ['FLOAT_VECTOR', 'FLOAT_COLOR']:
        data = [co for v in fixed_iter(values, amount) for co in v]
    elif value_type == 'FLOAT2':
        data = [co for v in fixed_iter(values, amount) for co in v[:2]]
    else:
        raise TypeError(f'Unsupported type {value_type}')

    if value_type in ["FLOAT", "INT", "BOOLEAN"]:
        attr.data.foreach_set("value", data)
    elif value_type in ["FLOAT_VECTOR", "FLOAT2"]:
        attr.data.foreach_set("vector", data)
    else:
        attr.data.foreach_set("color", data)

    attr.data.update()
    return out


class SvObjectsWithAttributes(bpy.types.PropertyGroup):
    obj: bpy.props.PointerProperty(type=bpy.types.Object)  # this can be None if object was deleted
    attr: bpy.props.StringProperty()

    def add_attr(self, obj, attr):
        self.obj = obj
        self.attr = attr

    def remove_attr(self):
        if self.obj is not None:
            attr = self.obj.data.attributes.get(self.attr)
            if attr:
                self.obj.data.attributes.remove(attr)


class SvSetMeshAttributeNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: set mesh attribute
    Tooltip: It adds an attribute to a mesh
    """
    bl_idname = 'SvSetMeshAttributeNode'
    bl_label = 'Set mesh attribute'
    bl_icon = 'SORTALPHA'

    def update_type(self, context):
        self.inputs['Value'].hide_safe = self.value_type not in ['FLOAT', 'INT', 'BOOLEAN']
        self.inputs['Value'].default_property_type = 'float' if self.value_type == 'FLOAT' else 'int'
        self.inputs['Vector'].hide_safe = self.value_type not in ['FLOAT_VECTOR', 'FLOAT2']
        self.inputs['Color'].hide_safe = self.value_type != 'FLOAT_COLOR'
        updateNode(self, context)

    domains = ['POINT', 'EDGE', 'CORNER', 'FACE']
    value_types = ['FLOAT', 'INT', 'FLOAT_VECTOR', 'FLOAT_COLOR', 'BOOLEAN', 'FLOAT2']

    domain: bpy.props.EnumProperty(items=[(i, i.capitalize(), '') for i in domains], update=updateNode)
    value_type: bpy.props.EnumProperty(items=[(i, i.capitalize(), '') for i in value_types], update=update_type)
    last_objects: bpy.props.CollectionProperty(type=SvObjectsWithAttributes)

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

    def sv_copy(self, original):
        self.last_objects.clear()

    def process(self):
        objects = self.inputs['Object'].sv_get(deepcopy=False, default=[])
        attr_name = self.inputs['Attr name'].sv_get(deepcopy=False, default=[])
        sock_name = 'Value' if self.value_type in ['FLOAT', 'INT', 'BOOLEAN'] else \
            'Vector' if self.value_type in ['FLOAT_VECTOR', 'FLOAT2'] else 'Color'
        values = self.inputs[sock_name].sv_get(deepcopy=False, default=[])

        # first step remove attributes from previous update if necessary
        iter_attr_names = chain(flat_iter(attr_name), cycle([None]))
        for last, obj, attr in zip(self.last_objects, chain(objects, cycle([None])), iter_attr_names):
            if last.obj != obj or last.attr != attr:
                last.remove_attr()
        correct_collection_length(self.last_objects, len(objects))

        # assign new attribute
        iter_attr_names = fixed_iter(flat_iter(attr_name), len(objects))
        for last, obj, attr, val in zip(self.last_objects, objects, iter_attr_names, fixed_iter(values, len(objects))):
            last.add_attr(obj, attr)
            set_attribute_node(obj=obj, values=val, attr_name=attr, domain=self.domain, value_type=self.value_type)

        self.outputs['Object'].sv_set(objects)


register, unregister = bpy.utils.register_classes_factory([SvObjectsWithAttributes, SvSetMeshAttributeNode])
