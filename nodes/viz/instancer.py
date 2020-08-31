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
from sverchok.utils.nodes_mixins.generating_objects import SvViewerNode


class SvInstancerNodeMK3(SvViewerNode, bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: copy instancing duplicate

    Copy by mesh data from object input
    """
    bl_idname = 'SvInstancerNodeMK3'
    bl_label = 'Obj instancer'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_INSTANCER'

    def update_full_copy(self, context):
        if self.full_copy:
            props_and_samples = zip(self.object_data, cycle(self.inputs['objects'].sv_get(default=[], deepcopy=False)))
            for prop, template in props_and_samples:
                prop.recreate_object(template)
        else:
            [prop.recreate_object() for prop in self.object_data]
        updateNode(self, context)

    full_copy: BoolProperty(name="Full Copy", update=update_full_copy, 
                            description="All properties related with given objects will be copied into instances")

    def sv_init(self, context):
        self.init_viewer()
        self.inputs.new('SvObjectSocket', 'objects')
        self.inputs.new('SvMatrixSocket', 'matrix')

    def draw_buttons(self, context, layout):
        self.draw_viewer_properties(layout)
        layout.prop(self, "full_copy", text="full copy", toggle=True)

    def process(self):

        if not self.is_active:
            return

        matrices = self.inputs['matrix'].sv_get(deepcopy=False, default=[])
        objects = self.inputs['objects'].sv_get(deepcopy=False, default=[])

        objects = [obj for obj, m in zip(cycle(objects), matrices)]
        meshes = [obj.data for obj, m in zip(cycle(objects), matrices)]
        self.regenerate_objects([self.base_data_name], meshes, [self.collection], objects if self.full_copy else [None])
        [setattr(prop.obj, 'matrix_local', m) for prop, m in zip(self.object_data, matrices)]  # update???

        self.outputs['Objects'].sv_set([prop.obj for prop in self.object_data])


register, unregister = bpy.utils.register_classes_factory([SvInstancerNodeMK3])
