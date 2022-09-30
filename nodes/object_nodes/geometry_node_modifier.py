# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from typing import Optional

import bpy
from sverchok.data_structure import fixed_iter

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.handle_blender_data import BlModifier, BlSocket


class SvUpdateNodeInterface(bpy.types.Operator):
    """Refresh the node sockets"""
    bl_idname = 'node.sv_update_node_interface'
    bl_label = 'Update node sockets'

    def execute(self, context):
        context.node.generate_sockets(context)
        return {'FINISHED'}


class SvGeometryNodeModifierNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: modifiers
    Tooltip:
    """
    bl_idname = 'SvGeometryNodeModifierNode'
    bl_label = 'Geometry Nodes Modifier'
    bl_icon = 'MODIFIER_DATA'

    # @property
    # def is_scene_dependent(self):
    #     return self.inputs['Object To'].is_linked \
    #            or self.inputs['Object To'].object_ref_pointer
    #
    # @property
    # def is_animation_dependent(self):
    #     return self.inputs['Object To'].is_linked \
    #            or self.inputs['Object To'].object_ref_pointer

    def generate_sockets(self, context):
        if not self.modifier:
            for sv_s in list(self.inputs)[:0:-1]:
                self.inputs.remove(sv_s)
            self.process_node(context)
            return
        for i in range(len(self.inputs)-1, len(self.modifier.inputs)-1, -1):
            self.inputs.remove(self.inputs[i])
        for gn_s, sv_s in zip(self.modifier.inputs[1:], self.inputs[1:]):
            gn_s = BlSocket(gn_s)
            if sv_s.bl_idname != (s_type := gn_s.sverchok_type):
                sv_s = sv_s.replace_socket(s_type)
            gn_s.copy_properties(sv_s)
            if hasattr(sv_s, 'show_domain'):
                sv_s.show_domain = True
        for gn_s in self.modifier.inputs[len(self.inputs):]:
            gn_s = BlSocket(gn_s)
            sv_s = self.inputs.new(gn_s.sverchok_type, '')
            gn_s.copy_properties(sv_s)
            if hasattr(sv_s, 'show_domain'):
                sv_s.show_domain = True
        self.process_node(context)

    modifier: bpy.props.PointerProperty(
        type=bpy.types.NodeTree,
        poll=lambda s, t: t.type == 'GEOMETRY',  # https://developer.blender.org/T97879
        update=generate_sockets,
        description="Geometry nodes modifier",
    )

    def sv_draw_buttons(self, context, layout):
        row = layout.row(align=True)
        row.prop(self, 'modifier', text='')
        row.operator(SvUpdateNodeInterface.bl_idname, text='', icon='FILE_REFRESH')

    def sv_init(self, context):
        self.inputs.new('SvObjectSocket', 'Object')
        self.outputs.new('SvObjectSocket', 'Object')

    def process(self):
        objs = self.inputs['Object'].sv_get(deepcopy=False, default=[])
        props = [s.sv_get(deepcopy=False, default=[]) for s in self.inputs[1:]]
        props = [fixed_iter(sock_data, len(objs), None) for sock_data in props]
        props = zip(*props) if props else fixed_iter([], len(objs), [])
        self.outputs[0].sv_set(objs)

        if self.modifier is None:
            for obj in objs:
                mod = self.get_modifier(obj, create=False)
                if mod is not None:
                    mod.remove()
        else:
            for obj, prop in zip(objs, props):
                if obj.type != 'MESH':
                    raise TypeError(f'Only mesh objects are supported, {obj.type} is given')
                mod = self.get_modifier(obj)
                for sv_s, gn_s, s_data in zip(self.inputs[1:], self.modifier.inputs[1:], prop):
                    domain = sv_s.domain if hasattr(sv_s, 'domain') else 'POINT'
                    mod.set_tree_data(gn_s.identifier, s_data, domain)
                if hasattr(obj.data, 'update'):
                    obj.data.update()

    def get_modifier(self, obj, create=True) -> Optional[BlModifier]:
        """Each node should work with its own modifier
        Whenever geometry tree updates its interface, the modifier clears
        its all Custom properties, so they can't be used to keep node_id"""
        for mod in obj.modifiers:
            if mod.name == self.node_id:
                break
        else:
            if create:
                mod = obj.modifiers.new(self.node_id, 'NODES')
                mod.node_group = self.modifier
            else:
                mod = None
        return mod and BlModifier(mod)


register, unregister = bpy.utils.register_classes_factory(
    [SvGeometryNodeModifierNode, SvUpdateNodeInterface])
