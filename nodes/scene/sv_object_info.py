# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.nodes_mixins.sv_animatable_nodes import SvAnimatableNode


class SvObjectInfoNode(bpy.types.Node, SverchCustomTreeNode, SvAnimatableNode):
    '''SvObjectInfoNode'''
    bl_idname = 'SvObjectInfoNode'
    bl_label = 'Object Info'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_OBJECT_ID_OUT'

    def sv_init(self, context):
        self.inputs.new('SvObjectSocket', "Object")
        self.outputs.new('SvVerticesSocket', "Location")
        self.outputs.new('SvVerticesSocket', "Rotation")
        self.outputs.new('SvVerticesSocket', "Scale")
        self.outputs.new('SvObjectSocket', "Object")

    def draw_buttons(self, context, layout):
        self.draw_animatable_buttons(layout, icon_only=True)

    def process(self):

        objs = self.inputs[0].sv_get()
        if isinstance(objs[0], list):
            objs = objs[0]

        if not objs[0].type in ['MESH', 'CURVE', 'FONT', 'SURFACE', 'META']:
            return 
        
        data_out = [[], [], [], []]

        get_location = lambda obj: [obj.location[:]]
        get_rotation = lambda obj: [obj.rotation_euler[:3]]
        get_scale = lambda obj: [obj.scale[:]]
        get_object = lambda obj: obj

        functors = [get_location, get_rotation, get_scale, get_object]

        for obj in objs:
            for socket, data, functor in zip(self.outputs, data_out, functors):
                if socket.is_linked:
                    data.append(functor(obj))

        for socket, data in zip(self.outputs, data_out):
            if socket.is_linked:
                socket.sv_set(data)


register, unregister = bpy.utils.register_classes_factory([SvObjectInfoNode])