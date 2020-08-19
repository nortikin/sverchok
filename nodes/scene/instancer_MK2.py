# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import itertools

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

    activate: BoolProperty(
        default=True,
        name='Show', description='Activate node?',
        update=updateNode)

    full_copy: BoolProperty(name="Full Copy", update=updateNode)

    base_data_name: StringProperty(
        default='Alpha',
        description='stores the mesh name found in the object, this mesh is instanced',
        update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvObjectSocket', 'objects')
        self.inputs.new('SvMatrixSocket', 'matrix')
        self.outputs.new('SvObjectSocket', 'objects')

    def draw_buttons(self, context, layout):
        row = layout.row(align=True)
        row.prop(self, "activate", text="Update")
        row = layout.row(align=True)
        row.prop(self, "full_copy", text="full copy", toggle=True)

        layout.label(text="Object base name")
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, "base_data_name", text="", icon='FILE_CACHE')

    def process(self):

        if not self.activate:
            return

        matrices = self.inputs['matrix'].sv_get(deepcopy=False)
        if not matrices:
            return

        objects = self.inputs['objects'].sv_get(deepcopy=False)
        if not objects:
            return

        meshes = [obj.data for obj, m in zip(itertools.cycle(objects), matrices)]
        self.regenerate_objects([self.base_data_name], meshes)
        [setattr(prop.obj, 'matrix_local', m) for prop, m in zip(self.objects, matrices)]

        self.outputs['objects'].sv_set([prop.obj for prop in self.objects])


register, unregister = bpy.utils.register_classes_factory([SvInstancerNodeMK2])
