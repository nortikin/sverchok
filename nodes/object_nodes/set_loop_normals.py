# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import bpy

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, repeat_last, fixed_iter


class SvSetLoopNormalsNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: # todo


    """
    bl_idname = 'SvSetLoopNormalsNode'
    bl_label = 'Set loop normals'
    bl_icon = 'NORMALS_VERTEX'

    mode: bpy.props.EnumProperty(items=[(i, i, '') for i in ['vertex', 'face']], update=updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'mode', expand=True)

    def sv_init(self, context):
        self.inputs.new('SvObjectSocket', 'Object')
        self.inputs.new('SvVerticesSocket', 'Normals')
        self.outputs.new('SvObjectSocket', "Object")

    def process(self):
        if not self.inputs['Object'].is_linked:
            return

        objects = self.inputs['Object'].sv_get(deepcopy=False)
        normals = self.inputs['Normals'].sv_get(deepcopy=False, default=[])

        for obj, norms in zip(objects, repeat_last(normals)):

            if self.mode == 'face':
                n_per_loop = [(0, 0, 0) for _ in range(len(obj.data.loops))]
                for p, n in zip(obj.data.polygons, repeat_last(norms)):
                    for i in range(p.loop_start, p.loop_start + p.loop_total):
                        n_per_loop[i] = n
                obj.data.normals_split_custom_set(n_per_loop)
            else:
                obj.data.normals_split_custom_set_from_vertices(list(fixed_iter(norms, len(obj.data.vertices))))

            obj.data.update()

        self.outputs['Object'].sv_set(objects)


register, unregister = bpy.utils.register_classes_factory([SvSetLoopNormalsNode])
