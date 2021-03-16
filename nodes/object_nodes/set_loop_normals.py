# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import bpy
from mathutils import Vector

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, repeat_last


class SvSetLoopNormalsNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: set loops normals

    Adding custom normals for input object
    Should be used together with Origins node
    """
    bl_idname = 'SvSetLoopNormalsNode'
    bl_label = 'Set loop normals'
    bl_icon = 'NORMALS_VERTEX'

    normalize: bpy.props.BoolProperty(name="Normalize", default=True, description="Normalize input normals",
                                      update=updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'normalize')

    def sv_init(self, context):
        self.inputs.new('SvObjectSocket', 'Object')
        self.outputs.new('SvObjectSocket', "Object")
        self.inputs.new('SvVerticesSocket', "Vert normals")
        self.inputs.new('SvStringsSocket', "Faces")

    def process(self):
        objects = self.inputs['Object'].sv_get(deepcopy=False, default=[])

        v_normals = self.inputs['Vert normals'].sv_get(deepcopy=False, default=[])
        faces = self.inputs['Faces'].sv_get(deepcopy=False, default=[])

        for obj, v_ns, fs in zip(objects, repeat_last(v_normals), repeat_last(faces)):
            obj.data.use_auto_smooth = True

            n_per_loop = [(0, 0, 0) for _ in range(len(obj.data.loops))]
            for me_p, f in zip(obj.data.polygons, fs):
                for l_i, f_i in zip(range(me_p.loop_start, me_p.loop_start + me_p.loop_total), repeat_last(f)):
                    try:
                        normal = v_ns[f_i]
                    except IndexError:
                        normal = v_ns[-1]
                    n_per_loop[l_i] = Vector(normal).normalized() if self.normalize else normal
            obj.data.normals_split_custom_set(n_per_loop)

        self.outputs['Object'].sv_set(objects)


register, unregister = bpy.utils.register_classes_factory([SvSetLoopNormalsNode])
