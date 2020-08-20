# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from itertools import cycle

import bpy
from bpy.props import BoolProperty, StringProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.utils.nodes_mixins.generating_objects import BlenderObjects


class SvInstancerNodeMK2(bpy.types.Node, SverchCustomTreeNode, BlenderObjects):
    ''' Copy by mesh data from object input '''
    bl_idname = 'SvInstancerNodeMK2'
    bl_label = 'Obj instancer'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_INSTANCER'

    is_active: bpy.props.BoolProperty(
        name='Live',
        description="When enabled this will process incoming data",
        default=True,
        update=updateNode)

    full_copy: BoolProperty(name="Full Copy", update=updateNode)

    base_data_name: StringProperty(
        default='Alpha',
        description='stores the mesh name found in the object, this mesh is instanced',
        update=updateNode)

    collection: bpy.props.PointerProperty(type=bpy.types.Collection, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvObjectSocket', 'objects')
        self.inputs.new('SvMatrixSocket', 'matrix')
        self.outputs.new('SvObjectSocket', 'objects')

    def draw_buttons(self, context, layout):
        col = layout.column(align=True)
        row = col.row(align=True)
        row.column().prop(self, 'is_active', toggle=True)
        self.draw_object_properties(row)
        layout.prop(self, "base_data_name", text="", icon='OUTLINER_OB_MESH')
        layout.prop_search(self, 'collection', bpy.data, 'collections', text='', icon='GROUP')
        layout.prop(self, "full_copy", text="full copy", toggle=True)

    def process(self):

        if not self.is_active:
            return

        matrices = self.inputs['matrix'].sv_get(deepcopy=False, default=[])
        objects = self.inputs['objects'].sv_get(deepcopy=False, default=[])

        meshes = [obj.data for obj, m in zip(cycle(objects), matrices)]
        self.regenerate_objects([self.base_data_name], meshes, [self.collection])
        [setattr(prop.obj, 'matrix_local', m) for prop, m in zip(self.object_data, matrices)]

        self.outputs['objects'].sv_set([prop.obj for prop in self.object_data])

    def sv_copy(self, original):
        # object list should be clear other wise two nodes would have links to the same objects
        self.object_data.clear()


register, unregister = bpy.utils.register_classes_factory([SvInstancerNodeMK2])
