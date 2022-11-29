# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE
from itertools import cycle
from typing import Optional

import bpy
from sverchok.data_structure import fixed_iter

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.handle_blender_data import BlModifier, BlSocket, correct_collection_length
from sverchok.utils.nodes_mixins.generating_objects import SvViewerLightNode, SvMeshData, SearchNode


class SvUpdateNodeInterface(SearchNode, bpy.types.Operator):
    """Refresh the node sockets"""
    bl_idname = 'node.sv_update_node_interface'
    bl_label = 'Update node sockets'

    def execute(self, context):
        self.node.generate_sockets(context)
        return {'FINISHED'}


class SvGeoNodesViewerNode(
        SvViewerLightNode, SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: modifiers
    Tooltip:
    """
    bl_idname = 'SvGeoNodesViewerNode'
    bl_label = 'Geo Nodes Viewer'
    bl_icon = 'GEOMETRY_NODES' if bpy.app.version >= (3, 3) else 'NODETREE'

    def generate_sockets(self, context):
        # remove all extra sockets
        if not self.modifier:
            for sv_s in list(self.inputs)[:2:-1]:
                self.inputs.remove(sv_s)
            self.process_node(context)
            return

        # remove sockets which are not presented in the modifier
        for i in range(len(self.inputs)-1, len(self.modifier.inputs)+1, -1):
            self.inputs.remove(self.inputs[i])

        # fix existing sockets
        for gn_s, sv_s in zip(self.modifier.inputs[1:], self.inputs[3:]):
            gn_s = BlSocket(gn_s)
            if sv_s.bl_idname != (s_type := gn_s.sverchok_type):
                sv_s = sv_s.replace_socket(s_type)
            gn_s.copy_properties(sv_s)
            if hasattr(sv_s, 'show_domain'):
                sv_s.show_domain = True

        # add new sockets
        for gn_s in self.modifier.inputs[len(self.inputs)-2:]:
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

    mesh_data: bpy.props.CollectionProperty(type=SvMeshData, options={'SKIP_SAVE'})
    fast_mesh_update: bpy.props.BoolProperty(
        default=True,
        update=lambda s, c: s.process_node(c),
        description="Usually should be enabled. If some glitches with"
                    " mesh update, switch it off")

    def sv_draw_buttons(self, context, layout):
        self.draw_viewer_properties(layout)
        row = layout.row(align=True)
        row.prop(self, 'modifier', text='')
        row.operator(SvUpdateNodeInterface.bl_idname, text='', icon='FILE_REFRESH')

    def draw_buttons_fly(self, layout):
        super().draw_buttons_fly(layout)
        row = layout.row(align=True)
        row.prop(self, 'modifier', text='')
        op = row.operator(SvUpdateNodeInterface.bl_idname, text='', icon='FILE_REFRESH')
        op.node_name = self.name
        op.tree_name = self.id_data.name

        col = layout.column()
        col.prop(self, 'fast_mesh_update')

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Vertices')
        self.inputs.new('SvStringsSocket', 'Edges')
        self.inputs.new('SvStringsSocket', 'Faces')
        self.init_viewer()

    def sv_copy(self, other):
        super().sv_copy(other)
        self.mesh_data.clear()

    def process(self):
        if not self.is_active:
            return

        verts = self.inputs['Vertices'].sv_get(deepcopy=False, default=[])
        edges = self.inputs['Edges'].sv_get(deepcopy=False, default=[[]])
        faces = self.inputs['Faces'].sv_get(deepcopy=False, default=[[]])

        obj_num = len(verts)

        # regenerate mesh data blocks
        correct_collection_length(self.mesh_data, obj_num)
        create_mesh_data = zip(self.mesh_data, cycle(verts), cycle(edges), cycle(faces))
        for me_data, v, e, f in create_mesh_data:
            me_data.regenerate_mesh(self.base_data_name, v, e, f, make_changes_test=self.fast_mesh_update)

        # regenerate object data blocks
        self.regenerate_objects([self.base_data_name], [d.mesh for d in self.mesh_data])
        objs = [obj_data.obj for obj_data in self.object_data]
        self.outputs[0].sv_set(objs)

        props = [s.sv_get(deepcopy=False, default=[]) for s in self.inputs[3:]]
        props = [fixed_iter(sock_data, obj_num, None) for sock_data in props]
        props = zip(*props) if props else fixed_iter([], obj_num, [])

        if self.modifier is None:
            for obj in objs:
                mod = self.get_modifier(obj, create=False)
                if mod is not None:
                    mod.remove()
        else:
            for obj, prop in zip(objs, props):
                mod = self.get_modifier(obj)
                for sv_s, gn_s, s_data in zip(self.inputs[3:], self.modifier.inputs[1:], prop):
                    domain = sv_s.domain if hasattr(sv_s, 'domain') else 'POINT'
                    mod.set_tree_data(gn_s.identifier, s_data, domain)
                obj.data.update()

    def get_modifier(self, obj, create=True) -> Optional[BlModifier]:
        """Whenever geometry tree updates its interface, the modifier clears
        its all Custom properties, so they can't be used to keep node_id"""
        for mod in obj.modifiers:
            if mod.name == "SvGeoNodesViewer":
                break
        else:
            if create:
                mod = obj.modifiers.new("SvGeoNodesViewer", 'NODES')
                mod.node_group = self.modifier
            else:
                mod = None
        return mod and BlModifier(mod)


register, unregister = bpy.utils.register_classes_factory(
    [SvGeoNodesViewerNode, SvUpdateNodeInterface])
