# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

import bpy
from sverchok.data_structure import fixed_iter
from sverchok.node_tree import SverchCustomTreeNode


def read_mesh_attribute(obj, name):
    attr = obj.data.attributes[name]

    if attr.data_type == 'FLOAT':
        out = np.zeros(len(attr.data), dtype=np.float32)
        attr.data.foreach_get('value', out)
    elif attr.data_type == 'INT':
        out = np.zeros(len(attr.data), dtype=int)
        attr.data.foreach_get('value', out)
    elif attr.data_type == 'BOOLEAN':
        out = np.zeros(len(attr.data), dtype=bool)
        attr.data.foreach_get('value', out)
    elif attr.data_type == 'FLOAT_VECTOR':
        out = np.zeros(len(attr.data) * 3, dtype=np.float32)
        attr.data.foreach_get('vector', out)
        out.shape = (-1, 3)
    elif attr.data_type == 'FLOAT2':
        out = np.zeros(len(attr.data) * 2, dtype=np.float32)
        attr.data.foreach_get('vector', out)
        out.shape = (-1, 2)
    elif attr.data_type == 'FLOAT_COLOR':
        out = np.zeros(len(attr.data) * 4, dtype=np.float32)
        attr.data.foreach_get('color', out)
        out.shape = (-1, 4)
    elif attr.data_type == 'BYTE_COLOR':
        # it seems blender keeps the values as floats internally
        out = np.zeros(len(attr.data) * 4)
        attr.data.foreach_get('color', out)
        out *= 255
        out = out.astype(np.uint8)
        out.shape = (-1, 4)
    else:
        raise TypeError(f"Unknown {attr.data_type=}")
    return out


class SvNamedMeshAttributeNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: object mesh
    Tooltip: Reading mesh attribute
    """
    bl_idname = 'SvNamedMeshAttributeNode'
    bl_label = 'Named Attribute'
    bl_icon = 'SORTALPHA'

    def sv_init(self, context):
        self.inputs.new('SvObjectSocket', 'Object')
        self.inputs.new('SvTextSocket', 'Name').use_prop = True
        self.outputs.new('SvObjectSocket', "Object")
        self.outputs.new('SvStringsSocket', "Attribute")

    def process(self):
        objs = self.inputs['Object'].sv_get(deepcopy=False, default=[])
        names = self.inputs['Name'].sv_get(deepcopy=False)

        attrs = []
        names = fixed_iter(names, len(objs))
        for obj, name in zip(objs, names):
            name = name[0]
            if name:
                attrs.append(read_mesh_attribute(obj, name))
            else:
                attrs.append([])

        self.outputs['Object'].sv_set(objs)
        self.outputs['Attribute'].sv_set(attrs)


register, unregister = bpy.utils.register_classes_factory(
    [SvNamedMeshAttributeNode])
